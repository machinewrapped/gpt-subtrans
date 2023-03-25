import logging
import openai
from os import linesep

from PySubtitleGPT.SubtitleBatcher import SubtitleBatcher
from PySubtitleGPT.ChatGPTClient import ChatGPTClient
from PySubtitleGPT.SubtitleError import TranslationError, TranslationFailedError, UntranslatedLinesError
from PySubtitleGPT.Helpers import BuildPrompt, Linearise, MergeTranslations, UnbatchScenes
from PySubtitleGPT.ChatGPTTranslationParser import ChatGPTTranslationParser

class SubtitleTranslator:
    """
    Processes subtitles into scenes and batches and sends them for translation
    """
    def __init__(self, options, project):
        """
        Initialise a SubtitleTranslator with translation options
        """
        if not options:
            raise Exception("No translation options provided")

        self.options = options
        self.project = project
        self.scenes = project.subtitles.scenes if project else None

    def TranslateSubtitles(self, subtitles, context=None):
        """
        Translate a SubtitleFile using the translation options
        """
        self.subtitles = subtitles
        options = self.options

        openai.api_key = options.api_key() or openai.api_key

        if not openai.api_key:
            raise ValueError('API key must be set in .env or provided as an argument')
        
        logging.info(f"Using API Key: {openai.api_key}")

        # Do the translation
        self.Translate(context)

        return self.scenes

    def Translate(self, context):
        """
        Perform the translation
        """
        options = self.options
        project = self.project

        if context:
            context_values = [f"{key}: {Linearise(value)}" for key, value in context.items()]
            logging.info(f"Translation context:\n{linesep.join(context_values)}")

        batcher = SubtitleBatcher(options)

        if self.scenes and project.resume:
            logging.info("Resuming translation")

        if not self.scenes:
            if project.retranslate or project.resume:
                logging.warning(f"Previous subtitles not found, starting fresh...")

            self.scenes = batcher.BatchSubtitles(self.subtitles)

        if not self.scenes:
            raise Exception("No scenes to translate")
        
        project.UpdateProjectFile(self.scenes)

        logging.info(f"Translating {len(self.subtitles)} subtitles in {len(self.scenes)} scenes")

        if not project.reparse:
            prompt = BuildPrompt(options)
            logging.info(f"Translation prompt: {prompt}")

        max_lines = options.get('max_lines')
        remaining_lines = max_lines

        # Iterate over each subtitle scene and request translation
        for scene_index, scene in enumerate(self.scenes):
            scene.number = scene_index + 1

            if project.resume and scene.batches and scene.all_translated:
                logging.info(f"Scene {scene.number} already translated {scene.linecount} lines...")
                continue

            logging.debug(f"Translating scene {scene.number} of {len(self.scenes)}")

            self.TranslateScene(scene, context, remaining_lines)

            if remaining_lines:
                remaining_lines = max(0, remaining_lines - scene.linecount)
                if not remaining_lines:
                    logging.info(f"Reached max_lines limit of ({max_lines} lines)... finishing")
                    break

        # Linearise the translated scenes
        subtitles, translations, untranslated = UnbatchScenes(self.scenes)

        if translations and not max_lines:
            logging.info(f"Successfully translated {len(translations)} subtitles!")

        if untranslated and not max_lines:
            logging.warning(f"Failed to translate {len(untranslated)} subtitles:")
            for subtitle in untranslated:
                logging.info(f"Untranslated > {subtitle.index}. {subtitle.text}")

        self.subtitles = subtitles
        self.translations = translations

    def TranslateScene(self, scene, context=None, remaining_lines=None):
        """
        Present a scene to ChatGPT for translation
        """
        options = self.options
        project = self.project
        prompt = options.get('prompt')

        scene.context = context.copy() if context else {}
        scene.AddContext('summary', "New scene")

        try:
            self.TranslateBatches(scene, prompt, scene.context, remaining_lines)

        except Exception as e:
            if project.write_project:
                project.UpdateProjectFile(self.scenes)

            if project.stop_on_error:
                raise
            else:
                logging.warning(f"Failed to translate all scenes ({str(e)})... finishing")

    # Present each batch of subtitles for translation
    def TranslateBatches(self, scene, prompt, context, remaining_lines=None):
        """
        Pass each batch of subtitles to ChatGPT for translation, building up context.
        """
        options = self.options
        project = self.project

        context = context or {}
        substitutions = context.get('substitutions')

        # Initialise the ChatGPT client
        client = ChatGPTClient(options, context.get('instructions'))

        for batch_index, batch in enumerate(scene.batches):
            batch.number = batch_index + 1

            if project.resume and batch.all_translated:
                logging.info(f"Scene {scene.number} batch {batch.number} already translated {batch.size} lines...")
                context['previous_batch'] = batch
                continue

            # If it's a retranslation, restore the context
            if project.retranslate or project.reparse:
                context = {**context, **batch.context}
            else:
                batch.SetContext({
                    'synopsis' : context.get('synopsis'),
                    'characters' : context.get('characters'),
                    'summary' : context.get('summary')
                    })

            # Apply any substitutions to the input
            replacements = batch.PerformInputSubstitutions(substitutions)

            # Filter out empty lines
            subtitles = [subtitle for subtitle in batch.subtitles if subtitle.text.strip()]

            if remaining_lines and len(subtitles) > remaining_lines:
                logging.info("Truncating batch to remain within max_lines")
                subtitles = subtitles[:remaining_lines]

            try:
                if  project.reparse and batch.translation:
                    logging.info(f"Reparsing scene {scene.number} batch {batch.number} with {len(subtitles)} lines...")
                    translation = batch.translation
                else:
                    logging.debug(f"Translating scene {scene.number} batch {batch.number} with {len(subtitles)} lines...")

                    if replacements:
                        replaced = [f"{Linearise(k)} -> {Linearise(v)}" for k,v in replacements.items()]
                        logging.info(f"Made substitutions in input:\n{linesep.join(replaced)}")

                    if project.preview:
                        project.UpdateProjectFile(self.scenes)
                        continue

                    # Ask OpenAI to do the translation
                    translation = client.RequestTranslation(prompt, subtitles, context)

                    if translation.reached_token_limit:
                        # Try again without the context to keep the tokens down
                        logging.warning("Hit API token limit, retrying batch without context...")
                        translation = client.RequestTranslation(prompt, subtitles, None)

                        if translation.reached_token_limit:
                            raise TranslationError(f"Too many tokens in translation", translation)

                if translation:
                    batch.translation = translation

                    # Process the response
                    self.ProcessTranslation(scene, batch, context, client)

                else:
                    logging.warning(f"No translation for scene {scene.number} batch {batch.number}")


            except TranslationError as e:
                if project.stop_on_error:
                    raise TranslationFailedError(f"Failed to translate a batch... terminating", batch.translation, e)
                else:
                    logging.warning(f"Error translating subtitle batch: {str(e)}")

            if remaining_lines:
                remaining_lines = max(0, remaining_lines - len(subtitles))
                if not remaining_lines:
                    break

            # Write WIP translations
            project.UpdateProjectFile(self.scenes)

            context['previous_batch'] = batch

    def ProcessTranslation(self, scene, batch, context, client):
        """
        Attempt to extract translation from the API response
        """
        options = self.options
        project = self.project
        substitutions = options.get('substitutions')

        translation = batch.translation

        if not translation.has_translation:
            raise ValueError("Translation contains no translated text")
        
        logging.debug(f"Scene {scene.number} batch {batch.number} translation:\n{translation.text}\n")

        try:
            # Apply the translation to the subtitles
            parser = ChatGPTTranslationParser(options)
            
            # Reset error list, hopefully they're obsolete
            batch.errors = []

            try:
                batch.translated = parser.ProcessChatGPTResponse(translation)

                # Try to match the translations with the original lines
                unmatched = parser.MatchTranslations(batch.subtitles)

                if unmatched:
                    logging.warning(f"Unable to match {len(unmatched)} subtitles with a source line")
                    if options.get('enforce_line_parity'):
                        raise UntranslatedLinesError(f"No translation found for {len(unmatched)} lines", unmatched)

                # Sanity check the results
                parser.ValidateTranslations()

            except TranslationError as e:
                if not options.get('allow_retranslations'):
                    raise
                else:
                    batch.errors.append(e)

            # Consider retrying if there were errors
            if batch.errors and options.get('allow_retranslations'):
                logging.info(f"Scene {scene.number} batch {batch.number} failed validation, requesting retranslation")
                self.RequestRetranslations(client, batch, translation)

            if batch.untranslated:
                batch.AddContext('untranslated_lines', [f"{item.index}. {item.text}" for item in batch.untranslated])

            # Apply any word/phrase substitutions to the translation 
            replacements = batch.PerformOutputSubstitutions(substitutions)

            if replacements:
                replaced = [f"{k} -> {v}" for k,v in replacements.items()]
                logging.info(f"Made substitutions in output:\n{linesep.join(replaced)}")

            # Perform substitutions on the output
            translation.PerformSubstitutions(substitutions)

            # Update the context, unless it's a retranslation pass
            if not project.retranslate:
                batch.summary = translation.summary or batch.summary
                self.UpdateContext(translation, batch, context)

            logging.info(f"Scene {scene.number} batch {batch.number}: {len(batch.translated)} subtitles and {len(batch.untranslated)} untranslated.")

            if batch.summary and batch.summary.strip():
                logging.info(f"Summary: {batch.summary}")

        except TranslationError as te:
            if project.stop_on_error:
                raise
            else:
                logging.warning(f"Error translating subtitle batch: {str(e)}")


    def RequestRetranslations(self, client, batch, translation):
        """
        Ask ChatGPT to retranslate any missing lines
        """
        retranslation = client.RequestRetranslation(translation, batch.errors)

        parser = ChatGPTTranslationParser(self.options)

        retranslated = parser.ProcessChatGPTResponse(retranslation)

        if not retranslated:
            logging.error("Retranslation request did not produce a useful result")
            return
        
        batch.AddContext('retranslated_lines', [f"{item.index}. {item.translation}" for item in retranslated])
        logging.info(f"Retranslated {len(retranslated)} of {len(retranslated) + len(batch.untranslated)} lines")

        try:
            parser.ValidateTranslations()

            logging.info("Retranslation passed validation")

        except TranslationError as e:
            # Let's assume the results were at least an improvement            
            logging.warn(f"Retranslation request did not fix problems:\n{retranslation.get('text')}\n")

        parser.MatchTranslations(batch.subtitles)

        MergeTranslations(batch.translated, retranslated)


    def UpdateContext(self, translation, batch, context):
        options = self.options
        context['summary'] = batch.summary or context['summary']
        context['synopsis'] = options.get('synopsis') or translation.synopsis or context['synopsis']
        #context['characters'] = options.get('characters') or translation.characters or context['characters']

