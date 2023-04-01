import logging
import os
import sys
from PySide6.QtWidgets import QApplication
from GUI.MainWindow import MainWindow

# This seems insane but ChatGPT told me to do it.
project_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_dir)

logging_level = eval(f"logging.{os.getenv('LOG_LEVEL', 'INFO')}")
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging_level)

def load_stylesheet(file_path):
    with open(file_path, 'r') as file:
        stylesheet = file.read()
    return stylesheet

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stylesheet = load_stylesheet("GUI\subtrans.qss")
    app.setStyleSheet(stylesheet)

    app.main_window = MainWindow()
    app.main_window.show()

    app.exec()
