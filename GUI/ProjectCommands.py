import logging
from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel

class BatchSubtitlesCommand(Command):
    def Execute(self, datamodel):
        logging.info("Executing BatchSubtitlesCommand")

        project = datamodel.project

        if not project or not project.subtitles:
            logging.error("No subtitles to batch")

        try:        
            project.subtitles.AutoBatch(datamodel.options, project)
            datamodel.CreateDataModel(datamodel.project.subtitles)
            return True
        
        except Exception as e:
            return False

    def Undo(self, datamodel):
        # Do we flatten, or do we cache the previous batches?
        pass    

class UpdateProjectOptionsCommand(Command):
    def __init__(self, options):
        super().__init__()
        self.options = options

    def Execute(self, datamodel: ProjectDataModel):
        if not self.options:
            return False
        
        if not datamodel.project:
            raise Exception("No project loaded")

        datamodel.project.UpdateProjectOptions(self.options)

        
