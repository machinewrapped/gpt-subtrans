
import os
from copy import deepcopy

from PySubtitle.Helpers import GetEnvFloat
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationProvider import TranslationProvider
from PySubtitle.Providers.Local.LocalClient import LocalClient

class Provider_LocalServer(TranslationProvider):
    name = "Local Server"

    information = """
    <p>Connect to a local LLM server with an OpenAI compatible API.</p>
    """

    def __init__(self, settings : dict):
        super().__init__(self.name, {
            "server_address": settings.get('server_address') or os.getenv('LOCAL_SERVER_ADDRESS', "http://localhost:1234"),
            "endpoint": "/v1/chat/completions",
            "supports_conversation": True,
            "supports_system_messages": True,
            'temperature': settings.get('temperature', GetEnvFloat('LOCAL_TEMPERATURE', 0.0)),
            'max_tokens': settings.get('max_tokens', GetEnvFloat('LOCAL_MAX_TOKENS', 2048))
            })
        
        #TODO: Add additional parameters option
        #TODO: Add support for custom prompt format
        #TODO: Add support for custom response parser
        self.refresh_when_changed = ['server_address']
        
    def GetTranslationClient(self, settings : dict) -> TranslationClient:
        client_settings : dict = deepcopy(self.settings)
        client_settings.update(settings)
        return LocalClient(client_settings)
    
    def GetAvailableModels(self) -> list[str]:
        # Choose the model on the server
        return []
    
    def GetParser(self):
        return TranslationParser(self.settings)
    
    def GetInformation(self):
        return self.information
    
    def GetOptions(self) -> dict:
        options = {
            'server_address': (str, "The address of the local server"),
            'endpoint': (str, "The endpoint to use on the server"),
            'supports_conversation': (bool, "Specify whether the server supports chat format requests (default true)"),
            'supports_system_messages': (bool, "Specify whether the server supports system messages (default true)"),
            'temperature': (float, "Higher temperature introduces more randomness to the translation (default 0.0)"),
            'max_tokens': (int, "The maximum number of tokens the AI should generate")
        }

        return options
