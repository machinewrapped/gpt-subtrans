from PySubtitle.Options import Options
from typing import Optional

def _GetLinePrompt(line):
    if not line._item:
        return None

    return '\n'.join([
        f"#{line.number}",
        "Original>",
        line.text_normalized,
        "Translation>"
    ])

def _GenerateTag(tag, content) -> str:
    """ Generate html-style tag with content """
    if isinstance(content, list):
        content = ', '.join(content)

    return f"<{tag}>{content}</{tag}>"

def GenerateTagLines(context, tags) -> Optional[str]:
    """
    Create a user message for specifying a set of tags

    :param context: dictionary of tag, value pairs
    :param tags: list of tags to extract from the context.
    """
    tag_lines = [ _GenerateTag(tag, context.get(tag,'')) for tag in tags if context.get(tag) ]

    if tag_lines:
        return '\n'.join([tag.strip() for tag in tag_lines if tag.strip()])
    else:
        return None

def BuildUserPrompt(options : Options) -> str:
    """
    Generate the base prompt to use for requesting translations
    """
    target_language = options.get('target_language')
    movie_name = options.get('movie_name')
    prompt = options.get('prompt', "Translate these subtitles [ for movie][ to language]")
    prompt = prompt.replace('[ to language]', f" to {target_language}" if target_language else "")
    prompt = prompt.replace('[ for movie]', f" for {movie_name}" if movie_name else "")

    for k,v in options.options.items():
        if v:
            prompt = prompt.replace(f"[{k}]", str(v))

    return prompt.strip()

def GenerateBatchPrompt(user_prompt : str, lines : list, context : dict = None, template : str = None):
    """
    Create the user prompt for translating a set of lines

    :param tag_lines: optional list of extra lines to include at the top of the prompt.
    :param template: optional template to format the prompt.
    """
    source_lines = [ _GetLinePrompt(line) for line in lines ]
    text = '\n\n'.join(source_lines).strip()

    if not text:
        raise ValueError("No source text provided")

    prompt = f"{user_prompt}\n\n{text}\n" if user_prompt else text

    tag_lines = GenerateTagLines(context, ['description', 'names', 'history', 'scene', 'summary', 'batch']) if context else ""

    if not template:
        template = "<context>{context}</context>\n\n{prompt}" if tag_lines else "{prompt}"

    text = template.format(prompt=prompt, context=tag_lines)

    return text
