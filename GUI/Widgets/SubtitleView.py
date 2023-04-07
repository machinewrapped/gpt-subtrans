from PySide6.QtWidgets import QListView

from GUI.ProjectViewModel import SubtitleItem
from GUI.Widgets.SubtitleItemDelegate import SubtitleItemDelegate
from GUI.Widgets.SubtitleListModel import SubtitleListModel

class SubtitleView(QListView):
    synchronise_scrolling = True    # TODO: Make this an option on the toolbar

    def __init__(self, parent=None):
        super().__init__(parent)

        subtitle_delegate = SubtitleItemDelegate()
        self.setItemDelegate(subtitle_delegate)

    def ShowSubtitles(self, subtitles):
        subtitle_items = [ item if isinstance(item, SubtitleItem) else SubtitleItem(item['index'], item) for item in subtitles ]
        model = SubtitleListModel(subtitle_items)
        self.setModel(model)

    def SynchroniseScrollbar(self, scrollbar):
        scrollbar.valueChanged.connect(self._partner_scrolled)

    def _partner_scrolled(self, value):
        if self.synchronise_scrolling:
            self.verticalScrollBar().setValue(value)