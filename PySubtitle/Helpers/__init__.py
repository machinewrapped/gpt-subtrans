import datetime
import os
import logging
import regex
import srt

from typing import List
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

def UpdateFields(item : dict, update: dict, fields : list[str]):
    """
    Patch selected fields in a dictionary
    """
    if not isinstance(item, dict) or not isinstance(update, dict):
        raise ValueError(f"Can't patch a {type(item).__name__} with a {type(update).__name__}")

    item.update({field: update[field] for field in update.keys() if field in fields})

def CreateSrtSubtitle(item) -> srt.Subtitle:
    """
    Try to construct an srt.Subtitle from the argument
    """
    if hasattr(item, 'item'):
        item = item.item

    if not isinstance(item, srt.Subtitle):
        line = str(item).strip()
        match = srt.SRT_REGEX.match(line)
        if match:
            raw_index, raw_start, raw_end, proprietary, content = match.groups()
            index = int(raw_index) if raw_index else None
            start = srt.srt_timestamp_to_timedelta(raw_start)
            end = srt.srt_timestamp_to_timedelta(raw_end)
            item = srt.Subtitle(index, start, end, content, proprietary)

    return item

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

def MergeTranslations(lines, translated):
    """
    Replace lines with corresponding lines in translated
    """
    line_dict = {item.key: item for item in lines if item.key}

    for item in translated:
        line_dict[item.key] = item

    lines = sorted(line_dict.values(), key=lambda item: item.key)

    return lines

def UnbatchScenes(scenes):
    """
    Reconstruct a sequential subtitle from multiple scenes
    """
    originals = []
    translations = []
    untranslated = []

    for i_scene, scene in enumerate(scenes):
        for i_batch, batch in enumerate(scene.batches):
            batch_originals = batch.originals if batch.originals else []
            batch_translations = batch.translated if batch.translated else []
            batch_untranslated = batch.untranslated if batch.untranslated else []

            originals.extend(batch_originals)
            translations.extend(batch_translations)
            untranslated.extend(batch_untranslated)

    return originals, translations, untranslated

def ResyncTranslatedLines(original_lines, translated_lines):
    """
    Copy number, start and end from original lines to matching translated lines.
    """
    num_original = len(original_lines)
    num_translated = len(translated_lines)
    min_lines = min(num_original, num_translated)

    for i in range(min_lines):
        translated_lines[i].start = original_lines[i].start
        translated_lines[i].end = original_lines[i].end
        translated_lines[i].number = original_lines[i].number

    if num_original < num_translated:
        logging.warning(f"Number of translated lines exceeds the number of original lines. "
                        f"Removed {num_translated - num_original} extra translated lines.")
        del translated_lines[num_original:]

    elif num_original > num_translated:
        logging.warning(f"Number of lines in original and translated subtitles don't match. Synced {min_lines} lines.")

def TimeDeltaToText(time: datetime.timedelta) -> str:
    """
    Convert a timedelta to a string
    """
    return srt.timedelta_to_srt_timestamp(time).replace('00:', '') if time is not None else None

def GetTimeDelta(time : datetime.timedelta | str | None) -> datetime.timedelta:
    """
    Ensure the input value is a timedelta, as best we can
    """
    if time is None:
        return None

    if isinstance(time, datetime.timedelta):
        return time

    try:
        return srt.srt_timestamp_to_timedelta(str(time))

    except Exception as e:
        time = str(time).strip()
        parts = regex.split('[:,]', time)

        if len(parts) == 3:
            if len(parts[-1]) == 3:
                logging.warning(f"Adding hour to time '{time}'")
                return GetTimeDelta(f"00:{parts[0]}:{parts[1]},{parts[2]}")
            else:
                logging.warning(f"Adding milliseconds to time '{time}'")
                return GetTimeDelta(f"{parts[0]}:{parts[1]}:{parts[2],000}")

        if len(parts) >= 4:
            if len(parts[-1]) == 3:
                logging.warning(f"Using last four parts of '{time}' as time")
                return GetTimeDelta(f"{parts[-4]}:{parts[-3]}:{parts[-2]},{parts[-1]}")

            logging.warning(f"Using first four parts of '{time}' as time")
            return GetTimeDelta(f"{parts[0]}:{parts[1]}:{parts[2]},{parts[3]}")

    raise ValueError(f"Unable to interpret time '{str(time)}'")

def ParseDelayFromHeader(value : str):
    """
    Try to figure out how long a suggested retry-after is
    """
    if not isinstance(value, str):
        return 12.3

    match = regex.match(r"([0-9\.]+)(\w+)?", value)
    if not match:
        return 32.1

    try:
        delay, unit = match.groups()
        delay = float(delay)
        unit = unit.lower() if unit else 's'
        if unit == 's':
            pass
        elif unit == 'm':
            delay *= 60
        elif unit == 'ms':
            delay /= 1000

        return max(1, delay)  # ensure at least 1 second

    except Exception as e:
        logging.error(f"Unexpected time value '{value}'")
        return 6.66

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