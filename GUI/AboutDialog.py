import os
import pkg_resources
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QDialogButtonBox, QLabel, QHBoxLayout)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from GUI.GuiHelpers import GetResourcePath

from PySubtitle.version import __version__

class AboutDialog(QDialog):
    """
    Show application information etc.
    """
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle("About GUI-Subtrans")
        self.setMinimumWidth(512)
        self.setMaximumWidth(768)
        
        # Main Horizontal Layout
        main_layout = QHBoxLayout(self)

        # Image on the left
        image_layout = QVBoxLayout()        
        image_label = QLabel(self)
        filepath = GetResourcePath(os.path.join("theme", "subtransmd.png"))
        pixmap = QPixmap(filepath)
        image_label.setPixmap(pixmap)
        
        # Label for image attribution
        image_attribution_label = QLabel('Logo generated with <a href="https://stability.ai/stablediffusion">Stable Diffusion XL</a>')
        image_attribution_label.setOpenExternalLinks(True)  # This ensures the link opens in a default web browser
        image_attribution_label.setWordWrap(True)
        image_attribution_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_layout.addWidget(image_label)
        image_layout.addWidget(image_attribution_label)
        main_layout.addLayout(image_layout)

        # Right side vertical layout
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(f"GUI-Subtrans Version {__version__}")
        font = title_label.font()
        font.setPointSize(24)
        title_label.setFont(font)
        
        # Description
        description_label = QLabel("GUI-Subtrans uses OpenAI's GPT AI to translate SRT subtitles into other languages, or to improve the quality of an existing translation.")
        description_label.setWordWrap(True)
        
        # Author Information and GitHub link
        author_label = QLabel("Developed by: MachineWrapped<br>"
                              "Contact: machinewrapped@gmail.com<br>"
                              '<a href="https://github.com/machinewrapped/gpt-subtrans">GitHub Repository</a><br>'
                              'Thanks to all contributors and those who have reported issues.')
        author_label.setOpenExternalLinks(True)
        author_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        # License information
        license_text = QLabel("GUI-Subtrans is released under the MIT License.\n\n"
                             "Permission is hereby granted, free of charge, to any person obtaining a copy "
                             "of this software and associated documentation files, to deal in the software "
                             "without restriction, including without limitation the rights to use, copy, "
                             "modify, merge, publish, distribute, sublicense, and/or sell copies of the software.")
        license_text.setWordWrap(True)
        
        # Libraries and their versions
        libraries = ["openai", "srt", "pyside6", "regex", "events", "darkdetect", "appdirs", "python-dotenv"]
        library_strings = []

        for lib in libraries:
            try:
                version = pkg_resources.get_distribution(lib).version
                library_strings.append(f"{lib} ({version})")
            except pkg_resources.DistributionNotFound:
                library_strings.append(lib)

        libraries_list = QLabel("GUI-Subtrans would not work without these libraries:\n" + ", ".join(library_strings))
        libraries_list.setWordWrap(True)
        
        # OK Button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addWidget(author_label)
        layout.addWidget(license_text)
        layout.addWidget(libraries_list)
        layout.addWidget(button_box)

        # Add right side layout to the main layout
        main_layout.addLayout(layout)

        # Set the main layout for the dialog
        self.setLayout(main_layout)
