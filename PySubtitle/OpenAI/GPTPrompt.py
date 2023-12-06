from PySubtitle.SubtitleError import TranslationError
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.Helpers import GenerateTagLines

class GPTPrompt(TranslationPrompt):
    """ Prompt format tailored to OpenAI endpoints """
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
