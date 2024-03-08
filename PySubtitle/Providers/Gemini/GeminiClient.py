import logging
import google.generativeai as genai

from PySubtitle.Helpers import FormatMessages
from PySubtitle.SubtitleError import NoTranslationError, TranslationAbortedError, TranslationImpossibleError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt

class GeminiClient(TranslationClient):
    """
    Handles communication with Google Gemini to request translations
    """
    def __init__(self, settings : dict):
        super().__init__(settings)

        genai.configure(api_key=self.api_key)
        
        logging.info(f"Translating with Gemini {self.model or 'default'} model")

        self.gemini_model = genai.GenerativeModel(self.model)
        self.safety_settings = {
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",            
        }

    @property
    def api_key(self):
        return self.settings.get('api_key')
    
    @property
    def model(self):
        return self.settings.get('model')
    
    @property
    def rate_limit(self):
        return self.settings.get('rate_limit')
    
    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        temperature = temperature or self.temperature
        content = self._send_messages(prompt.messages, temperature)

        return Translation(content)
    
    def _abort(self):
        # TODO cancel any ongoing requests
        return super()._abort()

    def GetParser(self):
        return TranslationParser(self.settings)
    
    def _send_messages(self, messages : list, temperature):
        """
        Make a request to the Gemini API to provide a translation
        """
        content = {}
        retries = 0

        prompt = self._build_prompt(messages)

        try:
            config = genai.GenerationConfig(candidate_count=1, temperature=temperature)
            response = self.gemini_model.generate_content(prompt, 
                                                          generation_config=config, 
                                                          safety_settings=self.safety_settings)

            if self.aborted:
                raise TranslationAbortedError()

            if not response.candidates:
                raise NoTranslationError("No candidates returned in the response", response)

            candidate = response.candidates[0]
            if not candidate.content.parts:
                raise NoTranslationError("Gemini response has no content parts", response)

            response_text = "\n".join(part.text for part in candidate.content.parts)

            if not response_text:
                raise NoTranslationError("Gemini response is empty", response)

            content['text'] = response_text

            return content
        
        except Exception as e:
            raise TranslationImpossibleError(f"Unexpected error communicating with Gemini", content, error=e)

    def _build_prompt(self, messages : list):
        return "\n\n".join([ f"#{m.get('role')} ###\n{m.get('content')}" for m in messages ])