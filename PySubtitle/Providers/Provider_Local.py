
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

    information_invalid = """
    <p>This provider allows you to connect to a server running locally (or otherwise accessible) with an OpenAI compatible API, 
    e.g. <a href="https://lmstudio.ai/">LM Studio</a>.</p>
    <p><b>Server address and endpoint must be provided.</b></p>
    """

    def __init__(self, settings : dict):
        super().__init__(self.name, {
            'server_address': settings.get('server_address', os.getenv('LOCAL_SERVER_ADDRESS', "http://localhost:1234")),
            'endpoint': settings.get('endpoint', os.getenv('LOCAL_ENDPOINT', "/v1/chat/completions")),
            'supports_conversation': settings.get('supports_conversation', GetEnvBool('LOCAL_SUPPORTS_CONVERSATION', True)),
            'supports_system_messages': settings.get('supports_system_messages', GetEnvBool('LOCAL_SUPPORTS_SYSTEM_MESSAGES', True)),
            'prompt_template': settings.get('prompt_template', os.getenv('LOCAL_PROMPT_TEMPLATE', TranslationPrompt.default_template)),
            'temperature': settings.get('temperature', GetEnvFloat('LOCAL_TEMPERATURE', 0.0)),
            'max_tokens': settings.get('max_tokens', GetEnvInteger('LOCAL_MAX_TOKENS', 0)),
            "api_key": settings.get('api_key', os.getenv('LOCAL_API_KEY')),
            "model": settings.get('model', os.getenv('LOCAL_MODEL'))
            })
        
        #TODO: Add additional parameters option
        #TODO: Add support for custom response parser
        self.refresh_when_changed = ['server_address', 'supports_conversation']
    
    @property
    def server_address(self):
        return self.settings.get('server_address')
    
    @property
    def endpoint(self):
        return self.settings.get('endpoint')
    
    @property
    def api_key(self):
        return self.settings.get('api_key')
    
    @property
    def supports_conversation(self):
        return self.settings.get('supports_conversation', False)
    
    @property
    def supports_system_messages(self):
        return self.settings.get('supports_system_messages', False)
    
    @property
    def prompt_template(self):
        return self.settings.get('prompt_template')
    
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
        if self.ValidateSettings():
            return self.information
        else:
            return self.information_invalid
    
    def GetOptions(self) -> dict:
        options = {
            'server_address': (str, "The address of the local server"),
            'endpoint': (str, "The API function to call on the server"),
        }

        if self.ValidateSettings():
            options['supports_conversation'] = (bool, "Attempt to communicate with the endpoint using chat format")

            if self.settings.get('supports_conversation'):
                options['supports_system_messages'] = (bool, "Instructions will be sent as system messages rather than the user prompt")

            options.update({
                'prompt_template': (MULTILINE_OPTION, "Template for the prompt to send to the server (use {prompt} and {context} tags)"),
                'temperature': (float, "Higher temperature introduces more randomness to the translation (default 0.0)"),
                'max_tokens': (int, "The maximum number of tokens the AI should generate in the response (0 for unlimited)"),
                'api_key': (str, "An API key is normally not needed for a local server"),
                'model': (str, "The model is normally set by the server, and should not need to be specified here")
            })

        return options
    
    def ValidateSettings(self) -> bool:
        """
        Validate the settings for the provider
        """
        if not self.server_address:
            self.validation_message = "Server address must be provided"
            return False
        
        if not self.endpoint:
            self.validation_message = "Endpoint must be provided"
            return False
        
        return True

