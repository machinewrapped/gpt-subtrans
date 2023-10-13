import logging
from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Helpers import GetOutputPath
from PySubtitle.Options import Options

from PySubtitle.SubtitleProject import SubtitleProject

class LoadSubtitleFile(Command):
    def __init__(self, filepath, options : Options):
        super().__init__()
        self.filepath = filepath
        self.project : SubtitleProject = None
        self.options : Options = options

    def execute(self):
        logging.debug(f"Executing LoadSubtitleFile {self.filepath}")

        if not self.filepath:
            return False

        try:
            options = self.options
            if not options:
                options = Options()
                options.Load()

            project = SubtitleProject(options)
            project.Initialise(self.filepath)

            if not project.subtitles:
                logging.error("Unable to load subtitles from {self.filepath}")
                return False
            
            self.project = project
            self.datamodel = ProjectDataModel(project, project.options)

            if self.datamodel.IsProjectInitialised():
                self.datamodel.CreateViewModel()

            return True
        
        except Exception as e:
            logging.error(f"Unable to load {self.filepath} ({str(e)})")
            return False

    def undo(self):
        # I suppose we _could_ store a reference to the previous project...
        pass

class SaveProjectFile(Command):
    def __init__(self, project : SubtitleProject, filepath = None):
        super().__init__()
        self.project = project
        self.filepath = filepath or project.subtitles.outputpath

    def execute(self):
        self.project.projectfile = self.project.GetProjectFilepath(self.filepath)
        self.project.WriteProjectFile()

        if self.project.subtitles.translated:
            outputpath = GetOutputPath(self.project.projectfile)
            self.project.SaveSubtitles(outputpath)
        return True

class SaveSubtitleFile(Command):
    def __init__(self, filepath, project : SubtitleProject):
        super().__init__()
        self.filepath = filepath
        self.project = project

    def execute(self):
        self.project.subtitles.SaveOriginals(self.filepath)
        return True

class SaveTranslationFile(Command):
    def __init__(self, filepath, project : SubtitleProject):
        super().__init__()
        self.filepath = filepath
        self.project = project

    def execute(self):
        self.project.SaveSubtitles(self.filepath)
        return True
