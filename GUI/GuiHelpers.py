from datetime import timedelta
import logging
import os
import sys

from srt import timedelta_to_srt_timestamp
from PySide6.QtWidgets import (QFormLayout)

from PySubtitle.Instructions import Instructions

def GetResourcePath(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path or "")

def GetThemeNames():
    themes = []
    theme_path = GetResourcePath("theme")
    for file in os.listdir(theme_path):
        if file.endswith(".qss"):
            theme_name = os.path.splitext(file)[0]
            themes.append(theme_name)

    themes.sort()
    return themes 

def GetInstructionFiles():
    instruction_path = GetResourcePath("")
    logging.debug(f"Looking for instruction files in {instruction_path}")
    files = os.listdir(instruction_path)
    return [ file for file in files if file.lower().startswith("instructions") ]

def LoadInstructionsResource(resource_name):
    filepath = GetResourcePath(resource_name)
    logging.debug(f"Loading instructions from {filepath}")
    instructions = Instructions({})
    instructions.LoadInstructionsFile(filepath)
    return instructions

def GetLineHeight(text: str, wrap_length: int = 100) -> int:
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