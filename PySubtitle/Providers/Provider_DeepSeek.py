import logging
import os

from PySubtitle.Helpers import GetEnvFloat
from PySubtitle.SubtitleError import ProviderError

try:
    # We use the OpenAI client to access DeepSeek, as the API is compatible
    import openai

    from PySubtitle.Providers.OpenAI.DeepSeekClient import DeepSeekClient
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationProvider import TranslationProvider


    class DeepSeekProvider(TranslationProvider):
        name = "DeepSeek"

        information = """
        <p>Select the <a href="https://api-docs.deepseek.com/quick_start/pricing">model</a> to use as a translator.</p>
        <p>Not that reasoning models are not generally recommended as translators.</p>
        """

        information_noapikey = """
        <p>To use this provider you need <a href="https://platform.deepseek.com/api_keys">a DeepSeek API key</a>.</p>
        <p>Note that you must have credit to use DeepSeek, there is no free usage tier.</p>
        """

        def __init__(self, settings : dict):
            super().__init__(self.name, {
                "api_key": settings.get('api_key', os.getenv('DEEPSEEK_API_KEY')),
                "api_base": settings.get('api_base', os.getenv('DEEPSEEK_API_BASE', "https://api.deepseek.com")),
                "model": settings.get('model', os.getenv('DEEPSEEK_MODEL', "deepseek-chat")),
                'max_tokens': settings.get('max_tokens', os.getenv('DEEPSEEK_MAX_TOKENS', 8192)),
                'temperature': settings.get('temperature', GetEnvFloat('DEEPSEEK_TEMPERATURE', 1.3)),
                'rate_limit': settings.get('rate_limit', GetEnvFloat('DEEPSEEK_RATE_LIMIT')),
                'reuse_client': settings.get('reuse_client', False)
            })

            self.refresh_when_changed = ['api_key', 'api_base', 'model']

        @property
        def api_key(self):
            return self.settings.get('api_key')

        @property
        def api_base(self):
            return self.settings.get('api_base')

        def GetTranslationClient(self, settings : dict) -> TranslationClient:
            client_settings = self.settings.copy()
            client_settings.update(settings)
            return DeepSeekClient(client_settings)

        def GetOptions(self) -> dict:
            options = {
                'api_key': (str, "A DeepSeek API key is required to use this provider (https://platform.deepseek.com/api_keys)"),
                'api_base': (str, "The base URL to use for requests (default is https://api.deepseek.com)"),
            }

            if self.api_key:
                models = self.available_models
                if models:
                    options.update({
                        'model': (models, "AI model to use as the translator"),
                        'reuse_client': (bool, "Reuse connection for multiple requests (otherwise a new connection is established for each)"),
                        'max_tokens': (int, "Maximum number of output tokens to return in the response."),
                        'temperature': (float, "Amount of random variance to add to translations. Generally speaking, none is best"),
                        'rate_limit': (float, "Maximum API requests per minute.")
                    })

                else:
                    options['model'] = (["Unable to retrieve models"], "Check API key and base URL and try again")

            return options

        def GetAvailableModels(self) -> list[str]:
            """
            Returns a list of possible values for the model
            """
            try:
                if not hasattr(openai, "OpenAI"):
                    raise ProviderError("The OpenAI library is out of date and must be updated", provider=self)

                if not self.api_key:
                    logging.debug("No DeepSeek API key provided")
                    return []

                client = openai.OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base or None
                )
                response = client.models.list()

                if not response or not response.data:
                    return []

                model_list = [ model.id for model in response.data]

                return sorted(model_list)

            except Exception as e:
                logging.error(f"Unable to retrieve available AI models: {str(e)}")
                return []

        def GetInformation(self) -> str:
            if not self.api_key:
                return self.information_noapikey
            return self.information

        def ValidateSettings(self) -> bool:
            """
            Validate the settings for the provider
            """
            if not self.api_key:
                self.validation_message = "API Key is required"
                return False

            return True

        def _allow_multithreaded_translation(self) -> bool:
            """
            If user has set a rate limit we can't make multiple requests at once
            """
            if self.settings.get('rate_limit', 0.0) != 0.0:
                return False

            return True

except ImportError:
    logging.info("OpenAI SDK not installed. DeepSeek provider will not be available")