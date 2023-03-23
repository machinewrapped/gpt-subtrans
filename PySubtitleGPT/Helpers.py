import logging
import re

from PySubtitleGPT.Subtitle import Subtitle

def Linearise(lines):
    if isinstance(lines, list):
        lines = " | ".join(lines)
    lines = [line.strip() for line in str(lines).split("\n")]
    return " | ".join(lines)

def GetSubtitles(lines):
    """
    (re)parse the lines as subtitles, assuming SubRip format 
    """
    if all(isinstance(line, Subtitle) for line in lines):
        return lines
    else:
        return [Subtitle(line) for line in lines]

def GetLineItems(lines, tag):
    """
    Generate a set of translation lines for the translator
    """
    items = GetSubtitles(lines)
    return [GetLineItem(item, tag) for item in items]

def GetLineItem(item, tag):
    """
    Generate the translation prompt line for a subtitle
    """
    line = f"<{tag} line={item.index}>{item.text}</{tag}>"
    return line

def GenerateBatchPrompt(prompt, lines, tag_lines=None):
    """
    Create the user prompt for translating a set of lines

    :param tag_lines: optional list of extra lines to include at the top of the prompt.
    """
    source_lines = [ line.prompt for line in lines ]
    source_text = '\n\n'.join(source_lines)
    if tag_lines:
        return f"{tag_lines}\n----------\n{prompt}\n\n----------\n{source_text}\n"
    else:
        return f"{prompt}\n\n----------\n{source_text}\n"

def GenerateTagLines(context, tags):
    """
    Create a user message for specifying a set of tags

    :param context: dictionary of tag, value pairs
    :param tags: list of tags to extract from the context.
    """
    tag_lines = [ GenerateTag(tag, context.get(tag,'')) for tag in tags ]

    if tag_lines:
        return '\n'.join([tag.strip() for tag in tag_lines if tag.strip()])
    else:
        return None

def GenerateTag(tag, content):
    return f"<{tag}>{content}</{tag}>"

def BuildPrompt(options):
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
    text, characters = ExtractTag("characters", text)

    return text, summary, synopsis, characters

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

def MergeTranslations(subtitles, translated):
    """
    Replace lines in subtitles with corresponding lines in translated
    """
    subtitle_dict = {item.key: item for item in subtitles}

    for item in translated:
        subtitle_dict[item.key] = item

    subtitles = sorted(subtitle_dict.values(), key=lambda item: item.start)

    return subtitles

def UnbatchScenes(scenes):
    """
    Reconstruct a sequential subtitle from multiple scenes
    """
    subtitles = []
    translations = []
    untranslated = []

    for i_scene, scene in enumerate(scenes):
        for i_batch, batch in enumerate(scene.batches):
            batch_subtitles = batch.subtitles if batch.subtitles else []
            batch_translations = batch.translated if batch.translated else []
            batch_untranslated = batch.untranslated if batch.untranslated else []

            subtitles.extend(batch_subtitles)
            translations.extend(batch_translations)
            untranslated.extend(batch_untranslated)
    
    # Renumber
    for index, line in enumerate(translations):
        line.index = index + 1

    return subtitles, translations, untranslated

def ParseSubstitutions(sub_list, separator="::"):
    """
    :param sub_list: is assumed to be a list of (before,after) pairs 
    separated by the separator ("::" by default).

    :return: a dictionary of (before,after) pairs
    :rtype dict:
    """
    if not sub_list:
        return {}
    
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
        pattern = fr"((?<=\W)|^){re.escape(before)}((?=\W)|$)"
        result = re.sub(pattern, after, result)
        
    return result