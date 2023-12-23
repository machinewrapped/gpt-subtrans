import logging
import os

linesep = '\n'

default_instructions = linesep.join([
    "You are to translate subtitles to a target language",
    "Be concise but try to make the dialogue sound natural.",
    "Translations should be as accurate as possible, do not improvise!",
])

default_retry_instructions = linesep.join([
    'Translate the subtitles again, making sure every line has a translation that matches the dialog.'
])

class Instructions:
    def __init__(self, settings):
        self.InitialiseInstructions(settings)

    def InitialiseInstructions(self, settings : dict):
        self.prompt = settings.get('prompt') or settings.get('gpt_prompt')
        self.instructions = settings.get('instructions') or default_instructions
        self.retry_instructions = settings.get('retry_instructions') or default_retry_instructions
        self.instruction_file = settings.get('instruction_file') or None

        # Add any additional instructions from the command line
        if settings.get('instruction_args'):
            additional_instructions = linesep.join(settings['instruction_args'])
            if additional_instructions:
                self.instructions = linesep.join([self.instructions, additional_instructions])

        tags = {
            "[ for movie]": f" for {settings.get('movie_name')}" if settings.get('movie_name') else "",
            "[ to language]": f" to {settings.get('to_language')}" if settings.get('to_language') else "",
        }

        tags.update({ f"[{k}]": v for k, v in settings.items() if v })

        self.prompt = ReplaceTags(self.prompt, tags)
        self.instructions = ReplaceTags(self.instructions, tags)
        self.retry_instructions = ReplaceTags(self.retry_instructions, tags)

    def LoadInstructionsFile(self, filepath):
        """
        Try to load instructions from a text file.
        """
        if filepath and os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8", newline='') as f:
                lines = [l.strip() for l in f.readlines()]

            if not lines:
                return

            if not lines[0].startswith('###'):
                logging.info(f"Loading legacy instruction file: {filepath}")
                file_instructions, file_retry_instructions = LoadLegacyInstructions(lines)
                if file_instructions:
                    self.instructions = file_instructions
                    self.retry_instructions = file_retry_instructions or default_retry_instructions
                    self.instruction_file = os.path.basename(filepath)
                return

            sections = {}
            for line in lines:
                if line.startswith('###'):
                    section_name = line[3:].strip()
                    sections[section_name] = []
                elif line.strip() or sections[section_name]:
                    sections[section_name].append(line)

            self.prompt = linesep.join(sections.get('prompt', []))
            self.instructions = linesep.join(sections.get('instructions', []))
            self.retry_instructions = linesep.join(sections.get('retry_instructions', [])) or default_retry_instructions
            self.instruction_file = os.path.basename(filepath)

            if not self.prompt or not self.instructions:
                raise Exception("Invalid instruction file")

    def SaveInstructions(self, filepath):
        """
        Save instructions to a text file.
        """
        if filepath:
            # Make sure the file has a .txt extension
            if not filepath.endswith('.txt'):
                filepath += '.txt'

            # Write each section to the file with a header
            with open(filepath, "w", encoding="utf-8", newline='') as f:
                f.write("### prompt\n")
                f.write(self.prompt)
                f.write("\n\n### instructions\n")
                f.write(self.instructions)
                f.write("\n\n### retry_instructions\n")
                f.write(self.retry_instructions)
                f.write("\n")

            self.instruction_file = os.path.basename(filepath)

def LoadLegacyInstructions(lines):
    """
    Retry instructions can be added to the file after a line of at least 3 # characters.
    """
    if lines:
        for idx, item in enumerate(lines):
            if len(item) >= 3 and all(c == '#' for c in item):
                return linesep.join(lines[:idx]), linesep.join(lines[idx + 1:])

        return linesep.join(lines), []
        
    return None, None

def ReplaceTags(text, tags):
    """
    Replace option tags in a string with the value of the corresponding option.
    """
    if text:
        for name, value in tags.items():
            if value:
                text = text.replace(f"[{name}]", str(value))
    return text
