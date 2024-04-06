from GUI.Command import Command
from PySubtitle.SubtitleProject import SubtitleProject

class SaveTranslationFile(Command):
    def __init__(self, filepath, project : SubtitleProject):
        super().__init__()
        self.filepath = filepath
        self.project = project

    def execute(self):
        self.project.SaveTranslation(self.filepath)
        return True