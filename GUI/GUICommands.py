import logging

from GUI.Command import Command
from PySubtitle.Options import Options
from PySubtitle.TranslationProvider import TranslationProvider
from PySubtitle.Helpers.Localization import _

class ExitProgramCommand(Command):
    """
    Exit the program.
    """
    def __init__(self):
        super().__init__()
        self.is_blocking = True
        self.can_undo = False

    def execute(self):
        logging.info(_("Exiting Program"))

class CheckProviderSettings(Command):
    """
    Check if the translation provider is configured correctly.
    """
    def __init__(self, options : Options):
        super().__init__()
        self.is_blocking = True
        self.skip_undo = True
        self.options = options
        self.show_provider_settings = False

    def execute(self):
        try:
            translation_provider : TranslationProvider = self.datamodel.translation_provider
            if not translation_provider:
                logging.warning(_("Invalid translation provider"))
                self.show_provider_settings = True

            elif not translation_provider.ValidateSettings():
                logging.warning(_("Provider {provider} needs configuring: {message}").format(provider=translation_provider.name, message=translation_provider.validation_message))
                self.show_provider_settings = True

        except Exception as e:
            logging.error(_("CheckProviderSettings: {error}").format(error=e))

        return True

