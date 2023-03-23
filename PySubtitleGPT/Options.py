import os

default_instructions = os.linesep.join([
    "You are to translate subtitles to a target language",
    "Be concise but try to make the dialogue sound natural.",
    "Translations should be as accurate as possible, do not improvise!",
])

default_retry_instructions = os.linesep.join([
    'Translate the subtitles again, making sure every line has a translation that matches the dialog.'
])

def env_bool(key):
    var = os.getenv(key)
    return var and str(var).lower() in ('true', 'yes', '1')

default_options = {
    'api_key': os.getenv('API_KEY', None),
    'gpt_model': os.getenv('GPT_MODEL', 'gpt-3.5-turbo'),
    'gpt_prompt': os.getenv('GPT_PROMPT', "Please translate these subtitles[ for movie][ to language]."),
    'instruction_file': os.getenv('INSTRUCTIONFILE', "instructions.txt"),
    'target_language' : os.getenv('TARGET_LANGUAGE', 'English'),
    'movie_name' : None,
    'temperature': float(os.getenv('TEMPERATURE', 0.0)),
    'allow_retranslations': env_bool('ALLOW_RETRANSLATIONS'),
    'scene_threshold': float(os.getenv('SCENE_THRESHOLD', 15.0)),
    'batch_threshold': float(os.getenv('BATCH_THRESHOLD', 3.0)),
    'min_batch_size': int(os.getenv('MIN_BATCH_SIZE', 5)),
    'max_batch_size': int(os.getenv('MAX_BATCH_SIZE', 20)),
    'max_lines': int(os.getenv('MAX_LINES')) if os.getenv('MAX_LINES') else None, 
    'rate_limit': float(os.getenv('RATE_LIMIT')) if os.getenv('RATE_LIMIT') else None,
    'max_retries': int(os.getenv('MAX_RETRIES', 5)),
    'backoff_time': float(os.getenv('BACKOFF_TIME', 4.0)),
    'project' : os.getenv('PROJECT', None),
    'stop_on_error' : env_bool('STOP_ON_ERROR')
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

        # If instructions file exists load the instructions from that
        instructions, retry_instructions = LoadInstructionsFile(options.get('instruction_file'))
        instructions = instructions if instructions else default_instructions
        retry_instructions = retry_instructions if retry_instructions else self.options['retry_instructions']

        # Add any additional instructions from the command line
        if options.get('instruction_args'):
            instructions.extend(options['instruction_args'])

        options['instructions'] = instructions
        options['retry_instructions'] = retry_instructions

    def get(self, option, default=None):
        return self.options.get(option, default)
    
    def add(self, option, value):
        self.options[option] = value

    def api_key(self):
        return self.get('api_key')
    
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
                    return os.linesep.join(lines[:idx]), os.linesep.join(lines[idx + 1:])

            return os.linesep.join(lines), []
        
    return None, None
