from os import linesep
import logging
import threading

from PySubtitle.Helpers.Subtitles import MergeTranslations
from PySubtitle.Helpers.Text import Linearise, SanitiseSummary
from PySubtitle.Instructions import DEFAULT_TASK_TYPE, Instructions
from PySubtitle.Substitutions import Substitutions
from PySubtitle.SubtitleBatcher import SubtitleBatcher
from PySubtitle.SubtitleProcessor import SubtitleProcessor
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.Options import Options
from PySubtitle.SubtitleBatch import SubtitleBatch

from PySubtitle.SubtitleError import NoProviderError, NoTranslationError, ProviderError, TranslationAbortedError, TranslationError, TranslationImpossibleError
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
            raise NoProviderError("Translation provider is unavailable")

        try:
            self.client : TranslationClient = self.translation_provider.GetTranslationClient(self.settings)

        except Exception as e:
            raise ProviderError(f"Unable to create provider client: {str(e)}")

        if not self.client:
            raise ProviderError("Unable to create translation client")

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
            raise TranslationImpossibleError("No subtitles to translate")

        if subtitles.scenes and self.resume:
            logging.info("Resuming translation")

        if not subtitles.scenes:
            if self.retranslate or self.resume:
                logging.warning(f"Previous subtitles not found, starting fresh...")

            subtitles.AutoBatch(self.batcher)

        if not subtitles.scenes:
            raise TranslationImpossibleError("No scenes to translate")

        logging.info(f"Translating {subtitles.linecount} lines in {subtitles.scenecount} scenes")

        self.events.preprocessed(subtitles.scenes)

        # Iterate over each subtitle scene and request translation
        for scene in subtitles.scenes:
            if self.aborted:
                break

            if self.max_lines and self.lines_processed >= self.max_lines:
                break

            if self.resume and scene.all_translated:
                logging.info(f"Scene {scene.number} already translated {scene.linecount} lines...")
                continue

            logging.debug(f"Translating scene {scene.number} of {subtitles.scenecount}")
            batch_numbers = [ batch.number for batch in scene.batches if not batch.translated ] if self.resume else None

            self.TranslateScene(subtitles, scene, batch_numbers=batch_numbers)

            if self.errors and self.stop_on_error:
                logging.error(f"Failed to translate scene {scene.number}... stopping translation")
                return

        if self.aborted:
            logging.info("Translation aborted")
            return

        # Linearise the translated scenes
        originals, translations, untranslated = UnbatchScenes(subtitles.scenes)

        if translations:
            logging.info(f"Successfully translated {len(translations)} lines!")

        if untranslated and not self.max_lines:
            logging.warning(f"Failed to translate {len(untranslated)} lines:")
            for line in untranslated:
                logging.info(f"Untranslated > {line.number}. {line.text}")

        subtitles.originals = originals
        subtitles.translated = translations

    def TranslateScene(self, subtitles : SubtitleFile, scene : SubtitleScene, batch_numbers = None, line_numbers = None):
        """
        Send a scene for translation
        """
        try:
            batches = [ batch for batch in scene.batches if batch.number in batch_numbers ] if batch_numbers else scene.batches

            for batch in batches:
                context = subtitles.GetBatchContext(scene.number, batch.number, self.max_history)

                try:
                    self.TranslateBatch(batch, line_numbers, context)

                except TranslationImpossibleError as e:
                    raise

                except TranslationError as e:
                    logging.warning(f"Error translating scene {batch.scene} batch {batch.number}: {str(e)}")
                    batch.errors.append(e)

                if self.aborted:
                    return

                # Notify observers the batch was translated
                self.events.batch_translated(batch)

                if batch.errors:
                    logging.warning(f"Errors encountered translating scene {batch.scene} batch {batch.number}")
                    scene.errors.extend(batch.errors)
                    self.errors.extend(batch.errors)
                    if self.stop_on_error:
                        return

                if self.max_lines and self.lines_processed >= self.max_lines:
                    logging.info(f"Reached max_lines limit of ({self.max_lines} lines)... finishing")
                    break

            # Update the scene summary based on the best available information (we hope)
            scene.summary = self._get_best_summary([scene.summary, context.get('scene'), context.get('summary')])

            # Notify observers the scene was translated
            self.events.scene_translated(scene)

        except (TranslationAbortedError, TranslationImpossibleError) as e:
            raise

    def TranslateBatch(self, batch : SubtitleBatch, line_numbers : list[int], context : dict):
        """
        Send batches of subtitles for translation, building up context.
        """
        if self.aborted:
            return

        if self.resume and batch.all_translated:
            logging.info(f"Scene {batch.scene} batch {batch.number} already translated {batch.size} lines...")
            return

        if self.reparse and batch.translation:
            logging.info(f"Reparsing scene {batch.scene} batch {batch.number} with {len(batch.originals)} lines...")
            self.ProcessBatchTranslation(batch, batch.translation, line_numbers)
            return

        originals, context = self.PreprocessBatch(batch, context)

        logging.debug(f"Translating scene {batch.scene} batch {batch.number} with {len(originals)} lines...")

        # Build summaries context
        context['batch'] = f"Scene {batch.scene} batch {batch.number}"
        if batch.summary:
            context['summary'] = batch.summary

        instructions = self.instructions.instructions
        batch.prompt = self.client.BuildTranslationPrompt(self.user_prompt, instructions, originals, context)

        if self.preview:
            return

        # Ask the client to do the translation
        translation : Translation = self.client.RequestTranslation(batch.prompt)

        if (translation and translation.reached_token_limit) and not self.aborted:
            # Try again without the context to keep the tokens down
            # TODO: better to split the batch into smaller chunks
            logging.warning("Hit API token limit, retrying batch without context...")
            batch.prompt.GenerateMessages(self.instructions.instructions, batch.originals, {})

            translation = self.client.RequestTranslation(batch.prompt)

        if not self.aborted:
            if not translation:
                raise TranslationError(f"Unable to translate scene {batch.scene} batch {batch.number}")

            # Process the response
            self.ProcessBatchTranslation(batch, translation, line_numbers)

            # Consider retrying if there were errors
            if batch.errors and self.retry_on_error:
                logging.warning(f"Scene {batch.scene} batch {batch.number} failed validation, requesting retranslation")
                self.RequestRetranslation(batch, line_numbers=line_numbers, context=context)

            # Update the context, unless it's a retranslation pass
            if not self.retranslate and not self.aborted:
                context['summary'] = self._get_best_summary([translation.summary, batch.summary])
                context['scene'] = self._get_best_summary([translation.scene, context.get('scene')])
                context['synopsis'] = translation.synopsis or context.get('synopsis', "")
                #context['names'] = translation.names or context.get('names', []) or options.get('names')
                batch.UpdateContext(context)

    def PreprocessBatch(self, batch : SubtitleBatch, context : dict):
        """
        Preprocess the batch before translation
        """
        if batch.context and (self.retranslate or self.reparse):
            # If it's a retranslation, restore context from the batch
            for key, value in batch.context.items():
                context[key] = value

        # Apply any substitutions to the input
        replacements = batch.PerformInputSubstitutions(self.substitutions)

        if replacements:
            replaced = [f"{Linearise(k)} -> {Linearise(v)}" for k,v in replacements.items()]
            logging.info(f"Made substitutions in input:\n{linesep.join(replaced)}")
            batch.AddContext('replacements', replaced)

        # Filter out empty lines
        originals = [ line for line in batch.originals if line.text and line.text.strip() ]

        # Apply the max_lines limit
        with self.lock:
            line_count = min(self.max_lines - self.lines_processed, len(originals)) if self.max_lines else len(originals)
            self.lines_processed += line_count
            if len(originals) > line_count:
                logging.info("Truncating batch to remain within max_lines")
                originals = originals[:line_count] if line_count > 0 else []

        return originals, context

    def ProcessBatchTranslation(self, batch : SubtitleBatch, translation : Translation, line_numbers : list[int]):
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

        batch.translated = MergeTranslations(batch.translated or [], translated)

        batch.translation = translation
        batch.errors = parser.errors

        if batch.untranslated and not self.max_lines:
            logging.warning(f"Unable to match {len(unmatched)} lines with a source line")
            batch.AddContext('untranslated_lines', [f"{item.number}. {item.text}" for item in batch.untranslated])

        # Apply any word/phrase substitutions to the translation
        replacements = batch.PerformOutputSubstitutions(self.substitutions)

        if replacements:
            replaced = [f"{k} -> {v}" for k,v in replacements.items()]
            logging.info(f"Made substitutions in output:\n{linesep.join(replaced)}")

        # Perform substitutions on the output
        translation.PerformSubstitutions(self.substitutions)

        # Post-process the translation
        if self.postprocessor:
            batch.translated = self.postprocessor.PostprocessSubtitles(batch.translated)

        logging.info(f"Scene {batch.scene} batch {batch.number}: {len(batch.translated or [])} lines and {len(batch.untranslated or [])} untranslated.")

        if translation.summary and translation.summary.strip():
            logging.info(f"Summary: {translation.summary}")

    def RequestRetranslation(self, batch : SubtitleBatch, line_numbers : list[int] = None, context : dict = {}):
        """
        Ask the client to retranslate the input and correct errors
        """
        translation : Translation = batch.translation
        if not translation:
            raise TranslationError("No translation to retranslate")

        prompt : TranslationPrompt = batch.prompt
        if not prompt or not prompt.messages:
            raise TranslationError("No prompt to retranslate")

        prompt.GenerateRetryPrompt(translation.text, self.instructions.retry_instructions, batch.errors)

        # Let's raise the temperature a little bit
        temperature = self.client.temperature or 0.0
        retry_temperature = min(temperature + 0.1, 1.0)

        retranslation : Translation = self.client.RequestTranslation(prompt, retry_temperature)

        if self.aborted:
            return None

        if not isinstance(retranslation, Translation):
            raise TranslationError("Retranslation is not the expected type", translation=retranslation)

        logging.debug(f"Scene {batch.scene} batch {batch.number} retranslation:\n{retranslation.text}\n")

        self.ProcessBatchTranslation(batch, retranslation, line_numbers)

        if batch.errors:
            logging.warning(f"Retry failed validation: {FormatErrorMessages(batch.errors)}")
        else:
            logging.info("Retry passed validation")

    def _get_best_summary(self, candidates : list[str]):
        """
        Generate a summary of the translated subtitles
        """
        movie_name = self.settings.get('movie_name')
        max_length = self.max_summary_length
        for candidate in candidates:
            sanitised = SanitiseSummary(candidate, movie_name, max_length)
            if sanitised:
                if len(sanitised) < len(candidate):
                    logging.info(f"Summary was truncated from {len(candidate)} to {len(sanitised)} characters")
                return sanitised

        return None