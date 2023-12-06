from PySubtitle.SubtitleError import TranslationError
from PySubtitle.SubtitleLine import SubtitleLine

class TranslationPrompt:
    def __init__(self, instructions):
        self.user_prompt = None
        self.messages = []
        self.instructions = instructions
        
    def GenerateMessages(self, prompt, lines, context):
        raise NotImplementedError("Not implemented in the base class")

    def GenerateRetryPrompt(self, reponse : str, retry_instructions : str, errors : list[TranslationError]):
        raise NotImplementedError("Not implemented in the base class")

    def GenerateBatchPrompt(self, prompt : str, lines : list[SubtitleLine], tag_lines=None):
        """
        Create the user prompt for translating a set of lines

        :param tag_lines: optional list of extra lines to include at the top of the prompt.
        """
        source_lines = [ self.GetLinePrompt(line) for line in lines ]
        source_text = '\n\n'.join(source_lines)
        text = f"\n{source_text}\n\n<summary></summary>\n<scene></scene>"

        if prompt:
            text = f"{prompt}\n\n{text}"

        if tag_lines:
            text = f"<context>\n{tag_lines}\n{text}</context>"

        return text

    def GetLinePrompt(self, line):
        if not line._item:
            return None
        
        return '\n'.join([
            f"#{line.number}",
            "Original>",
            line.text_normalized,
            "Translation>"
        ])

