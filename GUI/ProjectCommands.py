import logging
from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitleGPT import SubtitleProject

class BatchSubtitlesCommand(Command):
    project : SubtitleProject
    
    def __init__(self, project):
        super().__init__()
        self.project = project

    def execute(self):
        logging.info("Executing BatchSubtitlesCommand")

        project = self.project
        datamodel = self.datamodel or ProjectDataModel()

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


