import logging
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

        self.provider_cache = {}
        self.translation_provider : TranslationProvider = None

        if self.project_options.provider:
            self.CreateTranslationProvider()

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

        self._update_translation_provider()

    def UpdateProjectSettings(self, settings : dict):
        """ Update the project settings """
        if self.project:
            self.project_options.update(settings)
            self._update_translation_provider()
            self.project.UpdateProjectSettings(settings)

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
        if not self.project_options.provider:
            return None

        try:
            self.translation_provider = TranslationProvider.get_provider(self.project_options)
            self.provider_cache[self.translation_provider.name] = self.translation_provider

        except Exception as e:
            logging.warning(f"Unable to create {self.provider} provider: {e}")
            return None
    
    def UpdateProviderSettings(self, settings : dict):
        """ Update the settings for the translation provider """
        self.provider_settings.update(settings)
        if self.translation_provider:
            self.translation_provider.UpdateSettings(settings)

    def ValidateProviderSettings(self):
        """Check if the translation provider is configured correctly."""
        if not self.translation_provider or not self.translation_provider.ValidateSettings():
            return False

        return True

    def PerformModelAction(self, action_name : str, params = None):
        params = params or {}
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
        provider = self.project_options.provider
        if not provider:
            self.translation_provider = None
            return
        
        if provider in self.provider_cache:
            self.translation_provider : TranslationProvider = self.provider_cache[provider]
            self.translation_provider.UpdateSettings(self.project_options)
            return

        self.CreateTranslationProvider()

    @classmethod
    def RegisterActionHandler(cls, action_name : str, handler : callable):
        handlers = cls._action_handlers.get(action_name) or []
        handlers.append(handler)
        cls._action_handlers[action_name] = handlers

