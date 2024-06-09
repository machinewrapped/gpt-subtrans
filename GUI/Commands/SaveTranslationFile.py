from GUI.Command import Command
from PySubtitle.SubtitleProject import SubtitleProject

class SaveTranslationFile(Command):
    def __init__(self, project : SubtitleProject, filepath : str = None):
        super().__init__()
        self.filepath = filepath or project.subtitles.outputpath
        self.project = project

    def execute(self):
        self.project.SaveTranslation(self.filepath)
        return True