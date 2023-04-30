import os
import logging

from PySide6.QtCore import QObject, QRunnable, QEventLoop, Slot, Signal

from GUI.ProjectDataModel import ProjectDataModel
from PySubtitleGPT.SubtitleError import TranslationAbortedError

if os.environ.get("DEBUG_MODE") == "1":
    try:
        import debugpy
    except ImportError:
        logging.warn("debugpy is not available, breakpoints on worker threads will not work")

class Command(QRunnable, QObject):
    commandExecuted = Signal(object, bool)
    abort = Signal()

    def __init__(self, datamodel : ProjectDataModel = None):
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.datamodel = datamodel
        self.executed : bool = False
        self.aborted : bool = False
        self.callback = None
        self.undo_callback = None
        self.datamodel_update = {}
        self.commands_to_queue : list = []

    def SetDataModel(self, datamodel):
        self.datamodel = datamodel

    def SetCallback(self, callback):
        self.callback = callback

    def SetUndoCallback(self, undo_callback):
        self.undo_callback = undo_callback

    def Abort(self):
        self.aborted = True
        self.abort.emit()

    @Slot()
    def run(self):
        if not self.aborted:
            if 'debugpy' in globals():
                debugpy.debug_this_thread()

            self.abort.connect(self.on_abort)

            # Create a QEventLoop to process the abort signal
            loop = QEventLoop()

            # Connect the abort signal to the loop's quit slot
            self.abort.connect(loop.quit)

            try:
                success = self.execute()

                self.commandExecuted.emit(self, success)

                loop.exec()

            except TranslationAbortedError:
                logging.debug(f"Aborted {type(self).__name__} command")
                self.commandExecuted.emit(self, False)

            except Exception as e:
                logging.error(f"Error executing {type(self).__name__} command ({str(e)})")
                self.commandExecuted.emit(self, False)

    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError
    
    def on_abort(self):
        self.aborted = True

    def execute_callback(self):
        if self.callback:
            self.callback(self)

    def execute_undo_callback(self):
        if self.undo_callback:
            self.undo_callback(self)

class CommandError(Exception):
    def __init__(self, command : Command, *args: object) -> None:
        super().__init__(*args)
        self.command = command

