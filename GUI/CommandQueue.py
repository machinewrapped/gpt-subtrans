import logging

from PySide6.QtCore import Qt, QObject, Signal, QThreadPool, QRecursiveMutex, QMutexLocker

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
    commandUndone = Signal(object)

    def __init__(self, parent):
        super().__init__(parent)

        self.logger = logging.getLogger("CommandQueue")

        self.queue : list[Command] = []
        self.undo_stack : list[Command] = []
        self.redo_stack : list[Command] = []

        self.mutex = QRecursiveMutex()

        self.command_pool = QThreadPool(self)

        self.SetMaxThreadCount(1)

    def SetMaxThreadCount(self, count):
        """
        Maximum number of worker threads
        """
        self.command_pool.setMaxThreadCount(count)

    @property
    def queue_size(self) -> int:
        """
        Number of commands in the queue
        """
        with QMutexLocker(self.mutex):
            return len(self.queue)

    @property
    def has_commands(self) -> bool:
        """
        Check if the queue has any commands
        """
        with QMutexLocker(self.mutex):
            return len(self.queue) > 0

    @property
    def has_blocking_commands(self) -> bool:
        with QMutexLocker(self.mutex):
            return any( command.is_blocking for command in self.queue )

    @property
    def can_undo(self) -> bool:
        with QMutexLocker(self.mutex):
            return len(self.undo_stack) > 0 and self.undo_stack[-1].can_undo

    @property
    def can_redo(self) -> bool:
        with QMutexLocker(self.mutex):
            return len(self.redo_stack) > 0

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
        command.setAutoDelete(False)

        with QMutexLocker(self.mutex):
            if isinstance(command, ClearCommandQueue):
                command.execute()
                self._clear_command_queue()
            else:
                self._queue_command(command, datamodel, callback, undo_callback)
                self._clear_redo_stack()

        self.commandAdded.emit(command)

        self._start_command_queue()

    def UndoLastCommand(self):
        """
        Undo the last command in the undo stack
        """
        with QMutexLocker(self.mutex):
            command = self.undo_stack.pop()
            if not command.can_undo:
                self.logger.error(f"Cannot undo the last {type(command).__name__} command")
                return

            self.logger.info(f"Undoing {type(command).__name__}")
            self.redo_stack.append(command)
            command.undo()

        self.commandUndone.emit(command)

    def RedoLastCommand(self):
        """
        Redo the last command in the redo stack
        """
        with QMutexLocker(self.mutex):
            command = self.redo_stack.pop()

        if not command:
            self.logger.warning("No commands to redo")
            return

        self.logger.info(f"Redoing {type(command).__name__}")
        self._queue_command(command)
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

        with QMutexLocker(self.mutex):
            return command_type and any( [ isinstance(command, command_type) ] for command in self.queue )

    def ClearUndoStack(self):
        """
        Clear the undo stack
        """
        with QMutexLocker(self.mutex):
            for command in self.undo_stack:
                command.deleteLater()
            for command in self.redo_stack:
                command.deleteLater()

            self.undo_stack = []
            self.redo_stack = []

    def _on_command_executed(self, command: Command, success: bool):
        """
        Handle command callbacks, and queuing further actions
        """
        if not command.aborted:
            self.logger.debug(f"A {type(command).__name__} command was completed")

        command.commandExecuted.disconnect(self._on_command_executed)

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

        command.started = False
        command.commandExecuted.connect(self._on_command_executed, Qt.ConnectionType.QueuedConnection)

    def _start_command_queue(self):
        """
        Start the command queue
        """
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
        """
        Abort any running commands and clear the command queue
        """
        self.logger.debug(f"Clearing command queue")

        with QMutexLocker(self.mutex):
            # Remove commands that haven't been started
            self.queue = [command for command in self.queue if command.started]

        # Pop the remaining commands from the queue and abort
        while True:
            with QMutexLocker(self.mutex):
                if not self.queue:
                    break

                command = self.queue.pop(0)

            command.Abort()

    def _clear_redo_stack(self):
        """
        Remove commands from the redo stack and delete them
        """
        with QMutexLocker(self.mutex):
            for command in self.redo_stack:
                command.deleteLater()

            self.redo_stack = []