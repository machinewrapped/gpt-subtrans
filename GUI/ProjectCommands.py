import logging
from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.ProjectSelection import ProjectSelection
from GUI.ProjectViewModelUpdate import ModelUpdate
from PySubtitle.Options import Options
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleError import TranslationError

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

        if not project or not project.subtitles:
            logging.error("No subtitles to batch")

        project.subtitles.AutoBatch(project.options)

        project.WriteProjectFile()

        self.datamodel : ProjectDataModel = self.datamodel or ProjectDataModel(project)
        self.datamodel.CreateViewModel()
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
        self.scene_numbers = sorted(scene_numbers)

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
        self.batch_numbers = sorted(batch_numbers)
        self.original_first_line_numbers = None

    def execute(self):
        logging.info(f"Merging scene {str(self.scene_number)} batches: {','.join(str(x) for x in self.batch_numbers)}")

        project: SubtitleProject = self.datamodel.project
        scene = project.subtitles.GetScene(self.scene_number)

        if len(self.batch_numbers) > 1:
            merged_batch_number = self.batch_numbers[0]

            self.original_first_line_numbers = [scene.GetBatch(batch_number).first_line_number for batch_number in self.batch_numbers]

            project.subtitles.MergeBatches(self.scene_number, self.batch_numbers)

            self.model_update.batches.replace((scene.number, merged_batch_number), scene.GetBatch(merged_batch_number))
            for batch_number in self.batch_numbers[1:]:
                self.model_update.batches.remove((scene.number, batch_number))

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
    Merge one or several lines together
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
            
        return True
    
    def undo(self):
        # TODO: Really need to implement undo for this!
        raise CommandError("Undo not supported for MergeLinesCommand yet")

#############################################################

