from datetime import timedelta
import logging
import os
import darkdetect

from srt import timedelta_to_srt_timestamp
from PySide6.QtWidgets import (QApplication, QFormLayout)

from PySubtitle.Helpers.resources import GetResourcePath

def GetThemeNames():
    themes = []
    theme_path = GetResourcePath("theme")
    for file in os.listdir(theme_path):
        if file.endswith(".qss"):
            theme_name = os.path.splitext(file)[0]
            themes.append(theme_name)

    themes.sort()
    return themes 

def LoadStylesheet(name):
    if not name or name == "default":
        name = "subtrans-dark" if darkdetect.isDark() else "subtrans"

    filepath = GetResourcePath("theme", f"{name}.qss")
    logging.info(f"Loading stylesheet from {filepath}")
    with open(filepath, 'r') as file:
        stylesheet = file.read()
    QApplication.instance().setStyleSheet(stylesheet)
    return stylesheet

def GetLineHeight(text: str, wrap_length: int = 60) -> int:
    """
    Calculate the number of lines for a given text with wrapping and newline characters.

    :param text: The input text.
    :param wrap_length: The maximum number of characters per line.
    :return: The total number of lines.
    """
    if not text:
        return 0

    wraps = -(-len(text) // wrap_length) if wrap_length else None  # Ceiling division
    return text.count('\n') + wraps

def TimeDeltaToText(time: timedelta) -> str:
    return timedelta_to_srt_timestamp(time).replace('00:', '') if time is not None else None

def DescribeLineCount(line_count, translated_count):
    if translated_count == 0:
        return f"{line_count} lines" 
    elif line_count == translated_count:
        return f"{translated_count} lines translated" 
    else:
        return f"{translated_count} of {line_count} lines translated"

def ClearForm(layout : QFormLayout):
    """
    Clear the widgets from a layout
    """
    while layout.rowCount():
        row = layout.takeRow(0)
        if row.fieldItem:
            widget = row.fieldItem.widget()
            if widget:
                widget.deleteLater()
        if row.labelItem:
            widget = row.labelItem.widget()
            if widget:
                widget.deleteLater()