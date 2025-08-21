from typing import Any
from PySubtitle.Helpers.Localization import _
from PySubtitle.Providers.Custom.CustomClient import CustomClient

class OpenRouterClient(CustomClient):
    """
    Handles chat communication with OpenRouter to request translations
    """
    def __init__(self, settings: dict[str, Any]):
        settings.setdefault('supports_system_messages', True)
        settings.setdefault('supports_conversation', True)
        settings.setdefault('server_address', 'https://openrouter.ai/api/')
        settings.setdefault('endpoint', '/v1/chat/completions')
        settings.setdefault('additional_headers', {
            'HTTP-Referer': 'https://github.com/machinewrapped/llm-subtrans',
            'X-Title': 'LLM-Subtrans'
            })
        super().__init__(settings)
