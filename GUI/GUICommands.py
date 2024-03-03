import logging

from GUI.Command import Command
from PySubtitle.Options import Options
from PySubtitle.TranslationProvider import TranslationProvider

class ExitProgramCommand(Command):
    """
    Exit the program.
    """
    def __init__(self):
        super().__init__()
        self.is_blocking = True

    def execute(self):
        logging.info("Exiting Program")

class CheckProviderSettings(Command):
    """
    Check if the translation provider is configured correctly.
    """
    def __init__(self, options : Options):
        super().__init__()
        self.is_blocking = True
        self.options = options

    def execute(self):
        try:
            translation_provider : TranslationProvider = TranslationProvider.get_provider(self.options)
            if not translation_provider or not translation_provider.ValidateSettings():
                self.datamodel.PerformModelAction('Show Provider Settings', {})
        except Exception as e:
            logging.error(f"CheckProviderSettings: {e}")

        return True
