import logging
import openai

from PySubtitle.Helpers import FormatMessages
from PySubtitle.SubtitleError import TranslationError, TranslationImpossibleError
from PySubtitle.Translation import Translation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt

class OpenAIClient(TranslationClient):
    """
    Handles communication with OpenAI to request translations
    """
    def __init__(self, settings : dict):
        super().__init__(settings)

        if not hasattr(openai, "OpenAI"):
            raise Exception("The OpenAI library is out of date and must be updated")

        openai.api_key = self.api_key or openai.api_key

        if not openai.api_key:
            raise ValueError('API key must be set in .env or provided as an argument')
        
        if self.api_base:
            openai.base_url = self.api_base
        
        logging.info(f"Translating with OpenAI model {self.model or 'default'}, Using API Base: {openai.base_url}")

        self.client = openai.OpenAI(api_key=openai.api_key, base_url=openai.base_url)

    @property
    def api_key(self):
        return self.settings.get('api_key')
    
    @property
    def api_base(self):
        return self.settings.get('api_base')
    
    @property
    def model(self):
        return self.settings.get('model')
    
    @property
    def rate_limit(self):
        return self.settings.get('rate_limit')
    
    @property
    def max_retries(self):
        return self.settings.get('max_retries', 3.0)
    
    @property
    def backoff_time(self):
        return self.settings.get('backoff_time', 5.0)

    def _request_translation(self, prompt : TranslationPrompt, temperature : float = None) -> Translation:
        """
        Request a translation based on the provided prompt
        """
        logging.debug(f"Messages:\n{FormatMessages(prompt.messages)}")

        temperature = temperature or self.temperature
        content = self._send_messages(prompt.messages, temperature)

        translation = Translation(content)

        if translation.quota_reached:
            raise TranslationImpossibleError("OpenAI account quota reached, please upgrade your plan or wait until it renews", translation)

        if translation.reached_token_limit:
            # Try again without the context to keep the tokens down
            # TODO: better to split the batch into smaller chunks
            logging.warning("Hit API token limit, retrying batch without context...")
            prompt.GenerateReducedMessages()

            content = self._send_messages(prompt.messages, temperature)

            translation = Translation(content)

            if translation.reached_token_limit:
                raise TranslationError(f"Too many tokens in translation", translation)

        return translation

    def _send_messages(self, messages : list[str], temperature : float):
        """
        Communicate with the API
        """
        raise NotImplementedError("Not implemented in the base class")#

    def _abort(self):
        self.client.close()
        return super()._abort()

    def GetParser(self):
        return TranslationParser(self.settings)
    
