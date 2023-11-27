import logging

from PySubtitleGPT.Helpers import GenerateTag, GenerateTagLines
from PySubtitleGPT.SubtitleError import TranslationError
from PySubtitleGPT.SubtitleLine import SubtitleLine

class ChatGPTPrompt:
    def __init__(self, instructions):
        self.user_prompt = None
        self.messages = []
        self.instructions = instructions
        
    def GenerateMessages(self, prompt, lines, context):
        if self.instructions:
            self.messages.append({'role': "system", 'content': self.instructions})

        if context:
            context_tags = GenerateTagLines(context, ['description', 'characters'])
            if context_tags:
                self.messages.append({'role': "user", 'content': context_tags})

            summaries = context.get('summaries')
            if summaries:
                self.messages.append({'role': "user", 'content': '\n'.join(summaries)})

            tag_lines = GenerateTagLines(context, ['scene', 'summary', 'batch'])

            self.user_prompt = self.GenerateBatchPrompt(prompt, lines, tag_lines)

        else:
            self.user_prompt = self.GenerateBatchPrompt(prompt, lines)

        self.messages.append({'role': "user", 'content': self.user_prompt})

    def GenerateRetryPrompt(self, reponse : str, retry_instructions : str, errors : list[TranslationError]):
        """
        Request retranslation of lines that were not translated originally
        """
        if errors:
            unique_errors = set(( f"- {str(e).strip()}" for e in errors ))
            error_list = list(unique_errors)
            error_message = '\n'.join(error_list)
            retry_prompt = f"There were some problems with the translation:\n{error_message}\n\nPlease correct them."
        else:
            # Maybe less is more?
            retry_prompt = 'Please try again'

        self.messages.extend([
            { 'role': "assistant", 'content': reponse },
            { 'role': "system", 'content': retry_instructions },
            { 'role': "user", 'content': retry_prompt }
        ])

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

