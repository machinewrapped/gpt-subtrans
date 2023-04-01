from PySide6.QtCore import QRunnable, Slot

class Command(QRunnable):
    def __init__(self):
        self.callback = None
        self.undo_callback = None
        self.executed = False

    def set_callback(self, callback):
        self.callback = callback

    def set_undo_callback(self, undo_callback):
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

