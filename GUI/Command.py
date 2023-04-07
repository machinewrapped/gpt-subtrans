from PySide6.QtCore import QRunnable, Slot

from GUI.ProjectDataModel import ProjectDataModel

class Command(QRunnable):
    datamodel : ProjectDataModel = None
    executed : bool = False
    callback = None
    undo_callback = None
    commands_to_queue : list = []

    def __init__(self, datamodel = None):
        self.datamodel = datamodel

    def SetDataModel(self, datamodel):
        self.datamodel = datamodel

    def SetCallback(self, callback):
        self.callback = callback

    def SetUndoCallback(self, undo_callback):
        self.undo_callback = undo_callback

    @Slot()
    def run(self):
        self.execute()

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

