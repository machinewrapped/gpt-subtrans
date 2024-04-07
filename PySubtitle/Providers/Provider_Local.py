
import os
from copy import deepcopy

from PySubtitle.Helpers import GetEnvFloat, GetEnvInteger, GetEnvBool
from PySubtitle.Options import MULTILINE_OPTION
from PySubtitle.TranslationClient import TranslationClient
from PySubtitle.TranslationParser import TranslationParser
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.TranslationProvider import TranslationProvider
from PySubtitle.Providers.Local.LocalClient import LocalClient

class Provider_LocalServer(TranslationProvider):
    name = "Local Server"

    information = """
    <p>This provider allows you to connect to a server running locally (or otherwise accessible) with an OpenAI compatible API, 
    e.g. <a href="https://lmstudio.ai/">LM Studio</a>.</p>
    <p>The AI model to use as a translator should be specified on the server, which should then provide an address and supported endpoints.</p>
    <p>Completion and chat endpoints are supported. For chat endpoints, indicate whether the server supports system messages.</p>
    <p>Note that locally hosted models are likely to be much less capable than the large models hosted in the cloud, and results may be underwhelming.</p>
    """

    def __init__(self, settings : dict):
        super().__init__(self.name, {
            'server_address': settings.get('server_address', os.getenv('LOCAL_SERVER_ADDRESS', "http://localhost:1234")),
            'endpoint': settings.get('endpoint', os.getenv('LOCAL_ENDPOINT', "/v1/chat/completions")),
            'supports_conversation': settings.get('supports_conversation', GetEnvBool('LOCAL_SUPPORTS_CONVERSATION', True)),
            'supports_system_messages': settings.get('supports_system_messages', GetEnvBool('LOCAL_SUPPORTS_SYSTEM_MESSAGES', True)),
            'prompt_template': settings.get('prompt_template', os.getenv('LOCAL_PROMPT_TEMPLATE', TranslationPrompt.default_template)),
            'temperature': settings.get('temperature', GetEnvFloat('LOCAL_TEMPERATURE', 0.0)),
            'max_tokens': settings.get('max_tokens', GetEnvInteger('LOCAL_MAX_TOKENS', 0))
            })
        
        #TODO: Add additional parameters option
        #TODO: Add support for custom prompt format
        #TODO: Add support for custom response parser
        self.refresh_when_changed = ['server_address', 'supports_conversation']
        
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
            'endpoint': (str, "The API function to call on the server"),
            'supports_conversation': (bool, "Attempt to communicate with the endpoint using chat format")
        }

        if self.settings.get('supports_conversation'):
            options['supports_system_messages'] = (bool, "Instructions will be sent as system messages rather than the user prompt")

        options.update({
            'prompt_template': (MULTILINE_OPTION, "Template for the prompt to send to the server (use {prompt} and {context} tags)"),
            'temperature': (float, "Higher temperature introduces more randomness to the translation (default 0.0)"),
            'max_tokens': (int, "The maximum number of tokens the AI should generate in the response (0 for unlimited)")
        })

        return options
