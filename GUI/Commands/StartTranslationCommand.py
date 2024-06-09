import logging

from GUI.Command import Command, CommandError
from GUI.Commands.SaveProjectFile import SaveProjectFile
from GUI.ProjectDataModel import ProjectDataModel
from GUI.Commands.TranslateSceneCommand import TranslateSceneCommand

from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject

class StartTranslationCommand(Command):
    def __init__(self, datamodel: ProjectDataModel = None, resume : bool = False, multithreaded : bool = False, scenes : dict = None):
        super().__init__(datamodel)
        self.multithreaded = multithreaded
        self.skip_undo = True
        self.is_blocking = True
        self.resume = resume
        self.scenes = scenes or {}

    def execute(self):
        if not self.datamodel or not self.datamodel.project or not self.datamodel.project.subtitles:
            raise CommandError("Nothing to translate", command=self)

        project : SubtitleProject = self.datamodel.project
        subtitles : SubtitleFile = project.subtitles

        if self.resume and subtitles.scenes and all(scene.all_translated for scene in subtitles.scenes):
            logging.info("All scenes are fully translated")
            return True

        starting = "Resuming" if self.resume and project.any_translated else "Starting"
        threaded = "multithreaded" if self.multithreaded else "single threaded"
        logging.info(f"{starting} {threaded} translation")

        previous_command : TranslateSceneCommand = self

        # Save the project first if it needs updating
        if project.needs_writing:
            command = SaveProjectFile(project=project)
            self.commands_to_queue.append(command)
            previous_command = command

        for scene in subtitles.scenes:
            if self.resume and scene.all_translated:
                continue

            if self.scenes and scene.number not in self.scenes:
                continue

            scene_data = self.scenes.get(scene.number, {})
            batch_numbers = scene_data.get('batches', None)
            line_numbers = scene_data.get('lines', None)

            if self.resume and scene.any_translated:
                batch_numbers = batch_numbers or [ batch.number for batch in scene.batches ]
                batch_numbers = [ number for number in batch_numbers if not scene.GetBatch(number).all_translated ]

            command = TranslateSceneCommand(scene.number, batch_numbers, line_numbers, datamodel=self.datamodel)

            if self.multithreaded:
                # Queue the commands in parallel
                self.commands_to_queue.append(command)
            else:
                # Queue the commands in sequence
                previous_command.commands_to_queue.append(command)
                previous_command = command

                if self.datamodel.autosave_enabled:
                    command.commands_to_queue.append(SaveProjectFile(project=project))

        return True