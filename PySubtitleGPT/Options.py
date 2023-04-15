import os
import dotenv
import darkdetect

linesep = '\n'

# Load environment variables from .env file
dotenv.load_dotenv()

default_instructions = linesep.join([
    "You are to translate subtitles to a target language",
    "Be concise but try to make the dialogue sound natural.",
    "Translations should be as accurate as possible, do not improvise!",
])

default_retry_instructions = linesep.join([
    'Translate the subtitles again, making sure every line has a translation that matches the dialog.'
])

def env_bool(key, default=False):
    var = os.getenv(key, default)
    return var and str(var).lower() in ('true', 'yes', '1')

default_options = {
    'api_key': os.getenv('API_KEY', None),
    'gpt_model': os.getenv('GPT_MODEL', 'gpt-3.5-turbo'),
    'gpt_prompt': os.getenv('GPT_PROMPT', "Please translate these subtitles[ for movie][ to language]."),
    'instruction_file': os.getenv('INSTRUCTION_FILE', "instructions.txt"),
    'target_language': os.getenv('TARGET_LANGUAGE', 'English'),
    'temperature': float(os.getenv('TEMPERATURE', 0.0)),
    'allow_retranslations': env_bool('ALLOW_RETRANSLATIONS', True),
    'scene_threshold': float(os.getenv('SCENE_THRESHOLD', 30.0)),
    'batch_threshold': float(os.getenv('BATCH_THRESHOLD', 5.0)),
    'min_batch_size': int(os.getenv('MIN_BATCH_SIZE', 5)),
    'max_batch_size': int(os.getenv('MAX_BATCH_SIZE', 25)),
    'max_context_summaries': int(os.getenv('MAX_CONTEXT_SUMMARIES', 10)),
    'max_characters': int(os.getenv('MAX_CHARACTERS', 120)),
    'max_newlines': int(os.getenv('MAX_NEWLINES', 3)),
    'max_lines': int(os.getenv('MAX_LINES')) if os.getenv('MAX_LINES') else None, 
    'rate_limit': float(os.getenv('RATE_LIMIT')) if os.getenv('RATE_LIMIT') else None,
    'max_retries': int(os.getenv('MAX_RETRIES', 5)),
    'backoff_time': float(os.getenv('BACKOFF_TIME', 4.0)),
    'project' : os.getenv('PROJECT', None),
    'enforce_line_parity': env_bool('ENFORCE_LINE_PARITY'),
    'stop_on_error' : env_bool('STOP_ON_ERROR'),
    'write_backup' : env_bool('WRITE_BACKUP_FILE'),
    'theme' : os.getenv('THEME', None)
}

class Options:
    def __init__(self, options=None, **kwargs):
        if not options:
            options = default_options.copy()
        else:
            # Remove None values from options and merge with default_options
            options = {k: v for k, v in options.items() if v}
            options = {**default_options, **options}

        self.options = options

        # Apply any explicit parameters
        options.update(kwargs)

        # Select theme or use OS default 
        if not self.get('theme'):
            self.add('theme', "subtrans-dark" if darkdetect.isDark() else "subtrans")

        # If instructions file exists load the instructions from that
        instructions, retry_instructions = LoadInstructionsFile(options.get('instruction_file'))
        instructions = instructions if instructions else default_instructions
        retry_instructions = retry_instructions if retry_instructions else self.options['retry_instructions']

        # Add any additional instructions from the command line
        if options.get('instruction_args'):
            instructions.extend(options['instruction_args'])

        instructions = self.ReplaceTagsWithOptions(instructions)
        retry_instructions = self.ReplaceTagsWithOptions(retry_instructions)

        options['instructions'] = instructions
        options['retry_instructions'] = retry_instructions

    def get(self, option, default=None):
        return self.options.get(option, default)
    
    def add(self, option, value):
        self.options[option] = value

    def update(self, options: dict):
        options = {k: v for k, v in options.items() if v}
        self.options.update(options)

    def api_key(self):
        return self.get('api_key')

    def ReplaceTagsWithOptions(self, text):
        """
        Replace option tags in a string with the value of the corresponding option.
        """
        for name, value in self.options.items():
            if value:
                text = text.replace(f"[{name}]", str(value))
        return text
    
    def GetNonProjectSpecificOptions(self):
        """
        Get a copy of the options with only the default keys included
        """
        return Options({
            key: self.get(key) for key in self.options.keys() & default_options.keys()
        })

def LoadInstructionsFile(filename):
    """
    Try to load instructions from a text file.
    Retry instructions can be added to the file after a line of at least 3 # characters.
    """
    if filename and os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]

        if lines:
            for idx, item in enumerate(lines):
                if len(item) >= 3 and all(c == '#' for c in item):
                    return linesep.join(lines[:idx]), linesep.join(lines[idx + 1:])

            return linesep.join(lines), []
        
    return None, None

