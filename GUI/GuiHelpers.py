import os
import sys

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
    files = os.listdir(instruction_path)
    return [ file for file in files if file.lower().startswith("instructions") ]

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