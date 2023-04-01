import logging
import debugpy
from queue import Queue

from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

class CommandQueue(QObject):
    command_added = pyqtSignal(object)
    command_executed = pyqtSignal(object, bool)

    def __init__(self, datamodel):
        super().__init__()
        self.datamodel = datamodel
        self.undo_stack = []

        self.command_queue = CommandQueueWorker()
        self.command_queue.command_executed.connect(self.on_command_executed)

        self.logger = logging.getLogger("CommandQueue")

    def on_command_executed(self, command, success):
        self.logger.debug(f"A {type(command).__name__} was completed")
        self.undo_stack.append(command)
        self.command_executed.emit(command, success)

    def add_command(self, command, callback=None, undo_callback=None):
        self.logger.debug(f"Adding a {type(command).__name__} command to the queue")
        command.set_callback(callback)
        command.set_undo_callback(undo_callback)

        self.command_queue.add_command(command, self.datamodel)
        self.command_added.emit(command)


class CommandQueueWorker(QThread):
    command_executed = pyqtSignal(object, bool)

    def __init__(self):
        super().__init__()

        self.queue = Queue()

        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.run)
        self.thread.start()

    def add_command(self, command, datamodel):
        self.queue.put((command, datamodel))

    @pyqtSlot()
    def run(self):
        debugpy.debug_this_thread()
        while self.queue:
            command, datamodel = self.queue.get()
            success = command.execute(datamodel)

            self.command_executed.emit(command, success)
