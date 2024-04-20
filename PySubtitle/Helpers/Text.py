import unicodedata
import regex

def RemoveWhitespaceAndPunctuation(string) -> str:
    """
    Remove all whitespace and punctuation from a string
    """
    # Matches any punctuation, separator, or other Unicode character
    pattern = r'[\p{P}\p{Z}\p{C}]'
    stripped = regex.sub(pattern, '', string)

    # Normalize Unicode characters to their canonical forms
    normalized = unicodedata.normalize('NFC', stripped)

    return normalized

def IsTextContentEqual(string1 : str, string2 : str) -> bool:
    """
    Compare two strings for equality, ignoring whitespace and punctuation
    """
    if string1 and string2:
        stripped1 = RemoveWhitespaceAndPunctuation(string1)
        stripped2 = RemoveWhitespaceAndPunctuation(string2)
        return stripped1 == stripped2

    return string1 == string2

def Linearise(lines : str | list[str]) -> str:
    """
    Ensure that the input is a single string
    """
    if not isinstance(lines, list):
        lines = str(lines).split("\n")

    lines = [ str(line).strip() for line in lines ]
    return " | ".join(lines)

def ConvertWhitespaceBlocksToNewlines(text) -> str:
    """
    Convert blocks of 3 or more spaces or chinese commas to newlines, unless the text contains newlines already
    """
    if text and '\n' not in text:
        text = regex.sub(r' {3,}|\，\s*', '\n', text)

    return text

def BreakDialogOnOneLine(text : str, dialog_marker : str) -> str:
    """
    Break dialog into separate lines
    """
    # Split line at dialog markers following any non-alphanumeric character and whitespace
    # This should catch the majority of genuine dialog markers and few other uses of a dash
    # Uses a look-behind followed by a look-ahead so that the split point is not consumed
    escaped_marker = regex.escape(dialog_marker)
    re_split = r"(?<=[^a-zA-Z0-9]\s*)(?=" + escaped_marker + ")"
    line_parts = regex.split(re_split, text)

    if len(line_parts) > 1:
        text = '\n'.join([part.strip() for part in line_parts])

    return text

def NormaliseDialogTags(text : str, dialog_marker : str) -> str:
    """
    Make sure dialog markers are consistent across lines
    """
    if not dialog_marker in text:
        return text

    line_parts = text.split('\n')

    # If a single line starts with a dialog marker, remove it
    if len(line_parts) == 1 and text.startswith(dialog_marker):
        return text[len(dialog_marker):].strip()

    # If any of the line parts starts with a dialog marker, they all should
    if any(part.startswith(dialog_marker) for part in line_parts):
        line_parts = [part if part.startswith(dialog_marker) else dialog_marker + part for part in line_parts]
        text = '\n'.join(part.strip() for part in line_parts)

    return text

def LimitTextLength(text : str, max_length : int) -> str:
    """
    Limit the length of a text string to a maximum number of characters, cutting at the nearest sentence end or whitespace
    """
    text = text.strip()

    if len(text) <= max_length:
        return text

    pattern = r'\.|\?|!'
    matches = [(m.start(), m.group()) for m in regex.finditer(pattern, text)]

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

def ContainsTags(text : str) -> bool:
    """
    Check if a line contains any html-like tags (<i>, <b>, etc.)
    """
    return regex.search(r"<[^>]+>", text) is not None

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
        raise ValueError(f"Malformed {tagname} tags in {text}")

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
