import logging
import threading
import debugpy
from queue import Queue

from PySide6.QtCore import QThread, QObject, Signal, Slot

from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel

class CommandQueue(QObject):
    """
    Execute commands on a background thread
    """
    commandAdded = Signal(object)
    commandExecuted = Signal(object, bool)

    undo_stack = []

    def __init__(self):
        super().__init__()

        self.command_queue = CommandQueueWorker()
        self.command_queue.commandExecuted.connect(self._on_command_executed)
        self.mutex = threading.Lock()

        self.logger = logging.getLogger("CommandQueue")

    def Stop(self):
        """
        Shut the background thread down
        """
        if self.command_queue:
            self.command_queue.Shutdown()

    def AddCommand(self, command : Command, datamodel : ProjectDataModel = None, callback = None, undo_callback = None):
        """
        Add a command to the command queue, with option callbacks for completion/undo events
        """
        if command:
            self.logger.debug(f"Adding a {type(command).__name__} command to the queue")
            with self.mutex:
                self._queue_command(command, datamodel, callback, undo_callback)
            self.commandAdded.emit(command)

    def _on_command_executed(self, command : Command, success : bool):
        """
        Handle command callbacks, and queuing further actions 
        """
        self.logger.debug(f"A {type(command).__name__} command was completed")
        self.undo_stack.append(command)

        if command.commands_to_queue:
            with self.mutex:
                for command in command.commands_to_queue:
                    self._queue_command(command, command.datamodel)

            for command in command.commands_to_queue:
                self.logger.debug(f"Added a {type(command).__name__} command to the queue")
                self.commandAdded.emit(command)

        self.commandExecuted.emit(command, success)

    def _queue_command(self, command : Command, datamodel : ProjectDataModel = None, callback=None, undo_callback=None):
        """
        Add a command to the worker thread queue
        """
        if datamodel:
            command.SetDataModel(datamodel)
        if callback:
            command.SetCallback(callback)
        if undo_callback:
            command.SetUndoCallback(undo_callback)

        self.command_queue.AddCommand(command)

class CommandQueueWorker(QThread):
    """
    Execute commands on a background thread
    """
    commandExecuted = Signal(object, bool)

    class StopThread(Command):
        def execute(self):
            raise CommandQueueWorker.StopThreadException()

    def __init__(self):
        super().__init__()

        self.queue = Queue()

        self.moveToThread(self)
        self.started.connect(self.run)
        self.start()

    def AddCommand(self, command : Command):
        self.queue.put(command)

    def Shutdown(self):
        self.AddCommand(CommandQueueWorker.StopThread())
        self.wait(100)

    @Slot()
    def run(self):
        debugpy.debug_this_thread()
        while self.queue:
            command : Command = self.queue.get()
            try:
                if isinstance(command, CommandQueueWorker.StopThread):
                    self.exit()
                    break

                success = command.execute()

                self.commandExecuted.emit(command, success)

            except Exception as e:
                logging.error(f"Error processing {type(command).__name__} command ({str(e)})")
