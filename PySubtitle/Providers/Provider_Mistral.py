import importlib.util
import logging
import os

if not importlib.util.find_spec("mistralai"):
    logging.info("Mistral SDK is not installed. Mistral provider will not be available")
else:
    try:
        import mistralai

        from PySubtitle.Helpers import GetEnvFloat
        from PySubtitle.Providers.Mistral.MistralClient import MistralClient
        from PySubtitle.TranslationClient import TranslationClient
        from PySubtitle.TranslationProvider import TranslationProvider

        class MistralProvider(TranslationProvider):
            name = "Mistral"

            information = """
            <p>Select the <a href="https://docs.mistral.ai/getting-started/models/models_overview/">model</a> to use as a translator.</p>
            """

            information_noapikey = """
            <p>To use this provider you need <a href="https://console.mistral.ai/api-keys/">a Mistral API key</a>.</p>
            <p>Note that Mistral provide many specialised models that are unlikely to be useful as translators.</p>
            """

            def __init__(self, settings : dict):
                super().__init__(self.name, {
                    "api_key": settings.get('api_key', os.getenv('MISTRAL_API_KEY')),
                    "server_url": settings.get('server_url', os.getenv('MISTRAL_SERVER_URL')),
                    "model": settings.get('model', os.getenv('MISTRAL_MODEL', "open-mistral-nemo")),
                    'temperature': settings.get('temperature', GetEnvFloat('MISTRAL_TEMPERATURE', 0.0)),
                    'rate_limit': settings.get('rate_limit', GetEnvFloat('MISTRAL_RATE_LIMIT')),
                })

                self.refresh_when_changed = ['api_key', 'server_url', 'model']

            @property
            def api_key(self):
                return self.settings.get('api_key')

            @property
            def server_url(self):
                return self.settings.get('server_url')

            def GetTranslationClient(self, settings : dict) -> TranslationClient:
                client_settings = self.settings.copy()
                client_settings.update(settings)
                client_settings.update({
                    'supports_conversation': True,
                    'supports_system_messages': True,
                    'supports_system_messages_for_retry': False,
                    'supports_system_prompt': False
                    })
                return MistralClient(client_settings)

            def GetOptions(self) -> dict:
                options = {
                    'api_key': (str, "A Mistral API key is required to use this provider (https://console.mistral.ai/api-keys/)"),
                    'server_url': (str, "The base URL to use for requests (default is https://api.mistral.ai)"),
                }

                if self.api_key:
                    models = self.available_models
                    if models:
                        options.update({
                            'model': (models, "AI model to use as the translator"),
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
                    if not self.api_key:
                        logging.debug("No Mistral API key provided")
                        return []

                    client = mistralai.Mistral(
                        api_key=self.api_key,
                        server_url=self.server_url or None
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
        logging.info("Mistral SDK not installed. Mistral provider will not be available")