import os
from PySubtitle.Providers.OpenAI.ChatGPTClient import ChatGPTClient
from PySubtitle.Providers.OpenAI.InstructGPTClient import InstructGPTClient
from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationProvider import TranslationProvider

class OpenAiProvider(TranslationProvider):
    name = "OpenAI"

    def __init__(self, settings : dict):
        #TODO: Eliminate the gpt_model setting
        super().__init__(self.name, {
            "api_key": settings.get('api_key') or os.getenv('OPENAI_API_KEY'),
            "api_base": settings.get('api_base') or os.getenv('OPENAI_API_BASE'),
            "model": settings.get('model') or settings.get('gpt_model') or os.getenv('OPENAI_MODEL'),
            "free_plan": settings.get('free_plan') or os.getenv('OPENAI_FREE_PLAN') == "True",
            'max_instruct_tokens': int(os.getenv('MAX_INSTRUCT_TOKENS', 2048)),
        })

    @property
    def api_key(self):
        return self.settings.get('api_key')
    
    @property
    def api_base(self):
        return self.settings.get('api_base')
    
    def GetTranslationClient(self, options : dict) -> TranslationClient:
        options.update(self.settings)
        is_instruct_model = self.selected_model.find("instruct") >= 0
        return InstructGPTClient(options) if is_instruct_model else ChatGPTClient(options)

    def GetOptions(self) -> dict:
        models = self.available_models
        return {
            'api_key': (str, "API key for the translation service"),
            'api_base': (str, "Base URL for the translation service"),
            'model': (models, "AI model to use as the translator" if models else "Unable to retrieve models"),
            'free_plan': (bool, "Select this if your OpenAI API Key is for a trial version"),
            'max_instruct_tokens': (int, "Maximum number of response tokens instruct models can send")
        }

    def _get_available_models(self) -> list[str]:
        if not self.api_key:
            return "No API key set"
        
        models = OpenAIClient.GetAvailableModels(self.api_key, self.api_base)
        return models or "Unable to retrieve model list"
    
