#############################################################

from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand, TranslateSceneMultithreadedCommand

import logging

class ResumeTranslationCommand(Command):
    def __init__(self, datamodel: ProjectDataModel = None, multithreaded = False):
        super().__init__(datamodel)
        self.multithreaded = multithreaded
        self.skip_undo = True

    def execute(self):
        if not self.datamodel or not self.datamodel.project or not self.datamodel.project.subtitles:
            raise CommandError("Nothing to translate", command=self)

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