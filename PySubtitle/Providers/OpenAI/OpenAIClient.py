import logging
import openai

from PySubtitle.Helpers import FormatMessages
from PySubtitle.Providers.OpenAI.GPTPrompt import GPTPrompt
from PySubtitle.Providers.OpenAI.GPTTranslation import GPTTranslation
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser

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
    def temperature(self):
        return self.settings.get('temperature', 0.0)
    
    @property
    def rate_limit(self):
        return self.settings.get('rate_limit')
    
    @property
    def max_retries(self):
        return self.settings.get('max_retries', 3.0)
    
    @property
    def backoff_time(self):
        return self.settings.get('backoff_time', 5.0)

    def _request_translation(self, prompt, lines, context):
        """
        Generate the prompt and send to OpenAI to request a translation
        """
        gpt_prompt = GPTPrompt(self.instructions)

        gpt_prompt.GenerateMessages(prompt, lines, context)

        logging.debug(f"Messages:\n{FormatMessages(gpt_prompt.messages)}")

        gpt_translation = self._send_messages(gpt_prompt.messages)

        translation = GPTTranslation(gpt_translation, gpt_prompt)

        return translation
    
    def _abort(self):
        self.client.close()
        return super()._abort()

    def GetParser(self):
        return TranslationParser(self.settings)
    
    @classmethod
    def GetAvailableModels(cls, api_key : str, api_base : str):
        """
        Returns a list of possible values for the LLM model 
        """
        try:
            if not hasattr(openai, "OpenAI"):
                raise Exception("The OpenAI library is out of date and must be updated")

            if not api_key:
                logging.debug("No OpenAI API key provided")
                return []

            client = openai.OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            response = client.models.list()

            if not response or not response.data:
                return []

            model_list = [ model.id for model in response.data if model.id.startswith('gpt') and model.id.find('vision') < 0 ]
            
            return sorted(model_list)

        except Exception as e:
            logging.error(f"Unable to retrieve available AI models: {str(e)}")
            return []
