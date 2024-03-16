from copy import deepcopy
import logging
import re
from os import linesep
from PySubtitle.Instructions import Instructions
from PySubtitle.SubtitleBatcher import CreateSubtitleBatcher
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.Options import Options
from PySubtitle.SubtitleBatch import SubtitleBatch

from PySubtitle.SubtitleError import NoProviderError, ProviderError, TranslationAbortedError, TranslationError, TranslationFailedError, TranslationImpossibleError, UntranslatedLinesError
from PySubtitle.Helpers import BuildUserPrompt, Linearise, MergeTranslations, ParseSubstitutions, RemoveEmptyLines, LimitTextLength, UnbatchScenes
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene
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
        self.aborted = False

        self.max_lines = options.get('max_lines')
        self.max_context_summaries = options.get('max_context_summaries')
        self.stop_on_error = options.get('stop_on_error')
        self.allow_retranslations = options.get('allow_retranslations')
        self.whitespaces_to_newline = options.get('whitespaces_to_newline')
        self.match_partial_words = options.get('match_partial_words')
        self.max_summary_length = options.get('max_summary_length')
        self.resume = options.get('resume')
        self.retranslate = options.get('retranslate')
        self.reparse = options.get('reparse')
        self.preview = options.get('preview')

        self.settings = options.GetSettings()
        self.instructions : Instructions = options.GetInstructions()
        self.user_prompt : str = BuildUserPrompt(options)
        self.substitutions = ParseSubstitutions(options.get('substitutions', {}))
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
        
        self.batcher = CreateSubtitleBatcher(options)

    def StopTranslating(self):
        self.aborted = True
        self.client.AbortTranslation()

    def TranslateSubtitles(self, subtitles : SubtitleFile):
        """
        Translate a SubtitleFile
        """
        if self.aborted:
            raise TranslationAbortedError()

        if not subtitles:
            raise TranslationError("No subtitles to translate")
    
        if subtitles.scenes and self.resume:
            logging.info("Resuming translation")

        if not subtitles.scenes:
            if self.retranslate or self.resume:
                logging.warning(f"Previous subtitles not found, starting fresh...")

            subtitles.AutoBatch(self.batcher)

        if not subtitles.scenes:
            raise Exception("No scenes to translate")
        
        logging.info(f"Translating {subtitles.linecount} lines in {subtitles.scenecount} scenes")

        self.events.preprocessed(subtitles.scenes)

        remaining_lines = self.max_lines

        # Iterate over each subtitle scene and request translation
        for scene in subtitles.scenes:
            if self.aborted:
                raise TranslationAbortedError()

            if self.resume and scene.all_translated:
                    logging.info(f"Scene {scene.number} already translated {scene.linecount} lines...")
                    continue

            logging.debug(f"Translating scene {scene.number} of {subtitles.scenecount}")
            batch_numbers = [ batch.number for batch in scene.batches if not batch.translated ] if self.resume else None

            self.TranslateScene(subtitles, scene, batch_numbers=batch_numbers, remaining_lines=remaining_lines)

            if remaining_lines:
                remaining_lines = max(0, remaining_lines - scene.linecount)
                if not remaining_lines:
                    logging.info(f"Reached max_lines limit of ({self.max_lines} lines)... finishing")
                    break

        # Linearise the translated scenes
        originals, translations, untranslated = UnbatchScenes(subtitles.scenes)

        if translations and not self.max_lines:
            logging.info(f"Successfully translated {len(translations)} lines!")

        if untranslated and not self.max_lines:
            logging.warning(f"Failed to translate {len(untranslated)} lines:")
            for line in untranslated:
                logging.info(f"Untranslated > {line.number}. {line.text}")

        subtitles.originals = originals
        subtitles.translated = translations

    def TranslateScene(self, subtitles : SubtitleFile, scene : SubtitleScene, batch_numbers = None, line_numbers = None, remaining_lines=None):
        """
        Send a scene for translation
        """
        try:
            context = deepcopy(scene.context)

            if batch_numbers:
                batches = [ batch for batch in scene.batches if batch.number in batch_numbers ]
                context['summaries'] = subtitles.GetBatchContext(scene.number, batch_numbers[-1], self.max_context_summaries)
            else:
                batches = scene.batches
                context['summaries'] = subtitles.GetBatchContext(scene.number, 1, self.max_context_summaries)

            context['scene'] = f"Scene {scene.number}: {scene.summary}" if scene.summary else f"Scene {scene.number}"

            self.TranslateBatches(batches, line_numbers, context, remaining_lines)

            # Update the scene summary based on the best available information (we hope)
            scene.summary = self.SanitiseSummary(scene.summary) or self.SanitiseSummary(context.get('scene')) or self.SanitiseSummary(context.get('summary'))

            # Notify observers the scene was translated
            self.events.scene_translated(scene)

        except (TranslationAbortedError, TranslationImpossibleError) as e:
            raise

        except Exception as e:
            if self.stop_on_error:
                raise
            else:
                logging.warning(f"Failed to translate scene {scene.number} ({str(e)})... finishing")

    def TranslateBatches(self, batches : list[SubtitleBatch], line_numbers : list[int], context : dict, remaining_lines=None):
        """
        Send batches of subtitles for translation, building up context.
        """
        for batch in batches:
            if self.aborted:
                raise TranslationAbortedError()

            if self.resume and batch.all_translated:
                logging.info(f"Scene {batch.scene} batch {batch.number} already translated {batch.size} lines...")
                continue

            if self.reparse and batch.translation:
                logging.info(f"Reparsing scene {batch.scene} batch {batch.number} with {len(originals)} lines...")
                translation = batch.translation
                self.ProcessTranslation(batch, line_numbers, context)
                continue

            originals, context = self.PreprocessBatch(batch, context)

            if remaining_lines and len(originals) > remaining_lines:
                logging.info("Truncating batch to remain within max_lines")
                originals = originals[:remaining_lines]

            try:
                logging.debug(f"Translating scene {batch.scene} batch {batch.number} with {len(originals)} lines...")

                if self.preview:
                    self.events.batch_translated(batch)
                    continue

                # Build summaries context
                context['batch'] = f"Scene {batch.scene} batch {batch.number}"
                context['summary'] = batch.summary

                batch.prompt = self.BuildTranslationPrompt(originals, context)

                # Ask the client to do the translation
                translation : Translation = self.client.RequestTranslation(batch.prompt)

                if self.aborted:
                    raise TranslationAbortedError()

                if not translation:
                    logging.warning(f"No translation for scene {batch.scene} batch {batch.number}")
                    if self.stop_on_error:
                        raise TranslationFailedError(f"No translation for scene {batch.scene} batch {batch.number}")

                if translation.reached_token_limit:
                    # Try again without the context to keep the tokens down
                    # TODO: better to split the batch into smaller chunks
                    logging.warning("Hit API token limit, retrying batch without context...")
                    batch.prompt.GenerateMessages(self.instructions.instructions, batch.originals, {})

                    translation = self.client.RequestTranslation(batch.prompt)

                batch.translation = translation

                # Process the response
                self.ProcessTranslation(batch, line_numbers, context)

                if batch.summary:
                    context['summaries'].append(batch.summary)  # TODO: may be out of order
                    context['summaries'] = context['summaries'][-self.max_context_summaries:]

                if self.stop_on_error and batch.errors:
                    raise TranslationFailedError(f"Failed to translate a batch... terminating", batch.translation, e)

            except (TranslationAbortedError, TranslationFailedError, TranslationImpossibleError) as e:
                raise

            except Exception as e:
                if self.stop_on_error:
                    raise
                else:
                    logging.warning(f"Failed to translate scene {batch.scene} batch {batch.number} ({str(e)})")

            if remaining_lines:
                remaining_lines = max(0, remaining_lines - len(originals))
                if not remaining_lines:
                    break

            # Notify observers the batch was translated
            self.events.batch_translated(batch)

    def BuildTranslationPrompt(self, lines : list, context : dict):
        """
        Generate a translation prompt for the context
        """
        prompt = TranslationPrompt(self.user_prompt, 
                                   conversation=self.client.supports_conversation, 
                                   supports_system_prompt=self.client.supports_system_prompt, 
                                   supports_system_messages=self.client.supports_system_messages)
        
        prompt.GenerateMessages(self.instructions.instructions, lines, context)
        return prompt

    def PreprocessBatch(self, batch : SubtitleBatch, context : dict):
        """
        Preprocess the batch before translation
        """
        if batch.context and (self.retranslate or self.reparse):
            # If it's a retranslation, restore context from the batch
            for key, value in batch.context.items():
                context[key] = value

        # Apply any substitutions to the input
        replacements = batch.PerformInputSubstitutions(self.substitutions, self.match_partial_words)

        if replacements:
            replaced = [f"{Linearise(k)} -> {Linearise(v)}" for k,v in replacements.items()]
            logging.info(f"Made substitutions in input:\n{linesep.join(replaced)}")
            batch.AddContext('replacements', replaced)

        # Split single lines with blocks of whitespace
        if self.whitespaces_to_newline:
            batch.ConvertWhitespaceBlocksToNewlines()

        # Filter out empty lines
        originals = RemoveEmptyLines(batch.originals)

        return originals, context

    def ProcessTranslation(self, batch : SubtitleBatch, line_numbers : list[int], context : dict):
        """
        Attempt to extract translation from the API response
        """
        translation : Translation = batch.translation

        if not translation.has_translation:
            raise ValueError("Translation contains no translated text")
        
        logging.debug(f"Scene {batch.scene} batch {batch.number} translation:\n{translation.text}\n")

        try:
            # Apply the translation to the subtitles
            parser : TranslationParser = self.client.GetParser()
            
            try:
                parser.ProcessTranslation(translation)

                # Try to match the translations with the original lines
                translated, unmatched = parser.MatchTranslations(batch.originals)

                # Sanity check the results
                batch.errors = parser.ValidateTranslations()

                if unmatched:
                    logging.warning(f"Unable to match {len(unmatched)} lines with a source line")
                    batch.errors.append(UntranslatedLinesError(f"No translation found for {len(unmatched)} lines", unmatched))
            
            except (TranslationAbortedError, TranslationImpossibleError):
                raise

            except TranslationError as e:
                if not self.allow_retranslations:
                    raise
                else:
                    batch.errors.append(e)

            # Consider retrying if there were errors
            if batch.errors and self.allow_retranslations and not self.aborted:
                logging.warn(f"Scene {batch.scene} batch {batch.number} failed validation, requesting retranslation")
                retranslated = self.RequestRetranslations(batch)

                if retranslated:
                    translated = MergeTranslations(translated or [], retranslated)

            # Assign the translated lines to the batch
            if line_numbers:
                translated = [line for line in translated if line.number in line_numbers]
                batch.translated = MergeTranslations(batch.translated or [], translated)
            else:
                batch.translated = translated

            if batch.untranslated:
                batch.AddContext('untranslated_lines', [f"{item.number}. {item.text}" for item in batch.untranslated])

            # Apply any word/phrase substitutions to the translation 
            replacements = batch.PerformOutputSubstitutions(self.substitutions, self.match_partial_words)

            if replacements:
                replaced = [f"{k} -> {v}" for k,v in replacements.items()]
                logging.info(f"Made substitutions in output:\n{linesep.join(replaced)}")

            # Perform substitutions on the output
            translation.PerformSubstitutions(self.substitutions, self.match_partial_words)

            # Update the context, unless it's a retranslation pass
            if not self.retranslate:
                batch.summary = self.SanitiseSummary(translation.summary or batch.summary)
                scene_summary = self.SanitiseSummary(translation.scene)

                context['summary'] = batch.summary
                context['scene'] = scene_summary or context['scene']
                context['synopsis'] = translation.synopsis or context.get('synopsis', "")
                #context['names'] = translation.names or context.get('names', []) or options.get('names')
                batch.UpdateContext(context)

            logging.info(f"Scene {batch.scene} batch {batch.number}: {len(batch.translated or [])} lines and {len(batch.untranslated or [])} untranslated.")

            if batch.summary and batch.summary.strip():
                logging.info(f"Summary: {batch.summary}")

        except TranslationError as te:
            if self.stop_on_error:
                raise
            else:
                logging.warning(f"Error translating batch: {str(te)}")

    def RequestRetranslations(self, batch : SubtitleBatch):
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

        if not isinstance(retranslation, Translation):
            raise TranslationError("Retranslation is not the expected type")

        logging.debug(f"Scene {batch.scene} batch {batch.number} retranslation:\n{retranslation.text}\n")

        parser : TranslationParser = self.client.GetParser()

        retranslated = parser.ProcessTranslation(retranslation)

        if not retranslated:
            #TODO line-by-line retranslation? Automatic batch splitting?
            logging.error("Retranslation request did not produce a useful result")
            return []
        
        try:
            _, unmatched = parser.MatchTranslations(batch.originals)

            batch.errors = parser.ValidateTranslations()

            if unmatched:
                logging.warning(f"Still unable to match {len(unmatched)} lines with a source line - try splitting the batch")
                batch.errors.append(UntranslatedLinesError(f"No translation found for {len(unmatched)} lines", unmatched))
            else:
                logging.info("Retranslation passed validation")

        except TranslationError as e:
            logging.warn(f"Retranslation request did not fix problems:\n{retranslation.text}\n")

        return retranslated

    def SanitiseSummary(self, summary : str):
        if not summary:
            return None

        summary = re.sub(r'^(?:(?:Scene|Batch)[\s\d:\-]*)+', '', summary, flags=re.IGNORECASE)
        summary = summary.replace("Summary of the batch", "")
        summary = summary.replace("Summary of the scene", "")

        movie_name = self.settings.get('movie_name')
        if movie_name:
            # Remove movie name and any connectors (-,: or whitespace)
            summary = re.sub(r'^' + re.escape(movie_name) + r'\s*[:\-]\s*', '', summary)

        summary = summary.strip()
        original_len = len(summary)
        
        summary = LimitTextLength(summary, self.max_summary_length)

        if len(summary) != original_len:
            logging.info(f"Summary was truncated from {original_len} to {len(summary)} characters")
        
        return summary or None

