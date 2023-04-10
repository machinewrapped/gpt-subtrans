from PySide6.QtCore import QRunnable, Slot

class Command(QRunnable):

    def __init__(self, datamodel = None):
        self.datamodel = datamodel
        self.executed : bool = False
        self.callback = None
        self.undo_callback = None
        self.commands_to_queue : list = []

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

