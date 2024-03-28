import logging
import time
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from PySubtitle.Helpers import FormatMessages
from PySubtitle.SubtitleError import TranslationImpossibleError, TranslationResponseError
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
        response = self._send_messages(prompt.content, temperature)

        return Translation(response) if response else None
    
    def _abort(self):
        # TODO cancel any ongoing requests
        return super()._abort()

    def GetParser(self):
        return TranslationParser(self.settings)
    
    def _send_messages(self, completion : str, temperature):
        """
        Make a request to the Gemini API to provide a translation
        """
        response = {}

        for retry in range(self.max_retries + 1):
            if self.aborted:
                return None

            try:
                config = genai.GenerationConfig(candidate_count=1, temperature=temperature)
                gcr : GenerateContentResponse = self.gemini_model.generate_content(completion, 
                                                                                        generation_config=config, 
                                                                                        safety_settings=self.safety_settings)

            except Exception as e:
                if retry < self.max_retries and not self.aborted:
                    logging.warning(f"Gemini request failure {str(e)}, trying to reconnect...")
                    sleep_time = self.backoff_time * 2.0**retry
                    time.sleep(sleep_time)
                
                    self.gemini_model = genai.GenerativeModel(self.model)
                    continue

            if self.aborted:
                return None

            if gcr.prompt_feedback.block_reason:
                raise TranslationResponseError(f"Request was blocked by Gemini: {str(gcr.prompt_feedback.block_reason)}", response=gcr)

            if not gcr.candidates:
                raise TranslationResponseError("No candidates returned in the response", response=gcr)

            # Try to find a validate candidate
            candidates = [candidate for candidate in gcr.candidates if candidate.finish_reason == "STOP"] or gcr.candidates

            candidate = candidates[0]
            response['token_count'] = candidate.token_count

            finish_reason = candidate.finish_reason
            if finish_reason == "STOP":
                response['finish_reason'] = "complete"
            elif finish_reason == "MAX_TOKENS":
                response['finish_reason'] = "length"
                raise TranslationResponseError("Gemini response exceeded token limit", response=candidate)
            elif finish_reason == "SAFETY":
                response['finish_reason'] = "blocked"
                raise TranslationResponseError("Gemini response was blocked for safety reasons", response=candidate)
            elif finish_reason == "RECITATION":
                response['finish_reason'] = "recitation"
                raise TranslationResponseError("Gemini response was blocked for recitation", response=candidate)
            elif finish_reason == "FINISH_REASON_UNSPECIFIED":
                response['finish_reason'] = "unspecified"
                raise TranslationResponseError("Gemini response was incomplete", response=candidate)
            else:
                # Probably a failure
                response['finish_reason'] = finish_reason

            response_text = "\n".join(part.text for part in candidate.content.parts)

            if not response_text:
                raise TranslationResponseError("Gemini response is empty", response=candidate)

            response['text'] = response_text

            return response

        raise TranslationImpossibleError(f"Failed to communicate with provider after {self.max_retries} retries")
