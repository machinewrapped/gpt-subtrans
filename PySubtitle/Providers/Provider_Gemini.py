
import logging
import os

from PySubtitle.Helpers import GetEnvFloat

try:
    import google.generativeai as genai
    from google.api_core.exceptions import FailedPrecondition

    from PySubtitle.Providers.Gemini.GeminiClient import GeminiClient
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationProvider import TranslationProvider

    class GeminiProvider(TranslationProvider):
        name = "Gemini"

        information = """
        <p>Select the <a href="https://ai.google.dev/models/gemini">AI model</a> to use as a translator.</p> 
        <p>Please note that the Gemini API can currently only be accessed from IP addresses in <a href="https://ai.google.dev/available_regions">certain regions</a>.</p>
        <p>You must ensure that the Generative Language API is enabled for your project and/or API key.</p>
        """

        information_noapikey = """
        <p>Please note that the Gemini API can currently only be accessed from IP addresses in <a href="https://ai.google.dev/available_regions">certain regions</a>.</p>
        <p>To use this provider you need to create an API Key <a href="https://aistudio.google.com/app/apikey">Google AI Studio</a>
        or a project on <a href="https://console.cloud.google.com/">Google Cloud Platform</a> and enable Generative Language API access.</p>
        """

        def __init__(self, settings : dict):
            super().__init__(self.name, {
                "api_key": settings.get('api_key') or os.getenv('GEMINI_API_KEY'),
                "model": settings.get('model') or os.getenv('GEMINI_MODEL'),
                'temperature': settings.get('temperature', GetEnvFloat('GEMINI_TEMPERATURE', 0.0)),
                'rate_limit': settings.get('rate_limit', GetEnvFloat('GEMINI_RATE_LIMIT', 0.0))
            })

            self.refresh_when_changed = ['api_key', 'model']
            self.gemini_models = []

        @property
        def api_key(self):
            return self.settings.get('api_key')
        
        def GetTranslationClient(self, settings : dict) -> TranslationClient:
            genai.configure(api_key=self.api_key)
            client_settings = self.settings.copy()
            client_settings.update(settings)
            client_settings['model'] = self._get_true_name(self.selected_model)
            return GeminiClient(client_settings)

        def GetOptions(self) -> dict:
            options = {
                'api_key': (str, "A Google Gemini API key is required to use this provider (https://makersuite.google.com/app/apikey)")
            }
            
            if self.api_key:
                try:
                    models = self.available_models
                    if models:
                        options.update({
                            'model': (models, "AI model to use as the translator" if models else "Unable to retrieve models"),
                            'temperature': (float, "Amount of random variance to add to translations. Generally speaking, none is best"),
                            'rate_limit': (float, "Maximum API requests per minute.")
                        })

                    else:
                        options['model'] = (["Unable to retrieve models"], "Check API key is authorized and try again")

                except FailedPrecondition as e:
                    options['model'] = (["Unable to access the Gemini API"], str(e))
                    
            return options

        def GetAvailableModels(self) -> list[str]:
            if not self.api_key:
                return []
            
            genai.configure(api_key=self.api_key)
            self.gemini_models = self._get_gemini_models()
            
            models = [ m.display_name for m in self.gemini_models if m.display_name.find("Vision") < 0]

            return models or []

        def GetInformation(self) -> str:
            return self.information if self.api_key else self.information_noapikey

        def ValidateSettings(self) -> bool:
            """
            Validate the settings for the provider
            """
            if not self.api_key:
                self.validation_message = "API Key is required"
                return False

            return True

        def _get_gemini_models(self):
            return [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods ]
        
        def _get_true_name(self, display_name : str) -> str:
            if not self.gemini_models:
                self.gemini_models = self._get_gemini_models()

            for m in self.gemini_models:
                if m.display_name == display_name:
                    return m.name
            
            raise ValueError(f"Model {display_name} not found")

except ImportError:
    logging.info("Google Generative AI SDK not installed. Gemini provider will not be available")

