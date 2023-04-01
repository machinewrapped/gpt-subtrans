from PySide6.QtWidgets import QListView, QWidget

class SubtitleView(QListView):
    def __init__(self, parent) -> None:
        super().__init__(parent)