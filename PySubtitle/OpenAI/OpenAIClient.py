

import logging
import openai
from PySubtitle.Options import Options
from PySubtitle.TranslationClient import TranslationClient

class OpenAIClient(TranslationClient):
    """
    Handles communication with OpenAI to request translations
    """
    def __init__(self, options : Options, instructions=None):
        super().__init__(options, instructions)

        openai.api_key = options.api_key() or openai.api_key

        if not openai.api_key:
            raise ValueError('API key must be set in .env or provided as an argument')
        
        if options.api_base():
            openai.api_base = options.api_base()
        
        logging.debug(f"Using API Key: {openai.api_key}, Using API Base: {openai.api_base}")

    @classmethod
    def GetAvailableModels(cls, api_key : str, api_base : str):
        """
        Returns a list of possible values for the LLM model 
        """
        try:
            if api_base:
                response = openai.Model.list(api_key, api_base = api_base) if api_key else None
            else:
                response = openai.Model.list(api_key) if api_key else None 
            if not response or not response.data:
                return []

            model_list = [ model.openai_id for model in response.data if model.openai_id.startswith('gpt') ]
            
            return sorted(model_list)

        except Exception as e:
            logging.error(f"Unable to retrieve available AI models: {str(e)}")
            return []
