from PySubtitle.Options import Options

def _GetLinePrompt(line):
    if not line._item:
        return None

    return '\n'.join([
        f"#{line.number}",
        "Original>",
        line.text_normalized,
        "Translation>"
    ])

def BuildUserPrompt(options : Options):
    """
    Generate the base prompt to use for requesting translations
    """
    target_language = options.get('target_language')
    movie_name = options.get('movie_name')
    prompt = options.get('prompt')
    prompt = prompt.replace('[ to language]', f" to {target_language}" if target_language else "")
    prompt = prompt.replace('[ for movie]', f" for {movie_name}" if movie_name else "")

    for k,v in options.options.items():
        if v:
            prompt = prompt.replace(f"[{k}]", str(v))
    return prompt

def GenerateBatchPrompt(prompt : str, lines, tag_lines=None):
    """
    Create the user prompt for translating a set of lines

    :param tag_lines: optional list of extra lines to include at the top of the prompt.
    """
    source_lines = [ _GetLinePrompt(line) for line in lines ]
    source_text = '\n\n'.join(source_lines)
    text = f"\n{source_text}\n\n<summary>Summary of the batch</summary>\n<scene>Summary of the scene</scene>"

    if prompt:
        text = f"{prompt}\n\n{text}"

    if tag_lines:
        text = f"<context>\n{tag_lines}\n</context>\n\n{text}"

    return text