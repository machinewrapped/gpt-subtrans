
import os
import sys
import appdirs

config_dir = appdirs.user_config_dir("GPTSubtrans", "MachineWrapped", roaming=True)

def GetResourcePath(relative_path, *parts):
    """
    Locate a resource file or folder in the application directory or the PyInstaller bundle.
    """
    if hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path, *parts)

    return os.path.join(os.path.abspath("."), relative_path or "", *parts)

