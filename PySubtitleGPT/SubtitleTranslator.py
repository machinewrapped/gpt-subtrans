import logging
import re
import openai
from os import linesep
from PySubtitleGPT.ChatGPTClient import ChatGPTClient
from PySubtitleGPT.ChatGPTTranslation import ChatGPTTranslation
from PySubtitleGPT.ChatGPTTranslationParser import ChatGPTTranslationParser
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.SubtitleBatcher import SubtitleBatcher

from PySubtitleGPT.SubtitleError import TranslationAbortedError, TranslationError, TranslationFailedError, TranslationImpossibleError, UntranslatedLinesError
from PySubtitleGPT.Helpers import BuildPrompt, Linearise, MergeTranslations, ParseSubstitutions, UnbatchScenes
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.TranslationEvents import TranslationEvents

class SubtitleTranslator:
    """
    Processes subtitles into scenes and batches and sends them for translation
    """
    @classmethod
    def __init__(self, subtitles : SubtitleFile, options : Options):
        """
        Initialise a SubtitleTranslator with translation options
        """
        if not options:
            raise Exception("No translation options provided")

        if not hasattr(openai, "OpenAI"):
            raise Exception("The OpenAI library is out of date and must be updated")
        
        openai.api_key = options.api_key() or openai.api_key

        if not openai.api_key:
            raise ValueError('API key must be set in .env or provided as an argument')
        
        if options.api_base():
            openai.base_url = options.api_base()
        
        logging.debug(f"Using API Key: {openai.api_key}, Using API Base: {openai.base_url}")

        self.subtitles = subtitles
        self.options = options
        self.events = TranslationEvents()
        self.aborted = False

        if not options.get('reparse') or not options.get('prompt'):
            options.add('prompt', BuildPrompt(options))

        logging.debug(f"Translation prompt: {options.get('prompt')}")
 
        # Update subtitle context from options and make our own copy of it
        self.context = subtitles.UpdateContext(options).copy()

        context_values = [f"{key}: {Linearise(value)}" for key, value in self.context.items()]
        logging.debug(f"Translation context:\n{linesep.join(context_values)}")

    @classmethod
    def GetAvailableModels(cls, api_key : str, api_base : str):
        """
        Returns a list of possible values for the LLM model 
        """
        try:
            if not hasattr(openai, "OpenAI"):
                raise Exception("The OpenAI library is out of date and must be updated")
        
            client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            response = client.models.list()

            if not response or not response.data:
                return []

            model_list = [model.id for model in response.data if model.id.startswith('gpt') and model.id.find('instruct') < 0 and model.id.find('vision') < 0]

            return sorted(model_list)

        except Exception as e:
            logging.error(f"Unable to retrieve available AI models: {str(e)}")
            return []

    def StopTranslating(self):
        self.aborted = True

    def TranslateSubtitles(self):
        """
        Translate a SubtitleFile
        """
        options : Options = self.options
        subtitles : SubtitleFile = self.subtitles 

        if self.aborted:
            raise TranslationAbortedError()

        if not subtitles:
            raise TranslationError("No subtitles to translate")
    
        if subtitles.scenes and options.get('resume'):
            logging.info("Resuming translation")

        if not subtitles.scenes:
            if options.get('retranslate') or options.get('resume'):
                logging.warning(f"Previous subtitles not found, starting fresh...")

            self.subtitles.AutoBatch(options)

        if not subtitles.scenes:
            raise Exception("No scenes to translate")
        
        logging.info(f"Translating {subtitles.linecount} lines in {subtitles.scenecount} scenes")

        self.events.preprocessed(subtitles.scenes)

        max_lines = options.get('max_lines')
        remaining_lines = max_lines

        # Iterate over each subtitle scene and request translation
        for scene in subtitles.scenes:
            if self.aborted:
                raise TranslationAbortedError()

            if options.get('resume') and scene.all_translated:
                    logging.info(f"Scene {scene.number} already translated {scene.linecount} lines...")
                    continue

            logging.debug(f"Translating scene {scene.number} of {subtitles.scenecount}")
            batch_numbers = [ batch.number for batch in scene.batches if not batch.translated ] if options.get('resume') else None

            self.TranslateScene(scene, batch_numbers=batch_numbers, remaining_lines=remaining_lines)

            if remaining_lines:
                remaining_lines = max(0, remaining_lines - scene.linecount)
                if not remaining_lines:
                    logging.info(f"Reached max_lines limit of ({max_lines} lines)... finishing")
                    break

        # Linearise the translated scenes
        originals, translations, untranslated = UnbatchScenes(subtitles.scenes)

        if translations and not max_lines:
            logging.info(f"Successfully translated {len(translations)} lines!")

        if untranslated and not max_lines:
            logging.warning(f"Failed to translate {len(untranslated)} lines:")
            for line in untranslated:
                logging.info(f"Untranslated > {line.number}. {line.text}")

        subtitles.originals = originals
        subtitles.translated = translations

    def TranslateScene(self, scene : SubtitleScene, batch_numbers = None, remaining_lines=None):
        """
        Present a scene to ChatGPT for translation
        """
        options : Options = self.options
        
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

            self.TranslateBatches(batches, context, remaining_lines)

            # Update the scene summary based on the best available information (we hope)
            scene.summary = self.SanitiseSummary(scene.summary) or self.SanitiseSummary(context.get('scene')) or self.SanitiseSummary(context.get('summary'))

            # Notify observers the scene was translated
            self.events.scene_translated(scene)

        except Exception as e:
            if options.get('stop_on_error'):
                raise
            else:
                logging.warning(f"Failed to translate scene {scene.number} ({str(e)})... finishing")

    def TranslateBatches(self, batches : list[SubtitleBatch], context : dict, remaining_lines=None):
        """
        Pass batches of subtitles ChatGPT for translation, building up context.
        """
        options : Options = self.options

        substitutions = ParseSubstitutions(context.get('substitutions', {}))
        match_partial_words = options.get('match_partial_words')

        # Initialise the ChatGPT client
        client = ChatGPTClient(options, context.get('instructions'))

        prompt = options.get('prompt')
        max_context_summaries = options.get('max_context_summaries')

        for batch in batches:
            if self.aborted:
                raise TranslationAbortedError()

            if options.get('resume') and batch.all_translated:
                logging.info(f"Scene {batch.scene} batch {batch.number} already translated {batch.size} lines...")
                continue

            if batch.context and (options.get('retranslate') or options.get('reparse')):
                # If it's a retranslation, restore context from the batch
                context = {**context, **batch.context}

            # Apply any substitutions to the input
            replacements = batch.PerformInputSubstitutions(substitutions, match_partial_words)

            # Split single lines with blocks of whitespace
            if options.get('whitespaces_to_newline'):
                batch.ConvertWhitespaceBlocksToNewlines()

            # Filter out empty lines
            originals = [line for line in batch.originals if line.text and line.text.strip()]

            if remaining_lines and len(originals) > remaining_lines:
                logging.info("Truncating batch to remain within max_lines")
                originals = originals[:remaining_lines]

            try:
                if  options.get('reparse') and batch.translation:
                    logging.info(f"Reparsing scene {batch.scene} batch {batch.number} with {len(originals)} lines...")
                    translation = batch.translation
                else:
                    logging.debug(f"Translating scene {batch.scene} batch {batch.number} with {len(originals)} lines...")

                    if replacements:
                        replaced = [f"{Linearise(k)} -> {Linearise(v)}" for k,v in replacements.items()]
                        logging.info(f"Made substitutions in input:\n{linesep.join(replaced)}")

                    if options.get('preview'):
                        self.events.batch_translated(batch)
                        continue

                    # Build summaries context
                    context['summaries'] = self.subtitles.GetBatchContext(batch.scene, batch.number, max_context_summaries)
                    context['summary'] = batch.summary
                    context['batch'] = f"Scene {batch.scene} batch {batch.number}"

                    # Ask OpenAI to do the translation
                    translation : ChatGPTTranslation = client.RequestTranslation(prompt, originals, context)

                    if self.aborted:
                        raise TranslationAbortedError()

                    if translation.quota_reached:
                        raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan or wait until it renews", translation)

                    if translation.reached_token_limit:
                        # Try again without the context to keep the tokens down
                        logging.warning("Hit API token limit, retrying batch without context...")
                        translation = client.RequestTranslation(prompt, originals, None)

                        if translation.reached_token_limit:
                            raise TranslationError(f"Too many tokens in translation", translation)

                if translation:
                    translation.ParseResponse()

                    batch.translation = translation
                    batch.AddContext('summary', context.get('summary'))
                    batch.AddContext('summaries', context.get('summaries'))

                    # Process the response
                    self.ProcessTranslation(batch, context, client)

                else:
                    logging.warning(f"No translation for scene {batch.scene} batch {batch.number}")

            except TranslationError as e:
                if options.get('stop_on_error') or isinstance(e, TranslationImpossibleError):
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

    def ProcessTranslation(self, batch : SubtitleBatch, context : dict, client : ChatGPTClient):
        """
        Attempt to extract translation from the API response
        """
        options : Options = self.options
        substitutions = options.get('substitutions')
        match_partial_words = options.get('match_partial_words')

        translation : ChatGPTTranslation = batch.translation

        if not translation.has_translation:
            raise ValueError("Translation contains no translated text")
        
        logging.debug(f"Scene {batch.scene} batch {batch.number} translation:\n{translation.text}\n")

        try:
            # Apply the translation to the subtitles
            parser = ChatGPTTranslationParser(options)
            
            # Reset error list, hopefully they're obsolete
            batch.errors = []

            try:
                parser.ProcessChatGPTResponse(translation)

                # Try to match the translations with the original lines
                batch.translated, unmatched = parser.MatchTranslations(batch.originals)

                if unmatched:
                    logging.warning(f"Unable to match {len(unmatched)} lines with a source line")
                    if options.get('enforce_line_parity'):
                        raise UntranslatedLinesError(f"No translation found for {len(unmatched)} lines", unmatched)

                # Sanity check the results
                parser.ValidateTranslations()
            
            except TranslationAbortedError:
                raise

            except TranslationError as e:
                if not options.get('allow_retranslations'):
                    raise
                else:
                    batch.errors.append(e)

            # Consider retrying if there were errors
            if batch.errors and options.get('allow_retranslations'):
                logging.warn(f"Scene {batch.scene} batch {batch.number} failed validation, requesting retranslation")
                self.RequestRetranslations(client, batch, translation)

            if batch.untranslated:
                batch.AddContext('untranslated_lines', [f"{item.number}. {item.text}" for item in batch.untranslated])

            # Apply any word/phrase substitutions to the translation 
            replacements = batch.PerformOutputSubstitutions(substitutions, match_partial_words)

            if replacements:
                replaced = [f"{k} -> {v}" for k,v in replacements.items()]
                logging.info(f"Made substitutions in output:\n{linesep.join(replaced)}")

            # Perform substitutions on the output
            translation.PerformSubstitutions(substitutions, match_partial_words)

            # Update the context, unless it's a retranslation pass
            if not options.get('retranslate'):
                batch.summary : str = self.SanitiseSummary(translation.summary or batch.summary)
                scene_summary : str = self.SanitiseSummary(translation.scene)

                context['summary'] = batch.summary
                context['scene'] = scene_summary or context['scene']
                context['synopsis'] = translation.synopsis or context.get('synopsis', "")
                #context['characters'] = translation.characters or context.get('characters', []) or options.get('characters')
                batch.UpdateContext(context)

            logging.info(f"Scene {batch.scene} batch {batch.number}: {len(batch.translated or [])} lines and {len(batch.untranslated or [])} untranslated.")

            if batch.summary and batch.summary.strip():
                logging.info(f"Summary: {batch.summary}")

        except TranslationError as te:
            if options.get('stop_on_error'):
                raise
            else:
                logging.warning(f"Error translating batch: {str(te)}")


    def RequestRetranslations(self, client : ChatGPTClient, batch : SubtitleBatch, translation : str):
        """
        Ask ChatGPT to retranslate any missing lines
        """
        retranslation : ChatGPTTranslation = client.RequestRetranslation(translation, batch.errors)

        if not isinstance(retranslation, ChatGPTTranslation):
            raise TranslationError("Retranslation is not the expected type")

        logging.debug(f"Scene {batch.scene} batch {batch.number} retranslation:\n{retranslation.text}\n")

        parser = ChatGPTTranslationParser(self.options)

        retranslated = parser.ProcessChatGPTResponse(retranslation)

        if retranslated:
            batch.AddContext('retranslated_lines', [f"{item.key}. {item.text}" for item in retranslated])
            logging.info(f"Retranslated {len(retranslated)} of {len(retranslated) + len(batch.untranslated)} lines")
        else:
            #TODO line-by-line retranslation?
            logging.error("Retranslation request did not produce a useful result")
            # return
        
        try:
            parser.MatchTranslations(batch.originals)

            parser.ValidateTranslations()

            logging.info("Retranslation passed validation")

            batch.translated = MergeTranslations(batch.translated or {}, retranslated)

            batch.Validate(self.options)

        except TranslationError as e:
            logging.warn(f"Retranslation request did not fix problems:\n{retranslation.text}\n")

    def SanitiseSummary(self, summary : str):
        if not summary:
            return None

        summary = re.sub(r'^(?:(?:Scene|Batch)[\s\d:\-]*)+', '', summary, flags=re.IGNORECASE)

        movie_name = self.options.get('movie_name')
        if movie_name:
            # Remove movie name and any connectors (-,: or whitespace)
            summary = re.sub(r'^' + re.escape(movie_name) + r'\s*[:\-]\s*', '', summary)

        return summary.strip() if summary.strip() else None
