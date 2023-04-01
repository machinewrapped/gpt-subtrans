from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QHeaderView, QMainWindow, QMenu,
    QMenuBar, QPushButton, QSizePolicy, QSplitter,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget)

from GUI.ProjectToolbar import ProjectToolbar
from GUI.Widgets.LogWindow import LogWindow
from GUI.Widgets.ScenesBatchesPanel import ScenesBatchesPanel
from GUI.Widgets.SubtitleView import SubtitleView
from GUI.Widgets.ProjectViewer import ProjectViewer

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(855, 707)
        MainWindow.setMinimumSize(QSize(855, 576))
        self.actionOpenProject = QAction(MainWindow)
        self.actionOpenProject.setObjectName(u"actionOpenProject")
        self.actionQuit = QAction(MainWindow)
        self.actionQuit.setObjectName(u"actionQuit")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.splitter_3 = QSplitter(self.centralwidget)
        self.splitter_3.setObjectName(u"splitter_3")
        self.splitter_3.setOrientation(Qt.Vertical)
        self.projectViewer = ProjectViewer(self.splitter_3)
        self.projectViewer.setObjectName(u"project_viewer")
        self.projectViewer.setOrientation(Qt.Horizontal)
        self.sceneViewer = ScenesBatchesPanel(self.projectViewer)
        self.sceneViewer.setObjectName(u"sceneViewer")
        self.sceneViewer.setMinimumSize(QSize(399, 0))
        self.projectViewer.addWidget(self.sceneViewer)
        self.splitter = QSplitter(self.projectViewer)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.subtitlesView = SubtitleView(self.splitter)
        self.subtitlesView.setObjectName(u"subtitles_view")
        self.splitter.addWidget(self.subtitlesView)
        self.translationsView = SubtitleView(self.splitter)
        self.translationsView.setObjectName(u"translations_view")
        self.splitter.addWidget(self.translationsView)
        self.projectViewer.addWidget(self.splitter)
        self.splitter_3.addWidget(self.projectViewer)
        self.splitter_2 = QSplitter(self.splitter_3)
        self.splitter_2.setObjectName(u"splitter_2")
        self.splitter_2.setOrientation(Qt.Horizontal)
        self.projectOptionsView = QStackedWidget(self.splitter_2)
        self.projectOptionsView.setObjectName(u"project_options_view")
        self.Page1 = QWidget()
        self.Page1.setObjectName(u"Page1")
        self.verticalLayout_2 = QVBoxLayout(self.Page1)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.pushButton = QPushButton(self.Page1)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout_2.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.Page1)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.verticalLayout_2.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.Page1)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.verticalLayout_2.addWidget(self.pushButton_3)

        self.projectOptionsView.addWidget(self.Page1)
        self.splitter_2.addWidget(self.projectOptionsView)
        self.log_window = LogWindow(self.splitter_2)
        self.log_window.setObjectName(u"log_window")
        self.log_window.setReadOnly(True)
        self.splitter_2.addWidget(self.log_window)
        self.splitter_3.addWidget(self.splitter_2)

        self.verticalLayout.addWidget(self.splitter_3)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 855, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolbar = ProjectToolbar(MainWindow)
        self.toolbar.setObjectName(u"toolbar")
        MainWindow.addToolBar(Qt.TopToolBarArea, self.toolbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionOpenProject)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionQuit)
        self.toolbar.addAction(self.actionOpenProject)

        self.retranslateUi(MainWindow)
        self.actionOpenProject.triggered.connect(MainWindow.openProjectFile)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        MainWindow.setWindowFilePath("")
        self.actionOpenProject.setText(QCoreApplication.translate("MainWindow", u"Open Project", None))
        self.actionQuit.setText(QCoreApplication.translate("MainWindow", u"Quit", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"PushButton", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"PushButton", None))
        self.pushButton_3.setText(QCoreApplication.translate("MainWindow", u"PushButton", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.toolbar.setWindowTitle(QCoreApplication.translate("MainWindow", u"toolBar", None))
    # retranslateUi

