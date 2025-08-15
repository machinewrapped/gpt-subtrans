from PySubtitle.Helpers.Localization import _
from PySubtitle.Providers.Custom.CustomClient import CustomClient

class OpenRouterClient(CustomClient):
    """
    Handles chat communication with OpenRouter to request translations
    """
    def __init__(self, settings : dict):
        settings.setdefault('supports_system_messages', True)
        settings.setdefault('supports_conversation', True)
        settings.setdefault('server_address', 'https://openrouter.ai/api/')
        settings.setdefault('endpoint', '/v1/chat/completions')
        settings.setdefault('additional_headers', {
            'HTTP-Referer': 'https://github.com/machinewrapped/gpt-subtrans',
            'X-Title': 'GPT-Subtrans'
            })
        super().__init__(settings)
