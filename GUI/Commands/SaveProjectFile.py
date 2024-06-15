from GUI.Command import Command
from PySubtitle.Helpers import GetOutputPath
from PySubtitle.SubtitleProject import SubtitleProject

class SaveProjectFile(Command):
    def __init__(self, project : SubtitleProject, filepath = None):
        super().__init__()
        self.project = project
        self.filepath = filepath or project.projectfile
        self.can_undo = False
        self.is_blocking = True

    def execute(self):
        self.project.projectfile = self.project.GetProjectFilepath(self.filepath)
        self.project.subtitles.outputpath = GetOutputPath(self.project.projectfile, self.project.target_language, self.project.subtitles.extension)
        self.project.WriteProjectFile()

        if self.project.subtitles.translated:
            self.project.SaveTranslation()

        return True
