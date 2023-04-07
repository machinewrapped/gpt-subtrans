from PySide6.QtCore import QRunnable, Slot

class Command(QRunnable):
    def __init__(self):
        self.callback = None
        self.undo_callback = None
        self.executed = False

    def SetCallback(self, callback):
        self.callback = callback

    def SetUndoCallback(self, undo_callback):
        self.undo_callback = undo_callback

    @Slot()
    def run(self):
        self.Execute()

    def Execute(self):
        raise NotImplementedError

    def Undo(self):
        raise NotImplementedError

    def execute_callback(self):
        if self.callback:
            self.callback(self)

    def execute_undo_callback(self):
        if self.undo_callback:
            self.undo_callback(self)

