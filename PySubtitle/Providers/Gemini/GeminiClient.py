import logging
import google.generativeai as genai

from PySubtitle.Helpers import FormatMessages
from PySubtitle.Providers.Gemini.GeminiPrompt import GeminiPrompt
from PySubtitle.SubtitleError import NoTranslationError, TranslationAbortedError, TranslationImpossibleError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser

class GeminiClient(TranslationClient):
    """
    Handles communication with Google Gemini to request translations
    """
    def __init__(self, settings : dict):
        super().__init__(settings)

        genai.configure(api_key=self.api_key)
        
        logging.info(f"Translating with Gemini {self.model or 'default'} model")

        self.gemini_config = genai.GenerationConfig(candidate_count=1, temperature=self.temperature)
        self.gemini_model = genai.GenerativeModel(self.model)

    @property
    def api_key(self):
        return self.settings.get('api_key')
    
    @property
    def model(self):
        return self.settings.get('model')
    
    @property
    def temperature(self):
        return self.settings.get('temperature', 0.0)
    
    @property
    def rate_limit(self):
        return self.settings.get('rate_limit')
    
    def _request_translation(self, prompt, lines, context) -> Translation:
        """
        Generate the prompt and request a translation
        """
        gemini_prompt = GeminiPrompt(self.instructions)

        gemini_prompt.GenerateMessages(prompt, lines, context)

        logging.debug(f"Messages:\n{FormatMessages(gemini_prompt.messages)}")

        gemini_translation = self._send_messages(gemini_prompt.messages)

        translation = Translation(gemini_translation, gemini_prompt)

        return translation
    
    def _abort(self):
        self.client.close()
        return super()._abort()

    def GetParser(self):
        return TranslationParser(self.settings)
    
    def _send_messages(self, messages : list, temperature : float = None):
        """
        Make a request to the Gemini API to provide a translation
        """
        translation = {}
        retries = 0

        prompt = self._build_prompt(messages)

        try:
            response = self.gemini_model.generate_content(prompt, generation_config=self.gemini_config)

            if self.aborted:
                raise TranslationAbortedError()

            if hasattr(response, 'text'):
                response_text = response.text
            else:
                # We only expect one choice to be returned as we have 0 temperature
                if not response.candidates:
                    raise NoTranslationError("No candidates returned in the response", response)

                candidate = response.candidates[0]
                if not candidate.content.parts:
                    raise NoTranslationError("Gemini response has no content parts")

                response_text = "\n".join(part.text for part in candidate.content.parts)

            if not response_text:
                raise NoTranslationError("Gemini response is empty")

            translation['text'] = response_text

            # Return the response if the API call succeeds
            return translation
        
        except Exception as e:
            raise TranslationImpossibleError(f"Unexpected error communicating with Gemini", translation, error=e)

    def _build_prompt(self, messages : list):
        return "\n\n".join([ f"#{m.get('role')} ###\n{m.get('content')}" for m in messages ])