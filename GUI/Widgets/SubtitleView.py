from PySide6.QtWidgets import QListView

from GUI.ProjectViewModel import SubtitleItem
from GUI.Widgets.SubtitleItemDelegate import SubtitleItemDelegate
from GUI.Widgets.SubtitleListModel import SubtitleListModel

class SubtitleView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)

        subtitle_delegate = SubtitleItemDelegate()
        self.setItemDelegate(subtitle_delegate)

    def show_subtitles(self, subtitles):
        subtitle_items = [ item if isinstance(item, SubtitleItem) else SubtitleItem(item['index'], item) for item in subtitles ]
        model = SubtitleListModel(subtitle_items)
        self.setModel(model)
