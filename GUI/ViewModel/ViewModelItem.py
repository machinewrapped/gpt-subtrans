from PySide6.QtGui import QStandardItem


class ViewModelItem(QStandardItem):
    def GetContent(self):
        return {
            'heading': "Item Heading",
            'subheading': "Optional Subheading",
            'body': "Body Content",
            'properties': {}
        }