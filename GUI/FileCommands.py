import json
import logging
from GUI.Command import Command
from GUI.ProjectCommands import BatchSubtitlesCommand
from GUI.ProjectDataModel import ProjectDataModel

from PySubtitleGPT.SubtitleProject import SubtitleProject

class LoadSubtitleFile(Command):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath
        self.project : SubtitleProject = None

    def execute(self):
        logging.info(f"Executing LoadSubtitleFile {self.filepath}")

        if not self.filepath:
            return False

        try:
            options = self.datamodel.options if self.datamodel else None
            project = SubtitleProject(options)
            project.Initialise(self.filepath)

            if not project.subtitles:
                logging.error("Unable to load subtitles from {self.filepath}")
                return False
            
            self.project = project
            self.datamodel = ProjectDataModel(project)

            if project.subtitles.scenes:
                self.datamodel.CreateModel(project.subtitles)
            else:
                self.commands_to_queue.append(BatchSubtitlesCommand(project))

            return True
        
        except Exception as e:
            logging.error(f"Unable to load {self.filepath} ({str(e)})")
            return False

    def undo(self):
        # I suppose we _could_ store a reference to the previous project...
        pass


class SaveProjectFile(Command):
    def __init__(self, filename, project : SubtitleProject):
        super().__init__()
        self.filename = filename
        self.project = project

    def execute(self):
        self.project.WriteProjectFile(self.filename)
        self.project.subtitles.SaveTranslation()

class SaveSubtitleFile(Command):
    def __init__(self, filename, project : SubtitleProject):
        super().__init__()
        self.filename = filename
        self.project = project

    def execute(self):
        self.project.subtitles.SaveSubtitles(self.filename)

class SaveTranslationFile(Command):
    def __init__(self, filename, project : SubtitleProject):
        super().__init__()
        self.filename = filename
        self.project = project

    def execute(self):
        self.project.subtitles.SaveTranslation(self.filename)
