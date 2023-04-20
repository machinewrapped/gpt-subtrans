from PySide6.QtCore import QMutex, QMutexLocker
from GUI.ProjectViewModel import ProjectViewModel
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleProject import SubtitleProject

class ProjectDataModel:
    _action_handlers = {}

    def __init__(self, project = None, options = None):
        self.project : SubtitleProject = project
        self.viewmodel : ProjectViewModel = None
        self.options = options or Options()
        self.mutex = QMutex()

        if project and project.options:
              self.options.update(project.options)

    @classmethod
    def RegisterActionHandler(cls, action_name : str, handler : callable):
        handlers = cls._action_handlers.get(action_name) or []
        handlers.append(handler)
        cls._action_handlers[action_name] = handlers

    def PerformModelAction(self, action_name : str, params):
        with QMutexLocker(self.mutex):
            handlers = self._action_handlers.get(action_name)
            if handlers:
                for handler in handlers:
                    handler(self, *params)
            else:
                raise ValueError(f"No handler defined for action {action_name}")

    def CreateViewModel(self):
        with QMutexLocker(self.mutex):
            self.viewmodel = ProjectViewModel()
            self.viewmodel.CreateModel(self.project.subtitles)
        return self.viewmodel

    def UpdateViewModel(self, update : dict):
        if not self.viewmodel:
            raise Exception("Cannot update view model because it doesn't exist")
        
        with QMutexLocker(self.mutex):
            self.viewmodel.UpdateModel(update)
