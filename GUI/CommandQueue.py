import logging
import threading
import debugpy
from queue import Queue

from PySide6.QtCore import QThread, QObject, Signal, Slot

from GUI.Command import Command

class CommandQueue(QObject):
    """
    Execute commands on a background thread
    """
    commandAdded = Signal(object)
    commandExecuted = Signal(object, bool)

    def __init__(self, datamodel):
        super().__init__()
        self.datamodel = datamodel
        self.undo_stack = []

        self.command_queue = CommandQueueWorker()
        self.command_queue.command_executed.connect(self._on_command_executed)
        self.mutex = threading.Lock()

        self.logger = logging.getLogger("CommandQueue")

    def Stop(self):
        """
        Shut the background thread down
        """
        if self.command_queue:
            self.command_queue.Shutdown()

    def AddCommand(self, command, callback=None, undo_callback=None):
        """
        Add a command to the command queue, with option callbacks for completion/undo events
        """
        if command:
            self.logger.debug(f"Adding a {type(command).__name__} command to the queue")
            with self.mutex:
                self._queue_command(command, callback, undo_callback)
            self.commandAdded.emit(command)

    def _on_command_executed(self, command, success):
        """
        Handle command callbacks, and queuing further actions 
        """
        self.logger.debug(f"A {type(command).__name__} was completed")
        self.undo_stack.append(command)

        if self.datamodel.commands_to_queue:
            with self.mutex:
                commands = [ cmd for cmd in self.datamodel.commands_to_queue if cmd ]
                self.datamodel.commands_to_queue = []

                for command in commands:
                    self._queue_command(command)

            for command in commands:
                self.logger.debug(f"Added a {type(command).__name__} command to the queue")
                self.commandAdded.emit(command)

        self.commandExecuted.emit(command, success)

    def _queue_command(self, command, callback=None, undo_callback=None):
        command.set_callback(callback)
        command.set_undo_callback(undo_callback)

        self.command_queue.AddCommand(command, self.datamodel)

class CommandQueueWorker(QThread):
    command_executed = Signal(object, bool)

    class StopThread(Command):
        def execute(self, _):
            raise CommandQueueWorker.StopThreadException()

    def __init__(self):
        super().__init__()

        self.queue = Queue()

        self.moveToThread(self)
        self.started.connect(self.run)
        self.start()

    def AddCommand(self, command, datamodel):
        self.queue.put((command, datamodel))

    def Shutdown(self):
        self.AddCommand(CommandQueueWorker.StopThread(), None)
        self.wait(500)

    @Slot()
    def run(self):
        debugpy.debug_this_thread()
        while self.queue:
            command, datamodel = self.queue.get()
            try:
                if isinstance(command, CommandQueueWorker.StopThread):
                    self.exit()
                    break

                success = command.execute(datamodel)

                self.command_executed.emit(command, success)

            except Exception as e:
                logging.error(f"Error processing {type(command).__name__} command ({str(e)})")
