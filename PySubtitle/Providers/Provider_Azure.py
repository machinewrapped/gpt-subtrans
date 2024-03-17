import logging
import os

try:
    from PySubtitle.Providers.Azure.AzureOpenAIClient import AzureOpenAIClient
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationProvider import TranslationProvider

    class AzureOpenAiProvider(TranslationProvider):
        name = "Azure"

        information = """
        <p>Azure API-provider.</p>
        """

        information_noapikey = """<p>You need an Azure API key/p>"""

        def __init__(self, settings : dict):
            super().__init__(self.name, {
                "api_key": settings.get('api_key', os.getenv('AZURE_API_KEY')),
                "api_base": settings.get('api_base', os.getenv('AZURE_API_BASE')),
                "api_version": settings.get('api_version', os.getenv('AZURE_API_VERSION')),
                "deployment_name": settings.get('deployment_name', os.getenv('AZURE_DEPLOYMENT_NAME')),
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
            return AzureOpenAIClient(client_settings)

        def GetOptions(self) -> dict:
            options = {
                'api_key': (str, "An Azure API key is required"),
                'api_version': (str, "An Azure API version is required"),
                'deployment_name': (str, "An Azure API deployment name is required"),
                'api_base': (str, "The Azure API base URL to use for requests."),
            }

            return options

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

            if not self.api_version:
                self.validation_message = "Azure API version is required"
                return False

            if not self.deployment_name:
                self.validation_message = "Azure deployment name is required"
                return False

            if not self.api_base:
                self.validation_message = "Azure API base is required"
                return False

            return True

except ImportError:
    logging.info("OpenAI SDK not installed. Azure provider will not be available")