class SplitBatchCommand(Command):
    def __init__(self, scene_number : int, batch_number : int, line_number : int, translation_number : int = None, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number
        self.line_number = line_number
        self.translation_number = translation_number

    def execute(self):
        logging.info(f"Splitting scene {str(self.scene_number)} batch: {str(self.batch_number)} at line {self.line_number}")

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise Exception("No subtitles")

        scene = project.subtitles.GetScene(self.scene_number)

        split_batch = scene.GetBatch(self.batch_number) if scene else None

        if not split_batch:
            raise CommandError(f"Cannot find scene {self.scene_number} batch {self.batch_number}")

        scene.SplitBatch(self.batch_number, self.line_number, self.translation_number)

        new_batch_number = self.batch_number + 1

        split_batch : SubtitleBatch = scene.GetBatch(self.batch_number)
        new_batch : SubtitleBatch = scene.GetBatch(new_batch_number)

        # Remove lines from the original batch that are in the new batch now
        for line_removed in range(self.line_number, new_batch.last_line_number + 1):
            self.model_update.originals.remove((self.scene_number, self.batch_number, line_removed))
            if new_batch.HasTranslatedLine(line_removed):
                self.model_update.translated.remove((self.scene_number, self.batch_number, line_removed))

        for batch_number in range(self.batch_number + 1, len(scene.batches)):
             self.model_update.batches.update((self.scene_number, batch_number), { 'number' : batch_number + 1})

        self.model_update.batches.add((self.scene_number, new_batch_number), scene.GetBatch(new_batch_number))

        return True

    def undo(self):
        project: SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise Exception("No subtitles")

        scene = project.subtitles.GetScene(self.scene_number)

        if not scene or not scene.GetBatch(self.batch_number):
            raise CommandError(f"Cannot find scene {self.scene_number} batch {self.batch_number}")

        try:
            scene.MergeBatches([self.batch_number, self.batch_number + 1])

            new_batch_number = self.batch_number + 1
            self.model_update.batches.replace((self.scene_number, self.batch_number), scene.GetBatch(self.batch_number))
            self.model_update.batches.remove((self.scene_number, new_batch_number), scene.GetBatch(new_batch_number))

            return True

        except Exception as e:
            raise CommandError(f"Unable to undo SplitBatchCommand command: {str(e)}")

#############################################################

class SplitSceneCommand(Command):
    def __init__(self, scene_number : int, batch_number : int, datamodel: ProjectDataModel = None):
        super().__init__(datamodel)
        self.scene_number = scene_number
        self.batch_number = batch_number

    def execute(self):
        logging.info(f"Splitting batch {str(self.scene_number)} at batch {str(self.batch_number)}")

        project : SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise Exception("No subtitles")
        
        scene = project.subtitles.GetScene(self.scene_number)
        if not scene:
            raise CommandError(f"Cannot split scene {self.scene_number} because it doesn't exist")
        
        last_batch = scene.batches[-1].number

        project.subtitles.SplitScene(self.scene_number, self.batch_number)

        for scene_number in range(self.scene_number + 1, len(project.subtitles.scenes)):
             self.model_update.scenes.update(scene_number, { 'number' : scene_number + 1})

        for batch_removed in range(self.batch_number, last_batch + 1):
            self.model_update.batches.remove((self.scene_number, batch_removed))

        self.model_update.scenes.add(self.scene_number + 1, project.subtitles.GetScene(self.scene_number + 1))

        return True

    def undo(self):
        project: SubtitleProject = self.datamodel.project

        if not project.subtitles:
            raise Exception("No subtitles")

        try:
            project.subtitles.MergeScenes([self.scene_number, self.scene_number + 1])
            self.model_update.rebuild = True

            return True
        
        except Exception as e:
            raise CommandError(f"Unable to undo SplitScene command: {str(e)}")


#############################################################

class TranslateSceneCommand(Command):
    """
    Ask the translator to translate a scene (optionally just select batches in the scene)
    """
    def __init__(self, scene_number : int, batch_numbers : list[int] = None, datamodel : ProjectDataModel = None):
        super().__init__(datamodel)
        self.translator = None
        self.scene_number = scene_number
        self.batch_numbers = batch_numbers

    def execute(self):
        if self.batch_numbers:
            logging.info(f"Translating scene number {self.scene_number} batch {','.join(str(x) for x in self.batch_numbers)}")
        else:
            logging.info(f"Translating scene number {self.scene_number}")

        if not self.datamodel.project:
            raise TranslationError("Unable to translate scene because project is not set on datamodel")

        project : SubtitleProject = self.datamodel.project
        options = self.datamodel.options

        self.translator = SubtitleTranslator(project.subtitles, options)

        self.translator.events.batch_translated += self._on_batch_translated

        scene = project.TranslateScene(self.scene_number, batch_numbers=self.batch_numbers, translator = self.translator)

        self.translator.events.batch_translated -= self._on_batch_translated

        project.UpdateProjectFile()

        if scene:
            self.model_update.scenes.update(scene.number, {
                'summary' : scene.summary
            })

            for batch in scene.batches:
                if batch.translated:
                    if not self.batch_numbers or batch.number in self.batch_numbers:
                        self.model_update.batches.update((scene.number, batch.number), {
                            'summary' : batch.summary,
                            'context' : batch.context,
                            'errors' : batch.errors,
                            'translation': batch.translation,
                            'translated' : { line.number : { 'text' : line.text } for line in batch.translated } 
                        })

        return True
    
    def on_abort(self):
        if self.translator:
            self.translator.StopTranslating()
    
    def _on_batch_translated(self, batch : SubtitleBatch):
        # Update viewmodel as each batch is translated 
        if self.datamodel and batch.translated:
            update = ModelUpdate()
            update.batches.update((batch.scene, batch.number), {
                'summary' : batch.summary,
                'context' : batch.context,
                'errors' : batch.errors,
                'translation': batch.translation,
                'translated' : { line.number : { 'text' : line.text } for line in batch.translated if line.number }
            })

            self.datamodel.UpdateViewModel(update)

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
        for original, translated in zip(batch.originals, batch.translated):
            if original and translated:
                self.model_update.originals.update((scene.number, batch.number, original.number), { 'text': translated.text } )
                self.model_update.translated.update((scene.number, batch.number, translated.number), { 'text': original.text } )

        return True
