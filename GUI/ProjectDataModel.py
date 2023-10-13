from PySide6.QtCore import QMutex, QMutexLocker
from GUI.ProjectViewModel import ProjectViewModel
from GUI.ProjectViewModelUpdate import ModelUpdate
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject

class ProjectDataModel:
    _action_handlers = {}

    def __init__(self, project = None, options = None):
        self.project : SubtitleProject = project
        self.viewmodel : ProjectViewModel = None
        self.options = options or Options()
        self.mutex = QMutex()

        if project and project.options:
              self.options.update(project.options)

    def UpdateOptions(self, options : Options):
        """ Update any options that have changed """
        #TODO: only store options in project that are non-default
        self.project.UpdateProjectOptions(options)
        self.options.update(self.project.options)

    def IsProjectInitialised(self):
        """Check whether the project has been initialised (subtitles loaded and batched)"""
        return self.project and self.project.subtitles and self.project.subtitles.scenes
    
    def NeedsSave(self):
        """Does the project have changes that should be saved"""
        return self.IsProjectInitialised() and self.project.needsupdate

    def NeedsAutosave(self):
        """Does the project have changes that should be auto-saved"""
        return self.NeedsSave() and self.options.get('autosave')
    
    def SaveProject(self):
        if self.NeedsSave():
            self.project.WriteProjectFile()

    def GetLock(self):
        return QMutexLocker(self.mutex)

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
        """
        Create a viewmodel for the subtitles
        """
        with QMutexLocker(self.mutex):
            self.viewmodel = ProjectViewModel()
            self.viewmodel.CreateModel(self.project.subtitles)
        return self.viewmodel

    def UpdateViewModel(self, update : ModelUpdate):
        """
        Patch the viewmodel
        """
        if not isinstance(update, ModelUpdate):
            raise Exception("Invalid model update")

        if update.rebuild:
            # TODO: rebuild on the main thread
            self.CreateViewModel()
        elif self.viewmodel:
            self.viewmodel.AddUpdate(update)
