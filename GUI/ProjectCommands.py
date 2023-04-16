import logging
from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
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

            datamodel.CreateViewModel()

            self.datamodel = datamodel
            return True
        
        except Exception as e:
            return False

    def undo(self):
        # Do we flatten, or do we cache the previous batches?
        pass    

#############################################################

class MergeScenesCommand(Command):
    """
    Combine multiple scenes into one
    """
    def __init__(self, scene_numbers : list[int], datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_numbers = scene_numbers

    def execute(self):
        logging.info(f"Merging scenes {','.join(str(x) for x in self.scene_numbers)}")

        project : SubtitleProject = self.datamodel.project

        if len(self.scene_numbers) > 1:
            project.subtitles.MergeScenes(self.scene_numbers)

        #TODO: incremental updates to the data/view model
        self.datamodel.CreateViewModel()

        return True

#############################################################

class MergeBatchesCommand(Command):
    """
    Combine multiple batches into one
    """
    def __init__(self, scene_number : int, batch_numbers : list[int], datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_numbers = batch_numbers

    def execute(self):
        logging.info(f"Merging scene {str(self.scene_number)} batches: {','.join(str(x) for x in self.batch_numbers)}")

        project : SubtitleProject = self.datamodel.project

        # First merge selected batches in each scene
        if len(self.batch_numbers) > 1:
            project.subtitles.MergeBatches(self.scene_number, self.batch_numbers)

        #TODO: incremental updates to the data/view model
        self.datamodel.CreateViewModel()

        return True

#############################################################

class TranslateSceneCommand(Command):
    """
    Ask ChatGPT to translate a scene (optionally just select batches in the scene)
    """
    def __init__(self, scene_number : int, batch_numbers : list[int] = None, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_numbers = batch_numbers
        self.datamodel_update = { scene_number : {

        }}

    def execute(self):
        logging.info(f"Translating scene number {self.scene_number}")
        if not self.datamodel.project:
            raise TranslationError("Unable to translate scene because project is not set on datamodel")

        project : SubtitleProject = self.datamodel.project

        project.events.batch_translated += self._on_batch_translated

        scene = project.TranslateScene(self.scene_number, batch_numbers=self.batch_numbers)

        project.events.batch_translated -= self._on_batch_translated

        if scene:
            self.datamodel_update[scene.number].update({
                'summary' : scene.summary
            })

            for batch in scene.batches:
                if not self.batch_numbers or batch.number in self.batch_numbers:
                    self.datamodel_update[self.scene_number][batch.number] = {
                        'summary' : batch.summary,
                        'context' : batch.context,
                        'translated' : { line.number : { 'text' : line.text } for line in batch.translated } 
                    }

        return True
    
    def _on_batch_translated(self, batch : SubtitleBatch):
        if self.datamodel:
            update = {
                'summary' : batch.summary,
                'context' : batch.context,
                'translated' : { line.number : { 'text' : line.text } for line in batch.translated } 
            }
            self.datamodel.UpdateViewModel({ batch.scene : { 'batches' : { batch.number : update } } })

#############################################################

class SwapTextAndTranslations(Command):
    """
    Test class for model updates
    """
    def __init__(self, scene_number : int, batch_number : int, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number

    def execute(self):
        logging.info(f"Swapping text and translations in scene {self.scene_number} batch {self.batch_number}")
        if not self.datamodel.project:
            raise TranslationError("Unable to translate scene because project is not set on datamodel")

        project : SubtitleProject = self.datamodel.project
        file : SubtitleFile = project.subtitles
        scene : SubtitleScene = file.GetScene(self.scene_number)
        batch : SubtitleBatch = scene.GetBatch(self.batch_number)

        # Swap original and translated text (only in the viewmodel)
        self.datamodel_update  = {
            self.scene_number : {
                'batches' : {
                    self.batch_number : {
                        'originals' : { line.number : { 'text' : line.text } for line in batch.translated },
                        'translated' : { line.number : { 'text' : line.text } for line in batch.originals }
                    }           
                }
            }
        }

        return True
