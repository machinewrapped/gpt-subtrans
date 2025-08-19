import logging
from typing import Any

from PySide6.QtCore import QRecursiveMutex, QMutexLocker

from GUI.ViewModel.ViewModel import ProjectViewModel
from GUI.ViewModel.ViewModelUpdate import ModelUpdate

from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.TranslationProvider import TranslationProvider
from PySubtitle.Helpers.Localization import _

class ProjectDataModel:
    def __init__(self, project : SubtitleProject|None = None, options : Options|None = None):
        self.project : SubtitleProject|None = project
        self.viewmodel : ProjectViewModel|None = None
        self.project_options : Options = Options(options)
        self.mutex = QRecursiveMutex()

        if project:
            project_settings = project.GetProjectSettings()
            self.project_options.update(project_settings)

        self.provider_cache = {}
        self.translation_provider : TranslationProvider|None = None

        if self.project_options.provider:
            self.CreateTranslationProvider()

    @property
    def provider(self):
        return self.translation_provider.name if self.translation_provider else None

    @property
    def provider_settings(self) -> dict[str, Any]:
        return self.project_options.current_provider_settings or {} if self.project_options else {}

    @property
    def available_providers(self) -> list[str]:
        return self.project_options.available_providers if self.project_options else []

    @property
    def available_models(self) -> list[str]:
        return self.translation_provider.available_models if self.translation_provider else []

    @property
    def selected_model(self) -> str|None:
        return self.translation_provider.selected_model if self.translation_provider else None

    @property
    def target_language(self):
        return self.project_options.target_language
    
    @property
    def task_type(self):
        return self.project.task_type if self.project else None

    @property
    def allow_multithreaded_translation(self):
        if not self.translation_provider:
            return False

        if self.project_options.get('max_threads', 1) == 1:
            return False

        return self.translation_provider.allow_multithreaded_translation

    @property
    def autosave_enabled(self):
        return self.project and self.project_options.get('autosave', False)

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

    def IsProjectValid(self) -> bool:
        """Check whether the project is valid (has any subtitles)"""
        return self.project is not None and self.project.subtitles is not None

    def IsProjectInitialised(self) -> bool:
        """Check whether the project has been initialised (subtitles loaded and batched)"""
        return self.project is not None and self.project.subtitles is not None and self.project.subtitles.scenes is not None

    def NeedsSave(self) -> bool:
        """Does the project have changes that should be saved"""
        return self.project is not None and self.IsProjectInitialised() and self.project.write_project

    def NeedsAutosave(self) -> bool:
        """Does the project have changes that should be auto-saved"""
        return self.NeedsSave() and self.project_options.get('autosave')

    def SaveProject(self):
        if self.project is not None and self.NeedsSave():
            self.project.UpdateProjectFile()

    def GetLock(self):
        return QMutexLocker(self.mutex)

    def CreateTranslationProvider(self) -> TranslationProvider|None:
        """ Create a translation provider for the current settings """
        if not self.project_options.provider:
            return None

        try:
            self.translation_provider = TranslationProvider.get_provider(self.project_options)
            self.provider_cache[self.translation_provider.name] = self.translation_provider

        except Exception as e:
            if self.provider is not None:
                logging.warning(_("Unable to create {provider} provider: {error}").format(provider=self.provider, error=e))
            return None

    def UpdateProviderSettings(self, settings : dict):
        """ Update the settings for the translation provider """
        self.provider_settings.update(settings)
        if self.translation_provider:
            self.translation_provider.UpdateSettings(settings)

    def ValidateProviderSettings(self) -> bool:
        """Check if the translation provider is configured correctly."""
        if not self.translation_provider or not self.translation_provider.ValidateSettings():
            return False

        return True

    def CreateViewModel(self) -> ProjectViewModel:
        """
        Create a viewmodel for the subtitles
        """
        with QMutexLocker(self.mutex):
            self.viewmodel = ProjectViewModel()
            if self.project is not None:
                self.viewmodel.CreateModel(self.project.subtitles)
        return self.viewmodel

    def UpdateViewModel(self, update : ModelUpdate):
        """
        Patch the viewmodel
        """
        if not isinstance(update, ModelUpdate):
            raise ValueError("Invalid model update")

        if self.viewmodel:
            self.viewmodel.AddUpdate(lambda viewmodel=self.viewmodel, model_update=update : model_update.ApplyToViewModel(viewmodel))

    def _update_translation_provider(self):
        """
        Create or update translation provider based on settings
        """
        provider = self.project_options.provider
        if not provider:
            self.translation_provider = None
            return

        if provider in self.provider_cache:
            self.translation_provider = self.provider_cache[provider]
            if self.translation_provider:
                self.translation_provider.UpdateSettings(self.project_options)
            return

        self.CreateTranslationProvider()


