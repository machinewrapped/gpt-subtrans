import importlib
import logging
import pkgutil
from PySubtitle.Options import Options
from PySubtitle.TranslationClient import TranslationClient

class TranslationProvider:
    """
    Base class for translation service providers.
    """
    def __init__(self, name : str, settings : dict):
        self.name : str = name
        self.settings : dict = settings
        self._available_models : list[str] = []
        self.refresh_when_changed = []
        self.validation_message = None

    @property
    def available_models(self) -> list[str]:
        """
        list of available models for the provider
        """
        if not self._available_models:
            self._available_models = self.GetAvailableModels()
        
        return self._available_models
    
    @property
    def selected_model(self) -> str:
        """
        The currently selected model for the provider
        """
        return self.settings.get('model')
    
    def GetAvailableModels(self) -> list[str]:
        """
        Returns a list of possible model for the provider
        """
        raise NotImplementedError()
    
    def GetInformation(self) -> str:
        """
        Returns information about the provider settings
        """
        return None

    def GetTranslationClient(self, settings : dict) -> TranslationClient:
        """
        Returns a new instance of the translation client for this provider
        """
        raise NotImplementedError()
    
    def ValidateSettings(self) -> bool:
        """
        Validate the settings for the provider
        """
        return True
    
    def UpdateSettings(self, settings : dict | Options):
        """
        Update the settings for the provider
        """
        if isinstance(settings, Options):
            settings.InitialiseProviderSettings(self.name, self.settings)
            settings = settings.provider_settings.get(self.name, {})

        # Update the settings
        for k, v in settings.items():
            if k in self.settings:
                self.settings[k] = v
    
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
    def get_provider(cls, options : Options):
        """
        Create a new instance of the provider with the given name
        """
        if not isinstance(options, Options):
            raise ValueError("Options object required")

        if not options.provider:
            raise ValueError("No provider set")

        provider_settings = options.current_provider_settings

        translation_provider : TranslationProvider = cls.create_provider(options.provider, provider_settings)
        if not translation_provider:
            raise ValueError(f"Unable to create translation provider '{options.provider}'")

        translation_provider.UpdateSettings(options)

        return translation_provider

    @classmethod
    def create_provider(cls, name, provider_settings):
        for provider_name, provider in cls.get_providers().items():
            if provider_name == name:
                return provider(provider_settings)
        
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
    
    @classmethod
    def get_available_models(cls, options : Options):
        """ Get the available models for the selected provider """
        if not isinstance(options, Options):
            raise ValueError("Options object required")

        if not options.provider:
            return []

        provider_class = cls.get_provider(options)
        if not provider_class:
            return []

        return provider_class.available_models