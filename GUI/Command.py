import os
import logging

from PySide6.QtCore import QObject, QRunnable, Slot, Signal

from PySubtitle.Helpers.Localization import _

from GUI.ProjectDataModel import ProjectDataModel
from GUI.ViewModel.ViewModelUpdate import ModelUpdate

if os.environ.get("DEBUG_MODE") == "1":
    try:
        import debugpy # type: ignore
    except ImportError:
        logging.warning("debugpy is not available, breakpoints on worker threads will not work")

class Command(QRunnable, QObject):
    commandStarted = Signal(object)
    commandCompleted = Signal(object)

    def __init__(self, datamodel : ProjectDataModel = None):
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.datamodel = datamodel
        self.can_undo : bool = True         # If true, cannot undo past this command
        self.skip_undo : bool = False       # If true, do not add this command to the undo stack
        self.is_blocking : bool = False      # If true, do not execute any other commands in parallel
        self.queued : bool = False
        self.started : bool = False
        self.executed : bool = False
        self.succeeded : bool = False
        self.aborted : bool = False
        self.terminal : bool = False        # If true, command ended with a fatal error, no further commands can be executed
        self.callback = None
        self.undo_callback = None
        self.model_updates : list[ModelUpdate] = []
        self.commands_to_queue : list[Command] = []

    def SetDataModel(self, datamodel):
        self.datamodel = datamodel

    def SetCallback(self, callback):
        self.callback = callback

    def SetUndoCallback(self, undo_callback):
        self.undo_callback = undo_callback

    def Abort(self):
        if not self.aborted:
            self.aborted = True
            self.queued = False
            self.on_abort()

    def AddModelUpdate(self) -> ModelUpdate:
        update = ModelUpdate()
        self.model_updates.append(update)
        return update

    def ClearModelUpdates(self):
        self.model_updates = []

    @Slot()
    def run(self):
        self.succeeded = None

        if self.aborted:
            logging.debug(f"Aborted {type(self).__name__} before it started")
            self.commandCompleted.emit(self)
            return

        if 'debugpy' in globals():
            debugpy.debug_this_thread()

        try:
            self.started = True
            self.commandStarted.emit(self)

            success = self.execute()

            if self.aborted:
                logging.info(_("Aborted {type}").format(type=type(self).__name__))
            elif self.terminal:
                logging.error(_("Unrecoverable error in {name}").format(name=type(self).__name__))
            else:
                self.succeeded = success

            self.commandCompleted.emit(self)

        except Exception as e:
            logging.error(_("Error executing {type}: {str}").format(type=type(self).__name__, str=e))
            self.commandCompleted.emit(self)

    def execute(self):
        raise NotImplementedError

    def undo(self):
        if self.skip_undo:
            logging.warning(f"Command {type(self).__name__} has no undo function and is not set to skip undo")
            return False

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
    def __init__(self, message : str, command : Command, *args: object) -> None:
        super().__init__(*args)
        self.message = message
        self.command = command

    def __str__(self) -> str:
        return _("Error in {command}: {message}").format(command=type(self.command).__name__, message=self.message)


class UndoError(CommandError):
    pass

