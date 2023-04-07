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

    def execute(self, datamodel: ProjectDataModel):
        logging.info(f"Executing LoadSubtitleFile {self.filepath}")

        if not self.filepath:
            return False

        options = datamodel.options

        try:
            project = SubtitleProject(options)
            project.Initialise(self.filepath)

            if not project.subtitles:
                logging.error("Unable to load subtitles from {self.filepath}")
                return False
            
            datamodel.project = project
            datamodel.viewmodel = None

            if project.subtitles.scenes:
                datamodel.CreateDataModel(project.subtitles)
            else:
                datamodel.commands_to_queue.append(BatchSubtitlesCommand())

            return True
        
        except Exception as e:
            logging.error(f"Unable to load {self.filepath} ({str(e)})")
            return False

    def undo(self, datamodel):
        # I suppose we _could_ store a reference to the previous project!
        pass


class SaveProjectFile(Command):
    def __init__(self, filename, project_data):
        super().__init__()
        self.filename = filename
        self.project_data = project_data

    def execute(self):
        with open(self.filename, 'w') as f:
            json.dump(self.project_data, f)
            # ... save project data ...
            pass

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
