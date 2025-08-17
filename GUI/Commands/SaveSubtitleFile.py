from GUI.Command import Command, CommandError
from PySubtitle.Helpers.Localization import _
from PySubtitle.SubtitleProject import SubtitleProject

class SaveSubtitleFile(Command):
    def __init__(self, filepath, project : SubtitleProject):
        super().__init__()
        self.filepath = filepath
        self.project = project

    def execute(self):
        if not self.datamodel or not self.datamodel.project:
            raise CommandError(_("No project data"), command=self)

        self.project.subtitles.SaveOriginal(self.filepath)
        return True