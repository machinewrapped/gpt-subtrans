from PySide6.QtCore import QMutex, QMutexLocker
from GUI.ProjectViewModel import ProjectViewModel
from GUI.ProjectViewModelUpdate import ModelUpdate
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.TranslationProvider import TranslationProvider

class ProjectDataModel:
    _action_handlers = {}

    def __init__(self, project = None, options = None):
        self.project : SubtitleProject = project
        self.viewmodel : ProjectViewModel = None
        self.project_options = Options(options)
        self.mutex = QMutex()

        if project:
            project_settings = project.GetProjectSettings()
            self.project_options.update(project_settings)

        self.translation_provider : TranslationProvider = self.CreateTranslationProvider()

    @property
    def provider(self):
        return self.translation_provider.name if self.translation_provider else None
    
    @property
    def provider_settings(self):
        return self.project_options.current_provider_settings
    
    @property
    def available_providers(self):
        return self.project_options.available_providers if self.project_options else []
    
    @property
    def available_models(self):
        return self.translation_provider.available_models if self.translation_provider else []
    
    @property
    def selected_model(self):
        return self.translation_provider.selected_model if self.translation_provider else None

    def UpdateSettings(self, settings : dict):
        """ Update any options that have changed """
        self.project_options.update(settings)

        if self.project:
            # Restore project-specific settings
            project_settings = self.project.GetProjectSettings()
            self.project_options.update(project_settings)
            TranslationProvider.update_provider_settings(self.project_options)

        self._update_translation_provider()

    def UpdateProjectSettings(self, settings : dict):
        """ Update the project settings """
        if self.project:
            self.project.UpdateProjectSettings(settings)
            self.project_options.update(settings)
            TranslationProvider.update_provider_settings(self.project_options)
            self._update_translation_provider()

    def IsProjectInitialised(self):
        """Check whether the project has been initialised (subtitles loaded and batched)"""
        return self.project and self.project.subtitles and self.project.subtitles.scenes
    
    def NeedsSave(self):
        """Does the project have changes that should be saved"""
        return self.IsProjectInitialised() and self.project.needsupdate

    def NeedsAutosave(self):
        """Does the project have changes that should be auto-saved"""
        return self.NeedsSave() and self.project_options.get('autosave')
    
    def SaveProject(self):
        if self.NeedsSave():
            self.project.WriteProjectFile()

    def GetLock(self):
        return QMutexLocker(self.mutex)

    def CreateTranslationProvider(self):
        """ Create a translation provider for the current settings """
        TranslationProvider.update_provider_settings(self.project_options)
        if not self.project_options.provider:
            return None

        return TranslationProvider.get_provider(self.project_options)
    
    def UpdateProviderSettings(self, settings : dict):
        """ Update the settings for the translation provider """
        self.provider_settings.update(settings)
        if self.translation_provider:
            self.translation_provider.UpdateSettings(settings)

    def ValidateProviderSettings(self):
        """Check if the translation provider is configured correctly."""
        if not self.translation_provider or not self.translation_provider.ValidateSettings():
            self.PerformModelAction('Show Provider Settings', {})
            return False

        return True

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

    def _update_translation_provider(self):
        """
        Create or update translation provider based on settings
        """
        if self.project_options.provider:
            if self.provider and self.provider == self.project_options.provider:
                self.translation_provider.UpdateSettings(self.provider_settings)
            else:
                self.translation_provider = self.CreateTranslationProvider()
        else:
            self.translation_provider = None

    @classmethod
    def RegisterActionHandler(cls, action_name : str, handler : callable):
        handlers = cls._action_handlers.get(action_name) or []
        handlers.append(handler)
        cls._action_handlers[action_name] = handlers

