import importlib.util
import logging

from PySubtitle.Helpers.Localization import _
from PySubtitle.Helpers.Settings import *
from PySubtitle.Options import SettingsType, GuiOptionsType

if not importlib.util.find_spec("anthropic"):
    logging.info(_("Anthropic SDK is not installed. Claude provider will not be available"))
else:
    try:
        import anthropic
        import os

        from copy import deepcopy

        from PySubtitle.Helpers import GetEnvFloat, GetEnvInteger
        from PySubtitle.Helpers.Localization import _
        from PySubtitle.Helpers.Parse import ParseNames
        from PySubtitle.Providers.Anthropic.AnthropicClient import AnthropicClient
        from PySubtitle.TranslationClient import TranslationClient
        from PySubtitle.TranslationProvider import TranslationProvider

        class Provider_Claude(TranslationProvider):
            name = "Claude"

            information = """
            <p>Select the <a href="https://docs.anthropic.com/claude/docs/models-overview">AI model</a> to use as a translator.</p>
            <p>Note that each model has a <a href="https://docs.anthropic.com/claude/docs/models-overview">maximum tokens limit</a>.</p>
            <p>See the <a href="https://docs.anthropic.com/claude/reference/rate-limits">Anthropic documentation</a> for information on rate limits and costs</p>
            """

            information_noapikey = """
            <p>To use Claude you need to provide an <a href="https://console.anthropic.com/settings/keys">Anthropic API Key </a>.</p>
            """

            default_model = "claude-3-5-haiku-latest"

            def __init__(self, settings : Options|SettingsType):
                super().__init__(self.name, {
                    "api_key": GetStrSetting(settings, 'api_key') or os.getenv('CLAUDE_API_KEY'),
                    "model": GetStrSetting(settings, 'model') or os.getenv('CLAUDE_MODEL', self.default_model),
                    "thinking": GetBoolSetting(settings, 'thinking', False),
                    "max_tokens": GetIntSetting(settings, 'max_tokens') or GetEnvInteger('CLAUDE_MAX_TOKENS', 4096),
                    "max_thinking_tokens": GetIntSetting(settings, 'max_thinking_tokens') or GetEnvInteger('CLAUDE_MAX_THINKING_TOKENS', 1024),
                    'temperature': GetFloatSetting(settings, 'temperature', GetEnvFloat('CLAUDE_TEMPERATURE', 0.0)),
                    'rate_limit': GetFloatSetting(settings, 'rate_limit', GetEnvFloat('CLAUDE_RATE_LIMIT', 10.0)),
                    'proxy': GetStrSetting(settings, 'proxy') or os.getenv('CLAUDE_PROXY'),
                })

                self.refresh_when_changed = ['api_key', 'model', 'thinking']

                self.claude_models = []

            @property
            def api_key(self) -> str|None:
                return GetStrSetting(self.settings, 'api_key')
            
            @property
            def allow_thinking(self) -> bool:
                return GetBoolSetting(self.settings, 'thinking', False)
            
            @property
            def max_tokens(self) -> int:
                return GetIntSetting(self.settings, 'max_tokens') or 8192
            
            @property
            def max_thinking_tokens(self) -> int:
                return GetIntSetting(self.settings, 'max_thinking_tokens') or 1024

            def GetTranslationClient(self, settings : SettingsType) -> TranslationClient:
                client_settings : dict = deepcopy(self.settings)
                client_settings.update(settings)
                client_settings.update({
                    'model': self._get_model_id(self.selected_model) if self.selected_model else None,
                    'supports_conversation': True,
                    'supports_system_messages': False,
                    'supports_system_prompt': True
                    })
                return AnthropicClient(client_settings)

            def GetAvailableModels(self) -> list[str]:
                if not self.api_key:
                    return []
                
                if not self.claude_models:
                    self.claude_models = self._get_claude_models()

                models = [model.display_name for model in self.claude_models]

                return models

            def RefreshAvailableModels(self):
                self._available_models = self.GetAvailableModels()

            def GetInformation(self):
                return self.information if self.api_key else self.information_noapikey

            def GetOptions(self) -> GuiOptionsType:
                options : GuiOptionsType = {
                    'api_key': (str, _("An Anthropic Claude API key is required to use this provider (https://console.anthropic.com/settings/keys)"))
                    }

                if not self.api_key:
                    return options

                self.RefreshAvailableModels()

                if self.available_models:
                    options.update({
                        'model': (self.available_models, _("The model to use for translations")),
                        'temperature': (float, _("The temperature to use for translations (default 0.0)")),
                        'rate_limit': (float, _("The rate limit to use for translations (default 60.0)")),
                        'max_tokens': (int, _("The maximum number of tokens to use for translations")),
                        'thinking': (bool, _("Enable thinking mode for translations")),
                    })

                if self.allow_thinking:
                    options['max_thinking_tokens'] = (int, _("The maximum number of tokens to use for thinking"))

                options['proxy'] = (str, _("Optional proxy server to use for requests (e.g. https://api.not-anthropic.com/"))
                return options

            def _allow_multithreaded_translation(self) -> bool:
                """
                If user has set a rate limit don't attempt parallel requests to make sure we respect it
                """
                if GetFloatSetting(self.settings, 'rate_limit', 0.0) != 0.0:
                    return False

                return True

            def _get_claude_models(self):
                if not self.api_key:
                    return []

                try:
                    client = anthropic.Anthropic(api_key=self.api_key)
                    model_list = client.models.list()

                    return [ m for m in model_list if m.type == 'model' ]

                except Exception as e:
                    logging.error(_("Unable to retrieve Claude model list: {error}").format(
                        error=str(e)
                    ))
                    return []

            def _get_model_id(self, name : str) -> str:
                if not self.claude_models:
                    self.claude_models = self._get_claude_models()

                for m in self.claude_models:
                    if m.id == name or m.display_name == name:
                        return m.id

                raise ValueError(f"Model {name} not found")

    except ImportError:
        logging.info(_("Unable to initialise Anthropic SDK. Claude provider will not be available"))
