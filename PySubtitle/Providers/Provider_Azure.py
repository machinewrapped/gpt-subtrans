import logging
import os

try:
    import openai

    from PySubtitle.Providers.Azure.AzureOpenAIClient import AzureOpenAIClient
    from PySubtitle.TranslationClient import TranslationClient
    from PySubtitle.TranslationProvider import TranslationProvider

    class AzureOpenAiProvider(TranslationProvider):
        name = "Azure"

        information = """
        <p>Azure API-provider.</p>
        <p>To use Azure as a provider you need to provide the name and address of an OpenAI Azure deployment, an API version and API Key.</p>
        """

        def __init__(self, settings : dict):
            super().__init__(self.name, {
                "api_key": settings.get('api_key', os.getenv('AZURE_API_KEY')),
                "api_base": settings.get('api_base', os.getenv('AZURE_API_BASE')),
                "api_version": settings.get('api_version', os.getenv('AZURE_API_VERSION')),
                "deployment_name": settings.get('deployment_name', os.getenv('AZURE_DEPLOYMENT_NAME')),
            })

            self.refresh_when_changed = ['api_key', 'api_base', 'api_version', 'deployment_name']

        @property
        def api_key(self):
            return self.settings.get('api_key')

        @property
        def api_base(self):
            return self.settings.get('api_base')

        @property
        def api_version(self):
            return self.settings.get('api_version')

        @property
        def deployment_name(self):
            return self.settings.get('deployment_name')

        def GetTranslationClient(self, settings : dict) -> TranslationClient:
            client_settings = self.settings.copy()
            client_settings.update(settings)
            client_settings.update({
                'supports_conversation': True,
                'supports_system_messages': True
                })
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
            information = self.information
            if not self.ValidateSettings():
                information = information + f"<p>{self.validation_message}</p>"
            return information

        def GetAvailableModels(self) -> list[str]:
            return []

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

        def _allow_multithreaded_translation(self) -> bool:
            """
            Assume the Aazure provider can handle multiple requests
            """
            return True

except ImportError:
    logging.info("OpenAI SDK not installed. Azure provider will not be available")
