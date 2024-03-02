from PySubtitle.SubtitleError import TranslationError
from PySubtitle.TranslationPrompt import TranslationPrompt
from PySubtitle.Helpers import GenerateBatchPrompt, GenerateTagLines

class GeminiPrompt(TranslationPrompt):
    """ Prompt format tailored to Gemini """
    def GenerateMessages(self, prompt, lines, context):
        """
        Generate the messages to request a translation
        """
        if self.instructions:
            self.messages.append({'role': "system", 'content': self.instructions})

        if context:
            summaries = context.get('summaries')
            if summaries:
                self.messages.append({'role': "user", 'content': '\n'.join(summaries)})

            tag_lines = GenerateTagLines(context, ['description', 'names','scene', 'summary', 'batch'])

            self.user_prompt = GenerateBatchPrompt(prompt, lines, tag_lines)

        else:
            self.user_prompt = GenerateBatchPrompt(prompt, lines)

        self.messages.append({'role': "user", 'content': self.user_prompt})

    def GenerateReducedMessages(self):
        """
        Remove context from the prompt to reduce the token count
        """
        self.messages.clear()
        if self.instructions:
            self.messages.append({'role': "system", 'content': self.instructions})
        
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

