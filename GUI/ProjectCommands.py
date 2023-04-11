import logging
from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from PySubtitleGPT.SubtitleProject import SubtitleProject
from PySubtitleGPT.SubtitleError import TranslationError

class BatchSubtitlesCommand(Command):
    def __init__(self, project : SubtitleProject):
        super().__init__()
        self.project : SubtitleProject = project

    def execute(self):
        logging.info("Executing BatchSubtitlesCommand")

        project : SubtitleProject = self.project
        datamodel = self.datamodel or ProjectDataModel(project)

        if not project or not project.subtitles:
            logging.error("No subtitles to batch")

        try:
            project.subtitles.AutoBatch(datamodel.options)

            project.UpdateProjectFile()

            datamodel.CreateModel(project.subtitles)

            self.datamodel = datamodel
            return True
        
        except Exception as e:
            return False

    def undo(self):
        # Do we flatten, or do we cache the previous batches?
        pass    

class TranslateSceneCommand(Command):
    def __init__(self, scene_number : int, batch_numbers : list[int] = None, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_numbers = batch_numbers

    def execute(self):
        logging.info(f"Translating scene number {self.scene_number}")
        if not self.datamodel.project:
            raise TranslationError("Unable to translate scene because project is not set on datamodel")

        project : SubtitleProject = self.datamodel.project
        project.TranslateScene(self.scene_number, batch_numbers=self.batch_numbers)

        #TODO: incremental updates to the data/view model
        self.datamodel.CreateModel(project.subtitles)

        return True

