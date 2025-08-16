from collections.abc import Callable

from PySide6.QtWidgets import QToolBar, QStyle, QApplication
from PySide6.QtCore import Qt, SignalInstance
from PySide6.QtGui import QAction, QIcon

from GUI.CommandQueue import CommandQueue
from GUI.GuiInterface import GuiInterface
from GUI.ProjectActions import ProjectActions
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Commands.StartTranslationCommand import StartTranslationCommand
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand
from PySubtitle.Helpers.Localization import _
from PySubtitle.Helpers.Resources import GetResourcePath

class MainToolbar(QToolBar):
    """
    Main toolbar for the application
    """
    _action_groups = [
        ["Load Subtitles", "Save Project"],
        ["Start Translating", "Start Translating Fast", "Stop Translating"],
        ["Undo", "Redo"],
        ["Settings"],
        ["About", "Quit"]
        ]

    def __init__(self,  gui_interface : GuiInterface):
        super().__init__(_("Main Toolbar"))

        self.gui : GuiInterface = gui_interface

        self._actions : dict[str, QAction] = {}

        # Subscribe to UI language changes
        self.gui.uiLanguageChanged.connect(self.UpdateUiLanguage, Qt.ConnectionType.QueuedConnection)

        self.DefineActions()
        self.AddActionGroups()

        self.setMovable(False)

    def UpdateToolbar(self):
        """
        Update the toolbar
        """
        self.UpdateBusyStatus()
        self.UpdateTooltips()

    def UpdateUiLanguage(self):
        """Recreate actions/labels after language change."""
        # Remove existing actions and rebuild with translated labels
        for action in list(self.actions()):
            self.removeAction(action)
        self.clear()
        self.DefineActions()
        self.AddActionGroups()
        self.UpdateToolbar()

    def GetAction(self, name : str) -> QAction:
        return self._actions[name]

    def GetActionList(self, names : list[str]) -> list[QAction]:
        return [ self.GetAction(name) for name in names ]

    def DefineActions(self):
        """
        Define the supported actions
        """
        self._actions = {}
        action_handler : ProjectActions = self.gui.GetActionHandler()
        self.DefineAction('Quit', action_handler.exitProgram, self._icon_file('quit'), 'Ctrl+W', _('Exit Program'))
        self.DefineAction('Load Subtitles', action_handler.LoadProject, self._icon_file('load_subtitles'), 'Ctrl+O', _('Load Project/Subtitles (Hold shift to reload subtitles)'))
        self.DefineAction('Save Project', action_handler.SaveProject, self._icon_file('save_project'), 'Ctrl+S', _('Save project (Hold shift to save as...)'))
        self.DefineAction('Settings', action_handler.showSettings, self._icon_file('settings'), 'Ctrl+?', _('Settings'))
        self.DefineAction('Start Translating', action_handler.StartTranslating, self._icon_file('start_translating'), 'Ctrl+T', _('Start Translating (hold shift to retranslate)'))
        self.DefineAction('Start Translating Fast', action_handler.StartTranslatingFast, self._icon_file('start_translating_fast'), None, _('Start translating on multiple threads (fast but unsafe)'))
        self.DefineAction('Stop Translating', action_handler.StopTranslating, self._icon_file('stop_translating'), 'Esc', _('Stop translation'))
        self.DefineAction('Undo', action_handler.UndoLastCommand, self._icon_file('undo'), 'Ctrl+Z', _('Undo last action'))
        self.DefineAction('Redo', action_handler.RedoLastCommand, self._icon_file('redo'), 'Ctrl+Shift+Z', _('Redo last undone action'))
        self.DefineAction('About', action_handler.showAboutDialog, self._icon_file('about'), tooltip=_('About this program'))

    def DefineAction(self, name : str, function : Callable[..., None]|SignalInstance, icon : str|QIcon|None = None, shortcut : str|None = None, tooltip : str|None =None):
        """
        Define an action with a name, function, icon, shortcut, and tooltip.
        """
        # Keep English name as key; show localized text
        action = QAction(_(name))
        action.triggered.connect(function)

        if icon:
            if isinstance(icon, QStyle.StandardPixmap):
                icon = QApplication.style().standardIcon(icon)
            else:
                icon = QIcon(icon)
            action.setIcon(icon)

        if shortcut:
            action.setShortcut(shortcut)

        if tooltip:
            tip = _(tooltip)
            action.setToolTip(f"{tip} ({shortcut})" if shortcut else tip)

        self._actions[name] = action

    def AddActionGroups(self):
        for group in self._action_groups:
            if group != self._action_groups[0]:
                self.addSeparator()

            actions = self.GetActionList(group)
            for action in actions:
                self.addAction(action)

    def EnableActions(self, action_list : list[str]):
        """
        Enable a list of commands
        """
        for name in action_list:
            action = self._actions.get(name)
            if action:
                action.setEnabled(True)

    def DisableActions(self, action_list : list[str]):
        """
        Disable a list of commands
        """
        for name in action_list:
            action = self._actions.get(name)
            if action:
                action.setEnabled(False)

    def SetActionsEnabled(self, action_list : list[str], enabled : bool):
        """
        Enable or disable a list of commands
        """
        for name in action_list:
            action = self._actions.get(name)
            if action:
                action.setEnabled(enabled)

    def UpdateTooltip(self, action_name : str, label : str):
        """
        Update the label of a command
        """
        action : QAction|None = self._actions.get(action_name)
        if action:
            action.setToolTip(label)

    def UpdateBusyStatus(self):
        """
        Update the toolbar status based on the current state of the project
        """
        datamodel : ProjectDataModel = self.gui.GetDataModel()

        if not datamodel or not datamodel.IsProjectInitialised():
            self.DisableActions([ "Save Project", "Start Translating", "Start Translating Fast", "Stop Translating", "Undo", "Redo" ])
            self.EnableActions([ "Load Subtitles" ])
            return

        # Enable or disable toolbar commands  depending on whether any translations are ongoing
        command_queue : CommandQueue = self.gui.GetCommandQueue()
        if command_queue.Contains(type_list = [TranslateSceneCommand, StartTranslationCommand]):
            self.DisableActions([ "Load Subtitles", "Save Project", "Start Translating", "Start Translating Fast", "Undo", "Redo"])
            self.EnableActions([ "Stop Translating" ])
            return

        self.DisableActions(["Stop Translating"])

        no_blocking_commands = not command_queue.has_blocking_commands
        self.SetActionsEnabled([ "Load Subtitles", "Save Project", "Start Translating" ], no_blocking_commands)
        self.SetActionsEnabled([ "Start Translating Fast" ], no_blocking_commands and datamodel.allow_multithreaded_translation)
        self.SetActionsEnabled([ "Undo" ], no_blocking_commands and command_queue.can_undo)
        self.SetActionsEnabled([ "Redo" ], no_blocking_commands and command_queue.can_redo)

    def UpdateTooltips(self):
        """
        Update the labels on the toolbar
        """
        command_queue : CommandQueue = self.gui.GetCommandQueue()
        if command_queue.can_undo:
            last_command = command_queue.undo_stack[-1]
            self.UpdateTooltip("Undo", _("Undo {command}").format(command=type(last_command).__name__))
        else:
            self.UpdateTooltip("Undo", _("Nothing to undo"))

        if command_queue.can_redo:
            next_command = command_queue.redo_stack[-1]
            self.UpdateTooltip("Redo", _("Redo {command}").format(command=type(next_command).__name__))
        else:
            self.UpdateTooltip("Redo", _("Nothing to redo"))

    def _icon_file(self, icon_name : str) -> str:
        """
        Get the file path for an icon
        """
        return GetResourcePath("assets", "icons", f"{icon_name}.svg")
