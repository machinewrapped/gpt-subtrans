import importlib
import logging
import pkgutil
from PySubtitle.TranslationClient import TranslationClient

class TranslationProvider:
    """
    Base class for translation service providers.
    """
    def __init__(self, name : str, settings : dict):
        self.name : str = name
        self.settings : dict = settings
        self._available_models : list[str] = []

    @property
    def needs_api_key(self) -> bool:
        """
        Whether the provider requires an API key to be set
        """
        return 'api_key' in self.settings
    
    @property
    def api_key(self) -> str:
        """
        The API key for the provider
        """
        return self.settings.get('api_key')

    @property
    def has_configurable_api_base(self) -> bool:
        """
        Whether the provider allows the API base to be configured
        """
        return 'api_base' in self.settings

    @property
    def api_base(self) -> str:
        """
        The API base URL for the provider
        """
        return self.settings.get('api_base')

    @property
    def available_models(self) -> list[str]:
        """
        list of available models for the provider
        """
        if not self._available_models:
            self._available_models = self._get_available_models()
        
        return self._available_models
    
    @property
    def selected_model(self) -> str:
        """
        The currently selected model for the provider
        """
        return self.settings.get('model')
    
    def GetTranslationClient(self, settings : dict) -> TranslationClient:
        """
        Returns a new instance of the translation client for this provider
        """
        raise NotImplementedError()
    
    def _get_available_models(self) -> list[str]:
        """
        Returns a list of possible model for the provider
        """
        raise NotImplementedError()
    
    @classmethod
    def get_providers(cls) -> dict:
        """
        Return a dictionary of all available providers
        """
        if not cls.__subclasses__():
            try:
                cls.import_providers(f"{__package__}.Providers")

            except Exception as e:
                logging.error(f"Error importing providers: {str(e)}")

        providers = { provider.name : provider for provider in cls.__subclasses__() }

        return providers

    @classmethod
    def create_provider(cls, name : str, settings : dict):
        """
        Create a new instance of the provider with the given name
        """
        for provider_name, provider in cls.get_providers().items():
            if provider_name == name:
                return provider(settings)
        
        raise ValueError(f"Unknown translation provider: {name}")    

    @classmethod
    def import_providers(cls, package_name):
        """
        Dynamically import all modules in the providers package.
        """
        package = importlib.import_module(package_name)
        for loader, module_name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + '.'):
            logging.debug(f"Importing provider: {module_name}")
            importlib.import_module(module_name)

