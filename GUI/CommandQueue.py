import logging

from PySide6.QtCore import QObject, Signal, QThreadPool, QRecursiveMutex, QMutexLocker

from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel

#############################################################

class ClearCommandQueue(Command):
    """
    Pseudo-command to clear the command queue
    """
    def __init__(self, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)

    def execute(self):
        logging.info("Terminating command queue...")

#############################################################

class CommandQueue(QObject):
    """
    Execute commands on a background thread
    """
    commandAdded = Signal(object)
    commandExecuted = Signal(object, bool)
    
    def __init__(self, parent):
        super().__init__(parent)

        self.logger = logging.getLogger("CommandQueue")

        self.queue = []
        self.undo_stack = []

        self.mutex = QRecursiveMutex()

        self.command_pool = QThreadPool(self)
        self.SetMaxThreadCount(1)

    def SetMaxThreadCount(self, count):
        """
        Maximum number of worker threads
        """
        self.command_pool.setMaxThreadCount(count)

    @property
    def queue_size(self):
        with QMutexLocker(self.mutex):
            return len(self.queue)

    def Stop(self):
        """
        Shut the background thread down
        """
        if self.queue_size > 0:
            self._clear_command_queue()
        self.command_pool.waitForDone()

    def AddCommand(self, command: Command, datamodel: ProjectDataModel = None, callback=None, undo_callback=None):
        """
        Add a command to the command queue, with optional callbacks for completion/undo events
        """
        if not isinstance(command, Command):
            raise ValueError(f"Issued a command that is not a Command ({type(command).__name__})")

        self.logger.debug(f"Adding a {type(command).__name__} command to the queue")
        command.setParent(self)

        with QMutexLocker(self.mutex):
            if isinstance(command, ClearCommandQueue):
                command.execute()
                self._clear_command_queue()
            else:
                self._queue_command(command, datamodel, callback, undo_callback)

        self.commandAdded.emit(command)

        self._start_command_queue()

    def Contains(self, command_type: type = None, type_list : list[type] = None):
        """
        Check if the queue contains a command type(s)
        """
        if not command_type and not type_list:
            raise ValueError("Specify a command type or a list of command types")

        if type_list:
            if any( self.Contains(type) for type in type_list ):
                return True
        
        return command_type and any( [ isinstance(command, command_type) ] for command in self.queue )
    
    def AnyCommands(self):
        """
        Any commands in the queue?
        """
        return True if self.queue else False
    
    def AnyBlocking(self):
        """
        Any blocking commands in the queue?
        """
        return any( command.is_blocking for command in self.queue )

    def _on_command_executed(self, command: Command, success: bool):
        """
        Handle command callbacks, and queuing further actions
        """
        if not command.aborted:
            self.logger.debug(f"A {type(command).__name__} command was completed")
 
        with QMutexLocker(self.mutex):
            self.undo_stack.append(command)
            self.queue.remove(command)

        self.commandExecuted.emit(command, success)

        can_proceed = not command.aborted and not command.terminal
        if command.commands_to_queue and can_proceed:
            with QMutexLocker(self.mutex):
                for queued_command in command.commands_to_queue:
                    self._queue_command(queued_command, command.datamodel)

            for queued_command in command.commands_to_queue:
                self.commandAdded.emit(queued_command)

        if not command.aborted:
            self._start_command_queue()
            
    def _queue_command(self, command: Command, datamodel: ProjectDataModel = None, callback=None, undo_callback=None):
        """
        Add a command to the worker thread queue
        """
        self.queue.append(command)

        if datamodel:
            command.SetDataModel(datamodel)
        if callback:
            command.SetCallback(callback)
        if undo_callback:
            command.SetUndoCallback(undo_callback)

        command.commandExecuted.connect(self._on_command_executed)

    def _start_command_queue(self):
        if not self.queue:
            return

        self.logger.debug(f"Starting command queue")

        with QMutexLocker(self.mutex):
            for command in self.queue:
                if not command.started:
                    command.started = True
                    self.command_pool.start(command)

                if command.is_blocking:
                    break

    def _clear_command_queue(self):
        self.logger.debug(f"Clearing command queue")

        # Remove commands that haven't been started
        self.queue = [command for command in self.queue if command.started]

        # Request termination of remaining commands
        for command in self.queue:
            command.Abort()

