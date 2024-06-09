from GUI.Command import Command, CommandError
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject

import logging

class LoadSubtitleFile(Command):
    def __init__(self, filepath, options : Options, reload_subtitles : bool = False):
        super().__init__()
        self.filepath = filepath
        self.project : SubtitleProject = None
        self.options : Options = Options(options)
        self.reload_subtitles = reload_subtitles
        self.write_backup = self.options.get('write_backup', False)
        self.can_undo = False

    def execute(self):
        logging.debug(f"Executing LoadSubtitleFile {self.filepath}")

        if not self.filepath:
            raise CommandError("No file path specified", command=self)

        try:
            self.options.InitialiseInstructions()

            project = SubtitleProject(self.options)
            project.InitialiseProject(self.filepath, reload_subtitles=self.reload_subtitles)

            if not project.subtitles:
                raise CommandError(f"Unable to load subtitles from {self.filepath}", command=self)

            if self.write_backup:
                logging.info("Saving backup copy of the project")
                project.WriteBackupFile()

            self.project = project
            self.datamodel = ProjectDataModel(project, self.options)

            if self.datamodel.IsProjectInitialised():
                self.datamodel.CreateViewModel()

            return True

        except Exception as e:
            raise CommandError(f"Unable to load {self.filepath} ({str(e)})", command=self)
