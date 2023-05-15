import logging

from PySubtitleGPT.Helpers import GenerateTag, GenerateTagLines, GenerateBatchPrompt
from PySubtitleGPT.SubtitleError import TranslationError

class ChatGPTPrompt:
    def __init__(self, instructions):
        self.user_prompt = None
        self.messages = []
        self.instructions = instructions
        
    def GenerateMessages(self, prompt, lines, context):
        if self.instructions:
            self.messages.append({'role': "system", 'content': self.instructions})

        if context:
            context_tags = GenerateTagLines(context, ['synopsis', 'characters'])
            if context_tags:
                self.messages.append({'role': "user", 'content': context_tags})

            # previous_batch = context.get('previous_batch')
            # if previous_batch:
            #     previous_originals = previous_batch.originals
            #     previous_lines = [ line.prompt for line in previous_originals ]
            #     user_previous = linesep.join(previous_lines)
            #     self.messages.append({'role': "assistant", 'content': user_previous})

            summaries = context.get('summaries')
            if summaries:
                tags = ( GenerateTag('summary', summary) for summary in summaries )
                self.messages.append({'role': "assistant", 'content': " ... ".join(tags)})

            tag_lines = GenerateTagLines(context, ['scene', 'summary'])

            self.user_prompt = GenerateBatchPrompt(prompt, lines, tag_lines)

        else:
            self.user_prompt = GenerateBatchPrompt(prompt, lines)

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


