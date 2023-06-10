import os
import sys

def GetResourcePath(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def GetThemeNames():
    themes = []
    theme_path = GetResourcePath("theme")
    for file in os.listdir(theme_path):
        if file.endswith(".qss"):
            theme_name = os.path.splitext(file)[0]
            themes.append(theme_name)

    themes.sort()
    return themes 


