from GUI.Command import Command
from PySubtitle.Helpers import GetOutputPath
from PySubtitle.SubtitleProject import SubtitleProject

class SaveProjectFile(Command):
    def __init__(self, project : SubtitleProject, filepath : str|None = None):
        super().__init__()
        self.can_undo = False
        self.is_blocking = True
        self.project : SubtitleProject = project
        self.filepath : str|None = filepath or project.projectfile

    def execute(self):
        if not self.filepath:
            raise ValueError("Project file path must be specified.")

        self.project.projectfile = self.project.GetProjectFilepath(self.filepath)
        self.project.subtitles.outputpath = GetOutputPath(self.project.projectfile, self.project.target_language)
        self.project.WriteProjectFile()

        if self.project.subtitles.translated:
            self.project.SaveTranslation()

        return True
