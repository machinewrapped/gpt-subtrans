import logging
from PySide6.QtWidgets import QTreeView, QAbstractItemView
from PySide6.QtCore import Qt

from GUI.Widgets.ScenesBatchesModel import ScenesBatchesModel
from GUI.Widgets.ScenesBatchesDelegate import ScenesBatchesDelegate

class ScenesView(QTreeView):
    def __init__(self, parent=None, viewmodel=None):
        super().__init__(parent)

        self.setMinimumWidth(500)
        self.setIndentation(20)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(True)
        self.setAnimated(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # Disable editing

        self.setItemDelegate(ScenesBatchesDelegate(self))  
        self.populate(viewmodel)

        self.clicked.connect(self.item_clicked)

    def clear(self):
        self.populate([])

    def populate(self, viewmodel):
        self.viewmodel = viewmodel
        self.model = ScenesBatchesModel(self.viewmodel)
        self.setModel(self.model)

    def item_clicked(self, index):
        model = index.model()
        data = model.data(index, role = Qt.ItemDataRole.UserRole)
        logging.info(f"Item clicked: {str(data)}")
        pass

