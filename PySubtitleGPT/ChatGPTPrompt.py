from os import linesep

from PySubtitleGPT.Helpers import GenerateTagLines, GenerateBatchPrompt

class ChatGPTPrompt:
    def __init__(self, instructions):
        self.instructions = instructions
        self.user_prompt = None
        self.messages = []
        
    def GenerateMessages(self, prompt, lines, context):
        if self.instructions:
            self.messages.append({'role': "system", 'content': self.instructions})

        if context:
            tags = ['synopsis', 'characters']
            context_tags = GenerateTagLines(context, tags)
            if context_tags:
                self.messages.append({'role': "user", 'content': context_tags})

            previous_batch = context.get('previous_batch')
            if previous_batch:
                previous_subtitles = previous_batch.subtitles
                previous_lines = [ line.prompt for line in previous_subtitles ]
                user_previous = linesep.join(previous_lines)
                self.messages.append({'role': "assistant", 'content': user_previous})

                # previous_translations = previous_batch.translations
                # if previous_translations:
                #     translation_lines = GetLineItems(previous_translations, 'translation')
                #     if (previous_batch.summary):
                #         translation_lines.append(f"{GenerateTag('summary', previous_batch.summary)}")
                #     self.messages.append({'role': "assistant", 'content': linesep.join(translation_lines)})

            tag_lines = GenerateTagLines(context, ['summary'])

            self.user_prompt = GenerateBatchPrompt(prompt, lines, tag_lines)

        else:
            self.user_prompt = GenerateBatchPrompt(prompt, lines)



        self.messages.append({'role': "user", 'content': self.user_prompt})

    # Request retranslation of lines that were not translated originally
    def GenerateRetryPrompt(self, translation, retry_instructions, untranslated):
        retry_prompt = GenerateBatchPrompt(retry_instructions, untranslated)

        self.messages.extend([
            { 'role': "assistant", 'content': translation.text },
            { 'role': "system", 'content': retry_instructions },
            { 'role': "user", 'content': retry_prompt }
        ])


