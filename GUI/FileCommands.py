import json
import logging
from GUI.Command import Command
from GUI.ProjectCommands import BatchSubtitlesCommand

from PySubtitleGPT.SubtitleProject import SubtitleProject

class LoadProjectFile(Command):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def execute(self, datamodel):
        logging.info(f"Executing LoadProjectFile {self.filepath}")

        options = datamodel.options

        if not self.filepath:
            return False

        try:        
            datamodel.project = SubtitleProject(options)
            datamodel.project.Initialise(self.filepath)
            datamodel.CreateDataModel(datamodel.project.subtitles)
            return True
        
        except Exception as e:
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

class LoadSubtitleFile(Command):
    def __init__(self, filepath):
        super().__init__()
        self.filepath = filepath

    def execute(self, datamodel):
        logging.info(f"Executing LoadSubtitleFile {self.filepath}")

        if not self.filepath:
            return False

        options = datamodel.options

        try:        
            datamodel.project = SubtitleProject(options)
            datamodel.project.Initialise(self.filepath)
            datamodel.commands_to_queue.append(BatchSubtitlesCommand())
            return True
        
        except Exception as e:
            return False

    def undo(self, datamodel):
        # I suppose we _could_ store a reference to the previous project!
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
