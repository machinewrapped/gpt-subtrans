import logging
from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from GUI.ProjectViewModelUpdate import ModelUpdate
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

            project.WriteProjectFile()

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
    def __init__(self, scene_number: int, batch_numbers: list[int], datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_numbers = batch_numbers
        self.original_first_line_numbers = None

    def execute(self):
        logging.info(f"Merging scene {str(self.scene_number)} batches: {','.join(str(x) for x in self.batch_numbers)}")

        project: SubtitleProject = self.datamodel.project
        scene = project.subtitles.GetScene(self.scene_number)

        if len(self.batch_numbers) > 1:
            self.original_first_line_numbers = [scene.GetBatch(batch_number).first_line_number for batch_number in self.batch_numbers]

            project.subtitles.MergeBatches(self.scene_number, self.batch_numbers)

        # TODO: Only replace the merged batches and renumber the rest
        self.model_update.scenes.replace(scene.number, scene)

        return True
    
    def undo(self):
        project: SubtitleProject = self.datamodel.project
        scene = project.subtitles.GetScene(self.scene_number)

        # Split the merged batch back into the original batches using the stored first line numbers
        for i in range(1, len(self.original_first_line_numbers)):
            scene.SplitBatch(self.batch_numbers[0], self.original_first_line_numbers[i])

        self.model_update.scenes.replace(scene.number, scene)

        return True

#############################################################

class MergeLinesCommand(Command):
    """
    Merge one or several lines together and renumber the rest
    """
    def __init__(self, selection : ProjectSelection, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.selection = selection

    def execute(self):
        originals = [line.number for line in self.selection.selected_originals]
        translated = [line.number for line in self.selection.selected_translated]

        if originals and translated and originals != translated:
            logging.info(f"Merging original lines {str(originals)} and translated lines {str(translated)}")
        elif originals:
            logging.info(f"Merging lines {str(originals)}")
        elif translated:
            logging.info(f"Merging translated lines {str(translated)}")
        else:
            raise CommandError("No lines selected to merge")

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise Exception("No subtitles")
        
        selected = self.selection.GetHierarchy()

        if selected:
            project.subtitles.MergeLines(selected)
            
            for scene_number in selected.keys():
                batches_to_update : list[SubtitleBatch] = [ project.subtitles.GetBatch(scene_number, batch_number) for batch_number in selected[scene_number].keys() ]

                for batch in batches_to_update:
                    self.model_update.batches.replace((scene_number, batch.number), batch)
            
            #TODO need to renumber all subsequent lines

        return True
    
    def undo(self):
        # TODO: Really need to implement undo for this!
        raise CommandError("Undo not supported for MergeLinesCommand yet")

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

        project.UpdateProjectFile()

        if scene:
            self.model_update.scenes.update(scene.number, {
                'summary' : scene.summary
            })

            for batch in scene.batches:
                if not self.batch_numbers or batch.number in self.batch_numbers:
                    self.model_update.batches.update((scene.number, batch.number), {
                        'summary' : batch.summary,
                        'context' : batch.context,
                        'errors' : batch.errors,
                        'translated' : { line.number : { 'text' : line.text } for line in batch.translated } 
                    })

        return True
    
    def _on_batch_translated(self, batch : SubtitleBatch):
        # Update viewmodel as each batch is translated 
        if self.datamodel:
            update = ModelUpdate()
            update.batches.update((batch.scene, batch.number), {
                'summary' : batch.summary,
                'context' : batch.context,
                'translated' : { line.number : { 'text' : line.text } for line in batch.translated } 
            })

            update.UpdateModel(self.datamodel)

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
        for original, translated in zip(batch.originals, batch.translated):
            if original and translated:
                self.model_update.originals.update((scene.number, batch.number, original.number), { 'text': translated.text } )
                self.model_update.translated.update((scene.number, batch.number, translated.number), { 'text': original.text } )

        return True
