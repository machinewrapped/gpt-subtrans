import os

from typing import List

import regex
from PySubtitle.SubtitleError import SubtitleError

def GetEnvBool(key, default=False):
    """
    Get a boolean value from an environment variable
    """
    var = os.getenv(key, default)
    if var is not None:
        return str(var).lower() in ('true', 'yes', '1')
    return default

def GetEnvFloat(name, default=None):
    """
    Get a float value from an environment variable
    """
    value = os.getenv(name, default)
    if value is not None:
        return float(value)
    return default

def GetEnvInteger(name, default=None):
    """
    Get an integer value from an environment variable
    """
    value = os.getenv(name, default)
    if value is not None:
        return int(value)
    return default

def GetValueName(value):
    """
    Get the name of an object if it has one, or a string representation of the object.
    Then, if the name is in CamelCase, insert spaces between each word.
    """
    name = getattr(value, 'name', str(value))

    # Insert spaces before all caps in CamelCase (but not at the start)
    spaced_name = regex.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)

    return spaced_name

def GetValueFromName(name, values, default=None):
    """
    Get the value from a name in a list of values
    """
    for value in values:
        if str(name) == str(value) or name == GetValueName(value):
            return value

    if default is not None:
        return default

    raise ValueError(f"Value '{name}' not found in {values}")

def UpdateFields(item : dict, update: dict, fields : list[str]):
    """
    Patch selected fields in a dictionary
    """
    if not isinstance(item, dict) or not isinstance(update, dict):
        raise ValueError(f"Can't patch a {type(item).__name__} with a {type(update).__name__}")

    item.update({field: update[field] for field in update.keys() if field in fields})

def GetInputPath(filepath):
    if not filepath:
        return None

    basename, _ = os.path.splitext(os.path.basename(filepath))
    if basename.endswith("-ChatGPT"):
        basename = basename[0:basename.index("-ChatGPT")]
    if basename.endswith("-GPT"):
        basename = basename[0:basename.index("-GPT")]
    path = os.path.join(os.path.dirname(filepath), f"{basename}.srt")
    return os.path.normpath(path)

def GetOutputPath(filepath, language="translated"):
    if not filepath:
        return None

    basename, _ = os.path.splitext(os.path.basename(filepath))

    if basename.endswith("-ChatGPT"):
        basename = basename[0:basename.index("-ChatGPT")]
    if basename.endswith("-GPT"):
        basename = basename[0:basename.index("-GPT")]
    language_suffix = f".{language}"
    if not basename.endswith(language_suffix):
        basename = basename + language_suffix

    return os.path.join(os.path.dirname(filepath), f"{basename}.srt")

def FormatMessages(messages):
    lines = []
    for index, message in enumerate(messages, start=1):
        lines.append(f"Message {index}")
        if 'role' in message:
            lines.append(f"Role: {message['role']}")
        if 'content' in message:
            content = message['content'].replace('\\n', '\n')
            lines.extend(["--------------------", content])
        lines.append("")

    return '\n'.join(lines)

def FormatErrorMessages(errors : List[SubtitleError]):
    """
    Extract error messages from a list of errors
    """
    return ", ".join([ error.message for error in errors ])