import logging
from GUI.Command import Command, CommandError
from GUI.FileCommands import SaveProjectFile
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from PySubtitleGPT.SubtitleTranslator import SubtitleTranslator
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

        project.subtitles.AutoBatch(datamodel.options)

        project.WriteProjectFile()

        self.datamodel = datamodel
        datamodel.project = project
        datamodel.CreateViewModel()
        return True
        
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
            
            # TODO: maybe MergeLines should return the update (need a model update builder anyway)
            for scene_number in selected.keys():
                self.datamodel_update[scene_number] = { 'batches' : {} }
                for batch_number in selected[scene_number].keys():
                    batch = project.subtitles.GetBatch(scene_number, batch_number)

                    self.datamodel_update[scene_number]['batches'][batch_number] = {
                        'originals' : { line.number : { 'text' : line.text } for line in batch.originals },
                        'translated' : { line.number : { 'text' : line.text } for line in batch.translated } 
                    }

        return True
    
    def undo(self):
        # Really need to implement undo for this!
        return super().undo()

#############################################################

class TranslateSceneCommand(Command):
    """
    Ask ChatGPT to translate a scene (optionally just select batches in the scene)
    """
    def __init__(self, scene_number : int, batch_numbers : list[int] = None, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.translator = None
        self.scene_number = scene_number
        self.batch_numbers = batch_numbers
        self.datamodel_update = { scene_number : {

        }}

    def execute(self):
        if self.batch_numbers:
            logging.info(f"Translating scene number {self.scene_number} batch {','.join(str(x) for x in self.batch_numbers)}")
        else:
            logging.info(f"Translating scene number {self.scene_number}")

        if not self.datamodel.project:
            raise TranslationError("Unable to translate scene because project is not set on datamodel")

        project : SubtitleProject = self.datamodel.project

        self.translator = SubtitleTranslator(project.subtitles, project.options)

        self.translator.events.batch_translated += self._on_batch_translated

        scene = project.TranslateScene(self.scene_number, batch_numbers=self.batch_numbers, translator = self.translator)

        self.translator.events.batch_translated -= self._on_batch_translated

        project.UpdateProjectFile()

        if scene:
            self.datamodel_update[scene.number].update({
                'summary' : scene.summary
            })

            for batch in scene.batches:
                if batch.translated:
                    if not self.batch_numbers or batch.number in self.batch_numbers:
                        self.datamodel_update[self.scene_number][batch.number] = {
                            'summary' : batch.summary,
                            'context' : batch.context,
                            'errors' : batch.errors,
                            'translation': batch.translation,
                            'translated' : { line.number : { 'text' : line.text } for line in batch.translated } 
                        }

        return True
    
    def on_abort(self):
        if self.translator:
            self.translator.StopTranslating()
    
    def _on_batch_translated(self, batch : SubtitleBatch):
        if self.datamodel and batch.translated:
            update = {
                'summary' : batch.summary,
                'context' : batch.context,
                'errors' : batch.errors,
                'translation': batch.translation,
                'translated' : { line.number : { 'text' : line.text } for line in batch.translated if line.number }
            }
            self.datamodel.UpdateViewModel({ batch.scene : { 'batches' : { batch.number : update } } })


#############################################################

class TranslateSceneMultithreadedCommand(TranslateSceneCommand):
    """
    A non-blocking version of TranslateSceneCommand
    """
    def __init__(self, scene_number: int, batch_numbers: list[int] = None, datamodel: ProjectDataModel = None):
        super().__init__(scene_number, batch_numbers, datamodel)
        self.is_blocking = False

#############################################################

class ResumeTranslationCommand(Command):
    def __init__(self, datamodel: ProjectDataModel = None, multithreaded = False):
        super().__init__(datamodel)
        self.multithreaded = multithreaded

    def execute(self):
        if not self.datamodel or not self.datamodel.project or not self.datamodel.project.subtitles:
            raise CommandError("Nothing to translated")

        subtitles = self.datamodel.project.subtitles

        if subtitles.scenes and all(scene.all_translated for scene in subtitles.scenes):
            logging.info("All scenes are fully translated")
            return True

        starting = "Resuming" if self.datamodel.project.AnyTranslated() else "Starting"
        threaded = "multithreaded" if self.multithreaded else "single threaded"
        logging.info(f"{starting} {threaded} translation")

        translate_command : TranslateSceneCommand = self

        for scene in subtitles.scenes:
            if not scene.all_translated:
                batch_numbers = [ batch.number for batch in scene.batches if not batch.all_translated ] if scene.any_translated else None

                if self.multithreaded:
                    # Queue scenes in parallel
                    command = TranslateSceneMultithreadedCommand(scene.number, batch_numbers, datamodel=self.datamodel)
                    translate_command.commands_to_queue.append(command)
                else:
                    # Queue scenes in series
                    command = TranslateSceneCommand(scene.number, batch_numbers, datamodel=self.datamodel)
                    translate_command.commands_to_queue.append(command)
                    translate_command = command

        return True

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
