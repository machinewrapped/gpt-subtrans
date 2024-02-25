import os
from PySubtitle.Providers.OpenAI.ChatGPTClient import ChatGPTClient
from PySubtitle.Providers.OpenAI.InstructGPTClient import InstructGPTClient
from PySubtitle.Providers.OpenAI.OpenAIClient import OpenAIClient
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationProvider import TranslationProvider

class OpenAiProvider(TranslationProvider):
    name = "OpenAI"

    def __init__(self, settings : dict):
        super().__init__(self.name, {
            "api_key": settings.get('api_key') or os.getenv('OPENAI_API_KEY'),
            "api_base": settings.get('api_base') or os.getenv('OPENAI_API_BASE'),
            "model": settings.get('model') or os.getenv('OPENAI_MODEL'),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', 0.0)),
            'rate_limit': float(os.getenv('OPENAI_RATE_LIMIT')) if os.getenv('OPENAI_RATE_LIMIT') else None,
            "free_plan": settings.get('free_plan') or os.getenv('OPENAI_FREE_PLAN') == "True",
            'max_instruct_tokens': int(os.getenv('MAX_INSTRUCT_TOKENS', 2048)),
        })

        self.refresh_when_changed = ['api_key', 'api_base', 'model']

    @property
    def api_key(self):
        return self.settings.get('api_key')
    
    @property
    def api_base(self):
        return self.settings.get('api_base')
    
    @property
    def is_instruct_model(self):
        return self.selected_model.find("instruct") >= 0
    
    def GetTranslationClient(self, settings : dict) -> TranslationClient:
        client_settings = self.settings.copy()
        client_settings.update(settings)
        if self.is_instruct_model:
            return InstructGPTClient(client_settings)
        else:
            return ChatGPTClient(client_settings)

    def GetOptions(self) -> dict:
        options = {
            'api_key': (str, "An OpenAI API key is required to use this provider (https://platform.openai.com/account/api-keys)"),
            'api_base': (str, "The base URL to use for requests - leave as default unless you know you need something else"),
        }
        
        if self.api_key:
            models = self.available_models
            if models:
                options.update({
                    'model': (models, "AI model to use as the translator" if models else "Unable to retrieve models"),
                    'temperature': (float, "Amount of random variance to add to translations. Generally speaking, none is best"),
                    'rate_limit': (float, "Maximum OpenAI API requests per minute. Mainly useful if you are on the restricted free plan")
                })

                if self.selected_model and self.selected_model.find("instruct") >= 0:
                    options['max_instruct_tokens'] = (int, "Maximum tokens a completion can contain (only applicable for -instruct models)")

            else:
                options['model'] = (["Unable to retrieve models"], "Check API key and base URL and try again")
            
        return options

    def GetAvailableModels(self) -> list[str]:
        if not self.api_key:
            return []
        
        models = OpenAIClient.GetAvailableModels(self.api_key, self.api_base)
        return models or []
    
    def ValidateSettings(self) -> bool:
        """
        Validate the settings for the provider
        """
        if not self.api_key:
            self.validation_message = "API Key is required"
            return False

        return True
