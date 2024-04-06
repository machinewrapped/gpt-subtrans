from GUI.Command import Command
from GUI.ProjectDataModel import ProjectDataModel
from PySubtitle.Options import Options
from PySubtitle.SubtitleProject import SubtitleProject

import logging

class LoadSubtitleFile(Command):
    def __init__(self, filepath, options : Options):
        super().__init__()
        self.filepath = filepath
        self.project : SubtitleProject = None
        self.options : Options = Options(options)
        self.write_backup = self.options.get('write_backup', False)

    def execute(self):
        logging.debug(f"Executing LoadSubtitleFile {self.filepath}")

        if not self.filepath:
            return False

        try:
            self.options.InitialiseInstructions()

            project = SubtitleProject(self.options)
            project.InitialiseProject(self.filepath, write_backup=self.write_backup)

            if not project.subtitles:
                logging.error("Unable to load subtitles from {self.filepath}")
                return False

            self.project = project
            self.datamodel = ProjectDataModel(project, self.options)

            if self.datamodel.IsProjectInitialised():
                self.datamodel.CreateViewModel()

            return True

        except Exception as e:
            logging.error(f"Unable to load {self.filepath} ({str(e)})")
            return False

    def undo(self):
        # I suppose we _could_ store a reference to the previous project...
        pass