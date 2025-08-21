import json
import logging
import os
import httpx

from PySubtitle.Helpers import GetEnvFloat
from PySubtitle.Helpers.Localization import _
from PySubtitle.Options import SettingsType, GuiOptionsType
from PySubtitle.Providers.Custom.DeepSeekClient import DeepSeekClient
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
        provider_settings = {
            "api_key": settings.get('api_key', os.getenv('DEEPSEEK_API_KEY')),
            "api_base": settings.get('api_base', os.getenv('DEEPSEEK_API_BASE', "https://api.deepseek.com")),
            "model": settings.get('model', os.getenv('DEEPSEEK_MODEL', "deepseek-chat")),
            'max_tokens': settings.get('max_tokens', os.getenv('DEEPSEEK_MAX_TOKENS', 8192)),
            'temperature': settings.get('temperature', GetEnvFloat('DEEPSEEK_TEMPERATURE', 1.3)),
            'rate_limit': settings.get('rate_limit', GetEnvFloat('DEEPSEEK_RATE_LIMIT')),
            'reuse_client': settings.get('reuse_client', False),
            'endpoint': settings.get('endpoint', '/v1/chat/completions'),
        }
        super().__init__(self.name, provider_settings)
        self.refresh_when_changed = ['api_key', 'api_base', 'model', 'endpoint']

    @property
    def api_key(self):
        return self.settings.get('api_key')

    @property
    def api_base(self):
        return self.settings.get('api_base')
    
    @property
    def server_address(self):
        return self.api_base

    def GetTranslationClient(self, settings : SettingsType) -> TranslationClient:
        client_settings = self.settings.copy()
        client_settings.update(settings)
        return DeepSeekClient(client_settings)

    def GetOptions(self) -> GuiOptionsType:
        options = {
            'api_key': (str, _("A DeepSeek API key is required to use this provider (https://platform.deepseek.com/api_keys)")),
            'api_base': (str, _("The base URL to use for requests (default is https://api.deepseek.com)")),
        }

        if self.api_key:
            models = self.available_models
            if models:
                options.update({
                    'model': (models, _("AI model to use as the translator")),
                    'reuse_client': (bool, _("Reuse connection for multiple requests (otherwise a new connection is established for each)")),
                    'max_tokens': (int, _("Maximum number of output tokens to return in the response.")),
                    'temperature': (float, _("Amount of random variance to add to translations. Generally speaking, none is best")),
                    'rate_limit': (float, _("Maximum API requests per minute."))
                })
            else:
                options['model'] = (["Unable to retrieve models"], _("Check API key and base URL and try again"))

        return options

    def GetAvailableModels(self) -> list[str]:
        """
        Fetch available models from DeepSeek API
        """
        if not self.api_key:
            logging.debug("No DeepSeek API key provided")
            return []

        try:
            url = self.server_address.rstrip('/') + '/v1/models'
            headers = {'Authorization': f"Bearer {self.api_key}"} if self.api_key else {}

            with httpx.Client(timeout=15) as client:
                result = client.get(url, headers=headers)
                if result.is_error:
                    logging.error(_("Error fetching models: {status} {text}").format(
                        status=result.status_code, text=result.text))
                    return []

                try:
                    data = result.json()
                    models = [m['id'] for m in data.get('data', [])]
                    return sorted(models)
                except json.JSONDecodeError:
                    logging.error(_("Unable to parse server response as JSON: {response_text}").format(response_text=result.text))
                    return []

        except Exception as e:
            logging.error(_("Unable to retrieve available models: {error}").format(error=str(e)))
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
            self.validation_message = _("API Key is required")
            return False

        return True

    def _allow_multithreaded_translation(self) -> bool:
        """
        If user has set a rate limit we can't make multiple requests at once
        """
        if self.settings.get('rate_limit', 0.0) != 0.0:
            return False

        return True

