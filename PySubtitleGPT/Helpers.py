import datetime
import os
import logging
import regex
import unicodedata
import srt

from PySubtitleGPT.Options import Options

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
        raise Exception(f"Can't patch a {type(item).__name__} with a {type(update).__name__}")

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
    if not time:
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
                logging.warn(f"Adding hour to time '{time}'")
                return GetTimeDelta(f"00:{parts[0]}:{parts[1]},{parts[2]}")
            else:
                logging.warn(f"Adding milliseconds to time '{time}'")
                return GetTimeDelta(f"{parts[0]}:{parts[1]}:{parts[2],000}")

        if len(parts) >= 4:
            if len(parts[-1]) == 3:
                logging.warn(f"Using last four parts of '{time}' as time")
                return GetTimeDelta(f"{parts[-4]}:{parts[-3]}:{parts[-2]},{parts[-1]}")

            logging.warn(f"Using first four parts of '{time}' as time")
            return GetTimeDelta(f"{parts[0]}:{parts[1]}:{parts[2]},{parts[3]}")

    raise ValueError(f"Unable to interpret time '{str(time)}'")

def GetInputPath(filepath):
    if not filepath:
        return None
    
    basename, _ = os.path.splitext(os.path.basename(filepath))
    if basename.endswith("-ChatGPT"):
        basename = basename[0:basename.index("-ChatGPT")]
    return os.path.join(os.path.dirname(filepath), f"{basename}.srt")

def GetOutputPath(filepath):
    if not filepath:
        return None
    
    basename, _ = os.path.splitext(os.path.basename(filepath))
    if not basename.endswith("-ChatGPT"):
        basename = basename + "-ChatGPT"
    return os.path.join(os.path.dirname(filepath), f"{basename}.srt")

def GenerateTagLines(context, tags):
    """
    Create a user message for specifying a set of tags

    :param context: dictionary of tag, value pairs
    :param tags: list of tags to extract from the context.
    """
    tag_lines = [ GenerateTag(tag, context.get(tag,'')) for tag in tags if context.get(tag) ]

    if tag_lines:
        return '\n'.join([tag.strip() for tag in tag_lines if tag.strip()])
    else:
        return None

def GenerateTag(tag, content):
    if isinstance(content, list):
        content = ', '.join(content)

    return f"<{tag}>{content}</{tag}>"

def BuildPrompt(options : Options):
    """
    Generate the base prompt to use for requesting translations
    """
    target_language = options.get('target_language')
    movie_name = options.get('movie_name')
    prompt = options.get('gpt_prompt')
    prompt = prompt.replace('[ to language]', f" to {target_language}" if target_language else "")
    prompt = prompt.replace('[ for movie]', f" for {movie_name}" if movie_name else "")
    options.add('prompt', prompt)
    return prompt

def ParseTranslation(text):
    """
    Unpack a response from Chat GPT
    """
    text, summary = ExtractTag("summary", text)
    text, synopsis = ExtractTag("synopsis", text)
    text, scene = ExtractTag("scene", text)
    text, characters = ExtractTagList("characters", text)

    context = {
        'summary': summary,
        'scene': scene,
        'synopsis': synopsis,
        'characters': characters
    }

    return text, context 

def ExtractTag(tagname, text):
    """
    Look for an xml-like tag in the input text, and extract the contents.
    """
    open_tag = f"<{tagname}>"
    close_tag = f"</{tagname}>"

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

def ParseCharacters(character_list):
    if isinstance(character_list, str):
        character_list = regex.split("[\n,]", character_list)

    if isinstance(character_list, list):
        return [ name.strip() for name in character_list ]
    
    return []


def ParseSubstitutions(sub_list, separator="::"):
    """
    :param sub_list: is assumed to be a list of (before,after) pairs 
    separated by the separator ("::" by default).

    :return: a dictionary of (before,after) pairs
    :rtype dict:
    """
    if not sub_list:
        return {}
    
    if isinstance(sub_list, dict):
        return sub_list

    if isinstance(sub_list, str):
        sub_list = regex.split("[\n,]", sub_list)

    if isinstance(sub_list, list):
        substitutions = {}
        for sub in sub_list:
            if "::" in sub:
                before, after = sub.split(separator)
                substitutions[before] = after
            else:
                try:
                    with open(sub, "r", encoding="utf-8") as f:
                        for line in [line.strip() for line in f if line.strip()]:
                            if "::" in line:
                                before, after = line.split("::")
                                substitutions[before] = after
                            else:
                                raise ValueError(f"Invalid substitution format in {sub}: {line}")
                except FileNotFoundError:
                    logging.warning(f"Substitution file not found: {sub}")
                except ValueError:
                    raise
        
        return substitutions

    return {}

def PerformSubstitutions(substitutions, input):
    """
    :param input: If input is string-like, attempt to substitute all (before,after) pairs 
    in substitutions. If input is a list, iterate over all elements performing substitutions.
    
    :return: If input is string-like, return a string with the substitutions.
    If input is a list, return a list of strings along with a dictionary of (before,after) pairs
    for each elements that had one or more substitutions. 
    """
    substitutions = substitutions if substitutions else {}

    if isinstance(input, list):
        new_list = [ PerformSubstitutions(substitutions, line) for line in input ]
        replacements = { line: new_line for line, new_line in zip(input, new_list) if new_line != str(line) }
        return new_list, replacements

    result = str(input)
    for before, after in substitutions.items():
        pattern = fr"((?<=\W)|^){regex.escape(before)}((?=\W)|$)"
        result = regex.sub(pattern, after, result)
        
    return result


def RemoveWhitespaceAndPunctuation(string):
    # Matches any punctuation, separator, or other Unicode character
    pattern = r'[\p{P}\p{Z}\p{C}]'
    stripped = regex.sub(pattern, '', string)

    # Normalize Unicode characters to their canonical forms
    normalized = unicodedata.normalize('NFC', stripped)
    return normalized

def IsTextContentEqual(string1 : str, string2 : str):
    stripped1 = RemoveWhitespaceAndPunctuation(string1)
    stripped2 = RemoveWhitespaceAndPunctuation(string2)
    return stripped1 == stripped2

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
