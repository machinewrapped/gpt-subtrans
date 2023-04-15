import logging
import debugpy

from PySide6.QtCore import QObject, QRunnable, Slot, Signal

from GUI.ProjectDataModel import ProjectDataModel

class Command(QRunnable, QObject):
    commandExecuted = Signal(object, bool)
    modelUpdated = Signal(object)

    def __init__(self, datamodel : ProjectDataModel = None):
        QRunnable.__init__(self)
        QObject.__init__(self)
        self.datamodel = datamodel
        self.executed : bool = False
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

    @Slot()
    def run(self):
        debugpy.debug_this_thread()

        try:
            success = self.execute()

            self.commandExecuted.emit(self, success)

        except Exception as e:
            logging.error(f"Error executing {type(self).__name__} command ({str(e)})")
            self.commandExecuted.emit(self, False)

    def execute(self):
        raise NotImplementedError

    def undo(self):
        raise NotImplementedError

    def execute_callback(self):
        if self.callback:
            self.callback(self)

    def execute_undo_callback(self):
        if self.undo_callback:
            self.undo_callback(self)

