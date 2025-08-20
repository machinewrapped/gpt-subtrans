from os import linesep
import logging
import threading
from typing import Any

from tenacity import retry

from PySubtitle.Helpers.Subtitles import MergeTranslations
from PySubtitle.Helpers.Localization import _, tr
from PySubtitle.Helpers.Text import Linearise, SanitiseSummary
from PySubtitle.Instructions import DEFAULT_TASK_TYPE, Instructions
from PySubtitle.Substitutions import Substitutions
from PySubtitle.SubtitleBatcher import SubtitleBatcher
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleProcessor import SubtitleProcessor
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.Options import Options
from PySubtitle.SubtitleBatch import SubtitleBatch

from PySubtitle.SubtitleError import NoProviderError, NoTranslationError, ProviderError, SubtitleError, TranslationAbortedError, TranslationError, TranslationImpossibleError
from PySubtitle.Helpers import FormatErrorMessages
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene, UnbatchScenes
from PySubtitle.TranslationEvents import TranslationEvents
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.TranslationProvider import TranslationProvider

class SubtitleTranslator:
    """
    Processes subtitles into scenes and batches and sends them for translation
    """
    def __init__(self, options: Options, translation_provider: TranslationProvider):
        """
        Initialise a SubtitleTranslator with translation options
        """
        self.events = TranslationEvents()
        self.lock = threading.Lock()
        self.aborted = False
        self.errors = []

        self.lines_processed = 0
        self.max_lines = options.get('max_lines')
        self.max_history = options.get('max_context_summaries')
        self.stop_on_error = options.get('stop_on_error')
        self.retry_on_error = options.get('retry_on_error')
        # self.split_on_error = options.get('autosplit_incomplete')
        self.max_summary_length = options.get('max_summary_length')
        self.resume = options.get('resume')
        self.retranslate = options.get('retranslate')
        self.reparse = options.get('reparse')
        self.preview = options.get('preview')

        self.instructions : Instructions = options.GetInstructions()
        self.task_type = self.instructions.task_type or DEFAULT_TASK_TYPE
        self.user_prompt : str = options.BuildUserPrompt()
        self.substitutions = Substitutions(options.get('substitutions', {}), options.get('substitution_mode', 'Auto'))

        self.settings = options.GetSettings()
        self.settings['instructions'] = self.instructions.instructions
        self.settings['retry_instructions'] = self.instructions.retry_instructions

        logging.debug(f"Translation prompt: {self.user_prompt}")

        self.translation_provider : TranslationProvider = translation_provider

        if not self.translation_provider:
            raise NoProviderError()

        try:
            self.client : TranslationClient = self.translation_provider.GetTranslationClient(self.settings)

        except Exception as e:
            raise ProviderError(_("Unable to create provider client: {error}").format(error=str(e)), translation_provider)

        if not self.client:
            raise ProviderError(_("Unable to create translation client"), translation_provider)

        self.batcher = SubtitleBatcher(options)

        self.postprocessor = SubtitleProcessor(options) if options.get('postprocess_translation') else None

    def StopTranslating(self):
        self.aborted = True
        self.client.AbortTranslation()

    def TranslateSubtitles(self, subtitles : SubtitleFile):
        """
        Translate a SubtitleFile
        """
        if not subtitles:
            raise TranslationImpossibleError(_("No subtitles to translate"))

        if subtitles.scenes and self.resume:
            logging.info(_("Resuming translation"))

        if not subtitles.scenes:
            if self.retranslate or self.resume:
                logging.warning(_("Previous subtitles not found, starting fresh..."))

            subtitles.AutoBatch(self.batcher)

        if not subtitles.scenes:
            raise TranslationImpossibleError(_("No scenes to translate"))

        logging.info(_("Translating {linecount} lines in {scenecount} scenes").format(linecount=subtitles.linecount, scenecount=subtitles.scenecount))

        self.events.preprocessed(subtitles.scenes)

        # Iterate over each subtitle scene and request translation
        for scene in subtitles.scenes:
            if self.aborted:
                break

            if self.max_lines and self.lines_processed >= self.max_lines:
                break

            if self.resume and scene.all_translated:
                logging.info(_("Scene {scene} already translated {linecount} lines...").format(scene=scene.number, linecount=scene.linecount))
                continue

            logging.debug(f"Translating scene {scene.number} of {subtitles.scenecount}")
            batch_numbers = [ batch.number for batch in scene.batches if not batch.translated ] if self.resume else None

            self.TranslateScene(subtitles, scene, batch_numbers=batch_numbers)

            if self.errors and self.stop_on_error:
                logging.error(_("Failed to translate scene {scene}... stopping translation").format(scene=scene.number))
                return

        if self.aborted:
            logging.info(_("Translation aborted"))
            return

        # Linearise the translated scenes
        originals, translations, untranslated = UnbatchScenes(subtitles.scenes)

        if translations:
            logging.info(_("Successfully translated {count} lines!").format(count=len(translations)))

        if untranslated and not self.max_lines:
            logging.warning(_("Failed to translate {count} lines:").format(count=len(untranslated)))
            for line in untranslated:
                logging.info(_("Untranslated > {number}. {text}").format(number=line.number, text=line.text))

        subtitles.originals = originals
        subtitles.translated = translations

    def TranslateScene(self, subtitles : SubtitleFile, scene : SubtitleScene, batch_numbers = None, line_numbers = None):
        """
        Send a scene for translation
        """
        try:
            batches = [ batch for batch in scene.batches if batch.number in batch_numbers ] if batch_numbers else scene.batches
            context = {}

            for batch in batches:
                context = subtitles.GetBatchContext(scene.number, batch.number, self.max_history)

                try:
                    self.TranslateBatch(batch, line_numbers, context)

                except TranslationImpossibleError as e:
                    raise

                except TranslationError as e:
                    logging.warning(_("Error translating scene {scene} batch {batch}: {error}").format(scene=batch.scene, batch=batch.number, error=str(e)))
                    batch.errors.append(e)

                if self.aborted:
                    return

                # Notify observers the batch was translated
                self.events.batch_translated(batch)

                if batch.errors:
                    logging.warning(_("Errors encountered translating scene {scene} batch {batch}").format(scene=batch.scene, batch=batch.number))
                    scene.errors.extend(batch.errors)
                    self.errors.extend(batch.errors)
                    if self.stop_on_error:
                        return

                if self.max_lines and self.lines_processed >= self.max_lines:
                    logging.info(_("Reached max_lines limit of ({lines} lines)... finishing").format(lines=self.max_lines))
                    break

            # Update the scene summary based on the best available information (we hope)
            scene.summary = self._get_best_summary([scene.summary, context.get('scene'), context.get('summary')])

            # Notify observers the scene was translated
            self.events.scene_translated(scene)

        except (TranslationAbortedError, TranslationImpossibleError) as e:
            raise

    def TranslateBatch(self, batch : SubtitleBatch, line_numbers : list[int]|None, context : dict[str,Any]|None):
        """
        Send batches of subtitles for translation, building up context.
        """
        if self.aborted:
            return

        if self.resume and batch.all_translated:
            logging.info(_("Scene {scene} batch {batch} already translated {lines} lines...").format(scene=batch.scene, batch=batch.number, lines=batch.size))
            return

        if self.reparse and batch.translation:
            logging.info(_("Reparsing scene {scene} batch {batch} with {count} lines...").format(scene=batch.scene, batch=batch.number, count=len(batch.originals)))
            self.ProcessBatchTranslation(batch, batch.translation, line_numbers)
            return

        originals, context = self.PreprocessBatch(batch, context)

        logging.debug(f"Translating scene {batch.scene} batch {batch.number} with {len(originals)} lines...")

        # Build summaries context
        context['batch'] = f"Scene {batch.scene} batch {batch.number}"
        if batch.summary:
            context['summary'] = batch.summary

        instructions = self.instructions.instructions
        if not instructions:
            raise TranslationImpossibleError(_("No instructions provided for translation"))

        batch.prompt = self.client.BuildTranslationPrompt(self.user_prompt, instructions, originals, context)

        if self.preview:
            return

        # Ask the client to do the translation
        translation : Translation|None = self.client.RequestTranslation(batch.prompt)

        if (translation and translation.reached_token_limit) and not self.aborted:
            # Try again without the context to keep the tokens down
            # TODO: better to split the batch into smaller chunks
            logging.warning(_("Hit API token limit, retrying batch without context..."))
            batch.prompt.GenerateMessages(instructions, batch.originals, {})

            translation = self.client.RequestTranslation(batch.prompt)

        if not self.aborted:
            if not translation:
                raise TranslationError(f"Unable to translate scene {batch.scene} batch {batch.number}")

            # Process the response
            self.ProcessBatchTranslation(batch, translation, line_numbers)

            # Consider retrying if there were errors
            if batch.errors and self.retry_on_error:
                logging.warning(_("Scene {scene} batch {batch} failed validation, requesting retranslation").format(scene=batch.scene, batch=batch.number))
                self.RequestRetranslation(batch, line_numbers=line_numbers, context=context)

            # Update the context, unless it's a retranslation pass
            if not self.retranslate and not self.aborted:
                context['summary'] = self._get_best_summary([translation.summary, batch.summary])
                context['scene'] = self._get_best_summary([translation.scene, context.get('scene')])
                context['synopsis'] = translation.synopsis or context.get('synopsis', "")
                #context['names'] = translation.names or context.get('names', []) or options.get('names')
                batch.UpdateContext(context)

    def PreprocessBatch(self, batch : SubtitleBatch, context : dict[str,Any]|None = None) -> tuple[list[SubtitleLine], dict[str, Any]]:
        """
        Preprocess the batch before translation
        """
        context = context or {}
        if batch.context and (self.retranslate or self.reparse):
            # If it's a retranslation, restore context from the batch
            for key, value in batch.context.items():
                context[key] = value

        # Apply any substitutions to the input
        replacements = batch.PerformInputSubstitutions(self.substitutions)

        if replacements:
            replaced : list[str] = [f"{Linearise(k)} -> {Linearise(v)}" for k,v in replacements.items()]
            logging.info(_("Made substitutions in input:\n{replaced}").format(replaced=linesep.join(replaced)))
            batch.AddContext('replacements', replaced)

        # Filter out empty lines
        originals = [ line for line in batch.originals if line.text and line.text.strip() ]

        # Apply the max_lines limit
        with self.lock:
            line_count = min(self.max_lines - self.lines_processed, len(originals)) if self.max_lines else len(originals)
            self.lines_processed += line_count
            if len(originals) > line_count:
                logging.info(_("Truncating batch to remain within max_lines"))
                originals = originals[:line_count] if line_count > 0 else []

        return originals, context

    def ProcessBatchTranslation(self, batch : SubtitleBatch, translation : Translation, line_numbers : list[int]|None):
        """
        Attempt to extract translation from the API response
        """
        if not translation:
            raise NoTranslationError("No translation provided")

        if not translation.has_translation:
            raise TranslationError("Translation contains no translated text", translation=translation)

        logging.debug(f"Scene {batch.scene} batch {batch.number} translation:\n{translation.text}\n")

        # Apply the translation to the subtitles
        parser : TranslationParser = self.client.GetParser(self.task_type)

        parser.ProcessTranslation(translation)

        # Try to match the translations with the original lines
        translated, unmatched = parser.MatchTranslations(batch.originals)

        # Assign the translated lines to the batch
        if line_numbers:
            translated = [line for line in translated if line.number in line_numbers]

        batch._translated = MergeTranslations(batch.translated or [], translated)

        batch.translation = translation
        batch.errors = [err for err in parser.errors if isinstance(err, str) or isinstance(err, SubtitleError)]

        if batch.untranslated and not self.max_lines:
            logging.warning(_("Unable to match {count} lines with a source line").format(count=len(unmatched)))
            batch.AddContext('untranslated_lines', [f"{item.number}. {item.text}" for item in batch.untranslated])

        # Apply any word/phrase substitutions to the translation
        replacements = batch.PerformOutputSubstitutions(self.substitutions)

        if replacements:
            replaced = [f"{k} -> {v}" for k,v in replacements.items()]
            logging.info(_("Made substitutions in output:\n{replaced}").format(replaced=linesep.join(replaced)))

        # Perform substitutions on the output
        translation.PerformSubstitutions(self.substitutions)

        # Post-process the translation
        if self.postprocessor:
            batch._translated = self.postprocessor.PostprocessSubtitles(batch.translated)

            logging.info(_("Scene {scene} batch {batch}: {translated} lines and {untranslated} untranslated.").format(
                scene=batch.scene, 
                batch=batch.number, 
                translated=len(batch.translated or []), 
                untranslated=len(batch.untranslated or []))
                )

        if translation.summary and translation.summary.strip():
            logging.info(_("Summary: {summary}").format(summary=translation.summary))

    def RequestRetranslation(self, batch : SubtitleBatch, line_numbers : list[int]|None = None, context : dict[str, str]|None = None):
        """
        Ask the client to retranslate the input and correct errors
        """
        translation : Translation|None = batch.translation
        if not translation:
            raise TranslationError("No translation to retranslate")

        prompt : TranslationPrompt|None = batch.prompt
        if not prompt or not prompt.messages:
            raise TranslationError("No prompt to retranslate")

        if not self.instructions.retry_instructions:
            raise TranslationError("No retry instructions provided")

        if not translation.text:
            raise TranslationError("No translation text to retranslate", translation=translation)

        retry_instructions = self.instructions.retry_instructions
        if retry_instructions is None:
            return

        prompt.GenerateRetryPrompt(translation.text, retry_instructions, batch.errors)

        # Let's raise the temperature a little bit
        temperature = self.client.temperature or 0.0
        retry_temperature = min(temperature + 0.1, 1.0)

        retranslation : Translation|None = self.client.RequestTranslation(prompt, retry_temperature)

        if self.aborted:
            return None

        if not isinstance(retranslation, Translation):
            raise TranslationError("Retranslation is not the expected type", translation=retranslation)

        logging.debug(f"Scene {batch.scene} batch {batch.number} retranslation:\n{retranslation.text}\n")

        self.ProcessBatchTranslation(batch, retranslation, line_numbers)

        if batch.errors:
            logging.warning(_("Retry failed validation: {errors}").format(errors=FormatErrorMessages(batch.errors)))
        else:
            logging.info(_("Retry passed validation"))

    def _get_best_summary(self, candidates : list[str|None]) -> str|None:
        """
        Generate a summary of the translated subtitles
        """
        movie_name = self.settings.get('movie_name', None)
        movie_name = str(movie_name).strip() if movie_name else None
        max_length = self.max_summary_length
        for candidate in candidates:
            if candidate is None:
                continue

            sanitised = SanitiseSummary(candidate, movie_name, max_length)
            if sanitised:
                if len(sanitised) < len(candidate):
                    logging.info(_("Summary was truncated from {original} to {truncated} characters").format(original=len(candidate), truncated=len(sanitised)))
                return sanitised

        return None