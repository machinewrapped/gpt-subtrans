import logging
logging.basicConfig(encoding='utf-8')
from GUI.Command import Command

class ExitProgramCommand(Command):
    """
    Exit the program.
    """
    def __init__(self):
        super().__init__()
        self.is_blocking = True

    def execute(self):
        logging.info("Exiting Program")

