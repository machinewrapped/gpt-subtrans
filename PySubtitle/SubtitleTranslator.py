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

from PySubtitle.SubtitleError import TranslationAbortedError, TranslationError, TranslationFailedError, TranslationImpossibleError, UntranslatedLinesError
from PySubtitle.Helpers import BuildPrompt, Linearise, MergeTranslations, ParseSubstitutions, UnbatchScenes
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.TranslationEvents import TranslationEvents
from PySubtitle.TranslationProvider import TranslationProvider

class SubtitleTranslator:
    """
    Processes subtitles into scenes and batches and sends them for translation
    """
    def __init__(self, options: Options):
        """
        Initialise a SubtitleTranslator with translation options
        """
        self.events = TranslationEvents()
        self.aborted = False

        self.max_lines = options.get('max_lines')
        self.max_context_summaries = options.get('max_context_summaries')
        self.stop_on_error = options.get('stop_on_error')
        self.enforce_line_parity = options.get('enforce_line_parity')
        self.allow_retranslations = options.get('allow_retranslations')
        self.whitespaces_to_newline = options.get('whitespaces_to_newline')
        self.match_partial_words = options.get('match_partial_words')
        self.resume = options.get('resume')
        self.retranslate = options.get('retranslate')
        self.reparse = options.get('reparse')
        self.preview = options.get('preview')

        self.settings = options.GetSettings()
        self.instructions : Instructions = options.GetInstructions()
        self.prompt : str = BuildPrompt(options)
        self.settings['instructions'] = self.instructions.instructions
        self.settings['retry_instructions'] = self.instructions.retry_instructions

        logging.debug(f"Translation prompt: {self.prompt}")
 
        self.provider_class : TranslationProvider = TranslationProvider.get_provider(options)
        if not self.provider_class:
            raise Exception("Unable to create translation provider")

        self.client : TranslationClient = self.provider_class.GetTranslationClient(self.settings)
        if not self.client:
            raise Exception("Unable to create translation client")
        
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
        if not scene.context:
            scene.context = self.context.copy()
        else:
            scene.context = {**scene.context, **self.context}

        try:
            if batch_numbers:
                batches = [ batch for batch in scene.batches if batch.number in batch_numbers ]
            else:
                batches = scene.batches

            context = scene.context.copy()
            context['scene'] = f"Scene {scene.number}: {scene.summary}" if scene.summary else f"Scene {scene.number}"

            self.TranslateBatches(subtitles, batches, line_numbers, context, remaining_lines)

            # Update the scene summary based on the best available information (we hope)
            scene.summary = self.SanitiseSummary(scene.summary) or self.SanitiseSummary(context.get('scene')) or self.SanitiseSummary(context.get('summary'))

            # Notify observers the scene was translated
            self.events.scene_translated(scene)

        except TranslationAbortedError:
            raise

        except Exception as e:
            if self.stop_on_error:
                raise
            else:
                logging.warning(f"Failed to translate scene {scene.number} ({str(e)})... finishing")

    def TranslateBatches(self, subtitles : SubtitleFile, batches : list[SubtitleBatch], line_numbers : list[int], context : dict, remaining_lines=None):
        """
        Send batches of subtitles for translation, building up context.
        """
        substitutions = ParseSubstitutions(context.get('substitutions', {}))

        for batch in batches:
            if self.aborted:
                raise TranslationAbortedError()

            if self.resume and batch.all_translated:
                logging.info(f"Scene {batch.scene} batch {batch.number} already translated {batch.size} lines...")
                continue

            if batch.context and (self.retranslate or self.reparse):
                # If it's a retranslation, restore context from the batch
                context = {**context, **batch.context}

            # Apply any substitutions to the input
            replacements = batch.PerformInputSubstitutions(substitutions, self.match_partial_words)

            # Split single lines with blocks of whitespace
            if self.whitespaces_to_newline:
                batch.ConvertWhitespaceBlocksToNewlines()

            # Filter out empty lines
            originals = [line for line in batch.originals if line.text and line.text.strip()]

            if remaining_lines and len(originals) > remaining_lines:
                logging.info("Truncating batch to remain within max_lines")
                originals = originals[:remaining_lines]

            try:
                if  self.reparse and batch.translation:
                    logging.info(f"Reparsing scene {batch.scene} batch {batch.number} with {len(originals)} lines...")
                    translation = batch.translation
                else:
                    logging.debug(f"Translating scene {batch.scene} batch {batch.number} with {len(originals)} lines...")

                    if replacements:
                        replaced = [f"{Linearise(k)} -> {Linearise(v)}" for k,v in replacements.items()]
                        logging.info(f"Made substitutions in input:\n{linesep.join(replaced)}")

                    if self.preview:
                        self.events.batch_translated(batch)
                        continue

                    # Build summaries context
                    context['summaries'] = subtitles.GetBatchContext(batch.scene, batch.number, self.max_context_summaries)
                    context['summary'] = batch.summary
                    context['batch'] = f"Scene {batch.scene} batch {batch.number}"

                    # Ask the client to do the translation
                    translation : Translation = self.client.RequestTranslation(self.prompt, originals, context)

                    if self.aborted:
                        raise TranslationAbortedError()

                    if translation.quota_reached:
                        raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan or wait until it renews", translation)

                    if translation.reached_token_limit:
                        # Try again without the context to keep the tokens down
                        logging.warning("Hit API token limit, retrying batch without context...")
                        translation = self.client.RequestTranslation(self.prompt, originals, None)

                        if translation.reached_token_limit:
                            raise TranslationError(f"Too many tokens in translation", translation)

                if translation:
                    translation.ParseResponse()

                    batch.translation = translation
                    batch.AddContext('summary', context.get('summary'))
                    batch.AddContext('summaries', context.get('summaries'))

                    # Process the response
                    self.ProcessTranslation(batch, line_numbers, context)

                else:
                    logging.warning(f"No translation for scene {batch.scene} batch {batch.number}")

            except TranslationAbortedError:
                raise
                    
            except TranslationError as e:
                if self.stop_on_error or isinstance(e, TranslationImpossibleError):
                    raise TranslationFailedError(f"Failed to translate a batch... terminating", batch.translation, e)
                else:
                    logging.warning(f"Error translating batch: {str(e)}")

            if remaining_lines:
                remaining_lines = max(0, remaining_lines - len(originals))
                if not remaining_lines:
                    break

            context['previous_batch'] = batch

            # Notify observers the batch was translated
            self.events.batch_translated(batch)

    def ProcessTranslation(self, batch : SubtitleBatch, line_numbers : list[int], context : dict):
        """
        Attempt to extract translation from the API response
        """
        substitutions = self.context.get('substitutions')

        translation : Translation = batch.translation

        if not translation.has_translation:
            raise ValueError("Translation contains no translated text")
        
        logging.debug(f"Scene {batch.scene} batch {batch.number} translation:\n{translation.text}\n")

        try:
            # Apply the translation to the subtitles
            parser : TranslationParser = self.client.GetParser()
            
            # Reset error list, hopefully they're obsolete
            batch.errors = []

            try:
                parser.ProcessTranslation(translation)

                # Try to match the translations with the original lines
                translated, unmatched = parser.MatchTranslations(batch.originals)

                if unmatched:
                    logging.warning(f"Unable to match {len(unmatched)} lines with a source line")
                    if self.enforce_line_parity:
                        raise UntranslatedLinesError(f"No translation found for {len(unmatched)} lines", unmatched)

                # Sanity check the results
                parser.ValidateTranslations()
            
            except TranslationAbortedError:
                raise

            except TranslationError as e:
                if not self.allow_retranslations:
                    raise
                else:
                    batch.errors.append(e)

            # Consider retrying if there were errors
            if batch.errors and self.allow_retranslations and not self.aborted:
                logging.warn(f"Scene {batch.scene} batch {batch.number} failed validation, requesting retranslation")
                retranslated = self.RequestRetranslations(batch, translation)

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
            replacements = batch.PerformOutputSubstitutions(substitutions, self.match_partial_words)

            if replacements:
                replaced = [f"{k} -> {v}" for k,v in replacements.items()]
                logging.info(f"Made substitutions in output:\n{linesep.join(replaced)}")

            # Perform substitutions on the output
            translation.PerformSubstitutions(substitutions, self.match_partial_words)

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


    def RequestRetranslations(self, batch : SubtitleBatch, translation : str):
        """
        Ask the client to retranslate the input and correct errors
        """
        retranslation : Translation = self.client.RequestRetranslation(translation, batch.errors)

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
            batch.errors = []

            _, unmatched = parser.MatchTranslations(batch.originals)

            if unmatched:
                logging.warning(f"Still unable to match {len(unmatched)} lines with a source line - try splitting the batch")
                batch.errors.append(UntranslatedLinesError(f"No translation found for {len(unmatched)} lines", unmatched))

            parser.ValidateTranslations()

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

        movie_name = self.context.get('movie_name')
        if movie_name:
            # Remove movie name and any connectors (-,: or whitespace)
            summary = re.sub(r'^' + re.escape(movie_name) + r'\s*[:\-]\s*', '', summary)

        return summary.strip() if summary.strip() else None

