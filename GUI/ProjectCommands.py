import logging
from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from PySubtitleGPT.SubtitleProject import SubtitleProject
from PySubtitleGPT.SubtitleError import TranslationError

class BatchSubtitlesCommand(Command):
    """
    Attempt to partition subtitles into scenes and batches based on thresholds and limits.
    """
    def __init__(self, project : SubtitleProject):
        super().__init__()
        self.project : SubtitleProject = project

    def execute(self):
        logging.info("Executing BatchSubtitlesCommand")

        project : SubtitleProject = self.project
        datamodel : ProjectDataModel = self.datamodel or ProjectDataModel(project)

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

class MergeSelectionCommand(Command):
    """
    Combine multiple scenes or batches into one
    """
    def __init__(self, selection : ProjectSelection, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.selection = selection

    def execute(self):
        logging.info(f"Merging selection: {str(self.selection)}")

        selection : ProjectSelection = self.selection
        project : SubtitleProject = self.datamodel.project

        selection_map = selection.GetSelection()

        # First merge selected batches in each scene
        for scene_number, scene_map in selection_map.items():
            batch_numbers = [ key for key in scene_map.keys() if isinstance(key, int) ]
            if len(batch_numbers) > 1:
                project.subtitles.MergeBatches(scene_number, batch_numbers)

        # Then merge each selected scene
        scene_numbers = [ number for number, scene in selection_map.items() if scene.get('selected') ]
        if len(scene_numbers) > 1:
            project.subtitles.MergeScenes(scene_numbers)

        #TODO: incremental updates to the data/view model
        self.datamodel.CreateModel(project.subtitles)

        return True

class TranslateSceneCommand(Command):
    """
    Ask ChatGPT to translate a scene (optionally just select batches in the scene)
    """
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

