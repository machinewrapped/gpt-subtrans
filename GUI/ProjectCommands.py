import logging
from GUI.Command import Command

class BatchSubtitlesCommand(Command):
    def execute(self, datamodel):
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

    def undo(self, datamodel):
        # Do we flatten, or do we cache the previous batches?
        pass    