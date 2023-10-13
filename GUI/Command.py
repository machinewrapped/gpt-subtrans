import os
import logging

from PySide6.QtCore import QObject, QRunnable, Slot, Signal

from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectViewModelUpdate import ModelUpdate
from PySubtitle.SubtitleError import TranslationAbortedError

if os.environ.get("DEBUG_MODE") == "1":
    try:
        import debugpy
    except ImportError:
        logging.warn("debugpy is not available, breakpoints on worker threads will not work")

class Command(QRunnable, QObject):
    commandExecuted = Signal(object, bool)

    def __init__(self, datamodel : ProjectDataModel = None):
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.datamodel = datamodel
        self.is_blocking : bool = True
        self.started : bool = False
        self.executed : bool = False
        self.aborted : bool = False
        self.callback = None
        self.undo_callback = None
        self.model_update = ModelUpdate()
        self.commands_to_queue : list = []

    def SetDataModel(self, datamodel):
        self.datamodel = datamodel

    def SetCallback(self, callback):
        self.callback = callback

    def SetUndoCallback(self, undo_callback):
        self.undo_callback = undo_callback

    def Abort(self):
        if not self.aborted:
            self.aborted = True
            self.on_abort()

    @Slot()
    def run(self):
        if self.aborted:
            logging.debug(f"{type(self).__name__} command aborted before it started")
            self.commandExecuted.emit(self, False)
            return

        if 'debugpy' in globals():
            debugpy.debug_this_thread()

        try:
            success = self.execute()

            self.commandExecuted.emit(self, success)

        except TranslationAbortedError:
            logging.info(f"Aborted {type(self).__name__} command")
            self.commandExecuted.emit(self, False)

        except Exception as e:
            logging.error(f"Error executing {type(self).__name__} command ({str(e)})")
            self.commandExecuted.emit(self, False)

    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError
    
    def on_abort(self):
        pass

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

