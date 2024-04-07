import datetime
import os
import logging
import re
import regex
import unicodedata
import srt
from typing import List
from PySubtitle.SubtitleError import SubtitleError

def GetEnvBool(key, default=False):
    var = os.getenv(key, default)
    if var is not None:
        return str(var).lower() in ('true', 'yes', '1')
    return default

def GetEnvFloat(name, default=None):
    value = os.getenv(name, default)
    if value is not None:
        return float(value)
    return default

def GetEnvInteger(name, default=None):
    value = os.getenv(name, default)
    if value is not None:
        return int(value)
    return default

def Linearise(lines):
    if not isinstance(lines, list):
        lines = str(lines).split("\n")

    lines = [ str(line).strip() for line in lines ]
    return " | ".join(lines)

def UpdateFields(item : dict, update: dict, fields : list[str]):
    """
    Patch selected fields in a dictionary
    """
    if not isinstance(item, dict) or not isinstance(update, dict):
        raise ValueError(f"Can't patch a {type(item).__name__} with a {type(update).__name__}")

    item.update({field: update[field] for field in update.keys() if field in fields})

def CreateSrtSubtitle(item):
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

def GetTimeDelta(time):
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

def WrapSystemMessage(message : str):
    separator = "--------"
    return '\n'.join( [ separator, "SYSTEM", separator, message.strip(), separator])

def ParseTranslation(text):
    """
    Unpack a response from Chat GPT
    """
    text, summary = ExtractTag("summary", text)
    text, synopsis = ExtractTag("synopsis", text)
    text, scene = ExtractTag("scene", text)
    text, names = ExtractTagList("names", text)

    context = {
        'summary': summary,
        'scene': scene,
        'synopsis': synopsis,
        'names': names
    }
    return text, context

def ExtractTag(tagname : str, text : str):
    """
    Look for an xml-like tag in the input text, and extract the contents.
    """
    open_tag = f"<{tagname}>"
    close_tag = f"</{tagname}>"
    empty_tag = f"<{tagname}/>"

    text = text.replace(empty_tag, '')

    end_index = text.rfind(close_tag)

    if end_index == -1:
        return text.strip(), None

    start_index = text.rfind(open_tag, 0, end_index)
    if start_index == -1:
        #raise ValueError(f"Malformed {tagname} tags in response")
        logging.warning(f"Malformed {tagname} tags in response")
        return text.strip(), None

    tag = text[start_index + len(open_tag):end_index].strip()
    text_before = text[:start_index].strip()
    text_after = text[end_index + len(close_tag):].strip()
    text = '\n'.join([text_before, text_after]).strip()

    return text, tag

def ExtractTagList(tagname, text):
    """
    Look for an xml-like tag in the input text, and extract the contents as a comma or newline separated list.
    """
    text, tag = ExtractTag(tagname, text)
    tag_list = [ item.strip() for item in regex.split("[\n,]", tag) ] if tag else []
    return text, tag_list

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


def RemoveEmptyLines(lines):
    return [line for line in lines if line.text and line.text.strip()]

def RemoveWhitespaceAndPunctuation(string):
    # Matches any punctuation, separator, or other Unicode character
    pattern = r'[\p{P}\p{Z}\p{C}]'
    stripped = regex.sub(pattern, '', string)

    # Normalize Unicode characters to their canonical forms
    normalized = unicodedata.normalize('NFC', stripped)
    return normalized

def IsTextContentEqual(string1 : str, string2 : str):
    if string1 and string2:
        stripped1 = RemoveWhitespaceAndPunctuation(string1)
        stripped2 = RemoveWhitespaceAndPunctuation(string2)
        return stripped1 == stripped2

    return string1 == string2

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

def LimitTextLength(text, max_length):
    text = text.strip()

    if len(text) <= max_length:
        return text

    pattern = r'\.|\?|!'
    matches = [(m.start(), m.group()) for m in re.finditer(pattern, text)]

    # Find the closest match to the max length, if any
    for position, match in reversed(matches):
        if position <= max_length:
            return text[:position + 1]

    # If no sentence end is found within the limit, cut at the nearest whitespace
    nearest_space = text.rfind(' ', 0, max_length)
    if nearest_space != -1:
        return text[:nearest_space] + '...'
    else:
        # As a last resort, cut directly at the max length
        return text[:max_length] + '...'

def SanitiseSummary(summary : str, movie_name : str = None, max_summary_length : int = None):
    """
    Remove trivial parts of summary text
    """
    if not summary:
        return None

    summary = re.sub(r'^(?:(?:Scene|Batch)[\s\d:\-]*)+', '', summary, flags=re.IGNORECASE)
    summary = summary.replace("Summary of the batch", "")
    summary = summary.replace("Summary of the scene", "")

    if movie_name:
        # Remove movie name and any connectors (-,: or whitespace)
        summary = re.sub(r'^' + re.escape(movie_name) + r'\s*[:\-]\s*', '', summary)

    summary = summary.strip()
    original_len = len(summary)

    if max_summary_length:
        summary = LimitTextLength(summary, max_summary_length)

    if len(summary) != original_len:
        logging.info(f"Summary was truncated from {original_len} to {len(summary)} characters")

    return summary or None

def FormatErrorMessages(errors : List[SubtitleError]):
    """
    Extract error messages from a list of errors
    """
    return ", ".join([ error.message for error in errors ])