import json
import logging
from GUI.Command import Command
from GUI.ProjectCommands import BatchSubtitlesCommand
from GUI.ProjectDataModel import ProjectDataModel

from PySubtitleGPT.SubtitleProject import SubtitleProject

class LoadSubtitleFile(Command):
    project : SubtitleProject = None

    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

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
            self.datamodel = ProjectDataModel(project.options)

            if project.subtitles.scenes:
                self.datamodel.CreateDataModel(project.subtitles)
            else:
                self.commands_to_queue.append(BatchSubtitlesCommand(self.project))

            return True
        
        except Exception as e:
            logging.error(f"Unable to load {self.filepath} ({str(e)})")
            return False

    def undo(self):
        # I suppose we _could_ store a reference to the previous project...
        pass


class SaveProjectFile(Command):
    filename : str = None
    project : SubtitleProject = None

    def __init__(self, filename, project):
        super().__init__()
        self.filename = filename
        self.project = project

    def execute(self):
        self.project.WriteProjectFile(self.filename)

class SaveSubtitleFile(Command):
    def __init__(self, filename, subtitle_data):
        super().__init__()
        self.filename = filename
        self.subtitle_data = subtitle_data

    def execute(self):
        with open(self.filename, 'w') as f:
            json.dump(self.subtitle_data, f)
            # ... save subtitle data ...
            pass

class SaveTranslationFile(Command):
    def __init__(self, filename, translation_data):
        super().__init__()
        self.filename = filename
        self.translation_data = translation_data

    def execute(self):
        with open(self.filename, 'w') as f:
            json.dump(self.translation_data, f)
            # ... save translation data ...
            pass
