import logging
from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitleGPT import SubtitleProject
from PySubtitleGPT.SubtitleError import TranslationError

class BatchSubtitlesCommand(Command):
    def __init__(self, project):
        super().__init__()
        self.project = project

    def execute(self):
        logging.info("Executing BatchSubtitlesCommand")

        project = self.project
        datamodel = self.datamodel or ProjectDataModel(project)

        if not project or not project.subtitles:
            logging.error("No subtitles to batch")

        try:
            project.subtitles.AutoBatch(datamodel.options, project)
            datamodel.CreateDataModel(project.subtitles)
            self.datamodel = datamodel
            return True
        
        except Exception as e:
            return False

    def undo(self):
        # Do we flatten, or do we cache the previous batches?
        pass    

class TranslateBatchCommand(Command):
    def __init__(self, batch_number, datamodel=None):
        super().__init__(datamodel)
        self.batch_number = batch_number

    def execute(self):
        logging.info(f"Translating batch number {self.batch_number}")
        if not self.datamodel.project:
            raise TranslationError("Unable to translate batch because project is not set on datamodel")

        project = self.datamodel.project
        project.TranslateBatch(self.batch_number)

        #TODO: incremental updates to the data/view model
        self.datamodel.CreateDataModel(project.subtitles)

        return True
