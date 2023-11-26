import json
import logging
import os
import dotenv
import appdirs

from PySubtitle.version import __version__

linesep = '\n'

config_dir = appdirs.user_config_dir("GPTSubtrans", "MachineWrapped", roaming=True)
settings_path = os.path.join(config_dir, 'settings.json')

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
    'version': __version__,
    'api_key': os.getenv('API_KEY', None),
    'api_base': os.getenv('API_BASE', 'https://api.openai.com/v1'),
    'gpt_model': os.getenv('GPT_MODEL', 'gpt-3.5-turbo'),
    'gpt_prompt': os.getenv('GPT_PROMPT', "Please translate these subtitles[ for movie][ to language]."),
    'instruction_file': os.getenv('INSTRUCTION_FILE', "instructions.txt"),
    'target_language': os.getenv('TARGET_LANGUAGE', 'English'),
    'include_original': env_bool('INCLUDE_ORIGINAL', False),
    'temperature': float(os.getenv('TEMPERATURE', 0.0)),
    'allow_retranslations': env_bool('ALLOW_RETRANSLATIONS', True),
    'use_simple_batcher': env_bool('USE_SIMPLE_BATCHER', False),
    'scene_threshold': float(os.getenv('SCENE_THRESHOLD', 30.0)),
    'batch_threshold': float(os.getenv('BATCH_THRESHOLD', 7.0)),
    'min_batch_size': int(os.getenv('MIN_BATCH_SIZE', 7)),
    'max_batch_size': int(os.getenv('MAX_BATCH_SIZE', 30)),
    'max_context_summaries': int(os.getenv('MAX_CONTEXT_SUMMARIES', 10)),
    'max_characters': int(os.getenv('MAX_CHARACTERS', 99)),
    'max_newlines': int(os.getenv('MAX_NEWLINES', 3)),
    'match_partial_words': env_bool('MATCH_PARTIAL_WORDS', False),
    'whitespaces_to_newline' : env_bool('WHITESPACES_TO_NEWLINE', False),
    'max_lines': int(os.getenv('MAX_LINES')) if os.getenv('MAX_LINES') else None, 
    'rate_limit': float(os.getenv('RATE_LIMIT')) if os.getenv('RATE_LIMIT') else None,
    'max_threads': int(os.getenv('MAX_THREADS', 4)),
    'max_retries': int(os.getenv('MAX_RETRIES', 5)),
    'backoff_time': float(os.getenv('BACKOFF_TIME', 4.0)),
    'max_instruct_tokens': int(os.getenv('MAX_INSTRUCT_TOKENS', 2048)),
    'project' : os.getenv('PROJECT', None),
    'autosave': env_bool('AUTOSAVE', True),
    'enforce_line_parity': env_bool('ENFORCE_LINE_PARITY', True),
    'stop_on_error' : env_bool('STOP_ON_ERROR'),
    'write_backup' : env_bool('WRITE_BACKUP_FILE', True),
    'theme' : os.getenv('THEME', None),
    'firstrun' : False
}

class Options:
    def __init__(self, options=None, **kwargs):
        # Initialise from defaults settings
        self.options = default_options.copy()

        if hasattr(options, 'options'):
            options = options.options

        if options:
            # Remove None values from options and merge with defaults
            options = {k: v for k, v in options.items() if v}
            self.options = {**self.options, **options}

        # Apply any explicit parameters
        self.options.update(kwargs)

        options = self.options

    def get(self, option, default=None):
        return self.options.get(option, default)
    
    def add(self, option, value):
        self.options[option] = value

    def update(self, options):
        if isinstance(options, Options):
            return self.update(options.options)

        options = {k: v for k, v in options.items() if v is not None}
        self.options.update(options)

    def api_key(self):
        return self.get('api_key')

    def api_base(self):
        return self.get('api_base')    
    
    def allow_multithreaded_translation(self):
        return self.get('max_threads') and self.get('max_threads') > 1

    def ReplaceTagsWithOptions(self, text):
        """
        Replace option tags in a string with the value of the corresponding option.
        """
        if text:
            for name, value in self.options.items():
                if value:
                    text = text.replace(f"[{name}]", str(value))
        return text
    
    def GetNonProjectSpecificOptions(self):
        """
        Get a copy of the options with only the default keys included
        """
        options = { key: self.get(key) for key in self.options.keys() & default_options.keys() }
        return Options(options)
    
    def GetSettings(self) -> dict:
        """
        Return a dictionary of generic options
        """
        exclusions = [ 'instructions', 'retry_instructions' ]
        keys = [ key for key in default_options.keys() if key not in exclusions]
        settings = { key: self.get(key) for key in keys if key in self.options.keys() }
        return settings

    def Load(self):
        if not os.path.exists(settings_path) or self.get('firstrun'):
            return False
        
        try:
            with open(settings_path, "r", encoding="utf-8") as settings_file:
                settings = json.load(settings_file)
            
            if not settings:
                return False
            
            if settings.get('version') != default_options['version']:
                self._update_settings_version(settings)

            if not self.options:
                self.options = default_options.copy()

            self.options.update(settings)

            return True
        
        except Exception as e:
            logging.error(f"Error loading settings from {settings_path}")
            return False

    def Save(self):
        try:
            settings : dict = self.GetSettings()

            if not settings:
                return False
            
            save_dict = { key : value for key, value in settings.items() if value != default_options.get(key) }

            if save_dict:
                os.makedirs(config_dir, exist_ok=True)

                save_dict['version'] = default_options['version']

                with open(settings_path, "w", encoding="utf-8") as settings_file:
                    json.dump(save_dict, settings_file, ensure_ascii=False)

            return True

        except Exception as e:
            logging.error(f"Error saving settings to {settings_path}")
            return False

    def InitialiseInstructions(self):
        instructions = self.get('instructions') or default_instructions
        retry_instructions = self.get('retry_instructions') or default_retry_instructions

        # If instructions file exists load the instructions from that
        if self.get('instruction_file'):
            file_instructions, file_retry_instructions = LoadInstructionsFile(self.get('instruction_file'))
            if file_instructions and file_retry_instructions:
                instructions = file_instructions
                retry_instructions = file_retry_instructions

        # Add any additional instructions from the command line
        if self.get('instruction_args'):
            instructions.extend(self['instruction_args'])

        instructions = self.ReplaceTagsWithOptions(instructions)
        retry_instructions = self.ReplaceTagsWithOptions(retry_instructions)

        self.add('instructions', instructions)
        self.add('retry_instructions', retry_instructions)

    def _update_settings_version(self, settings):
        """
        This is where we would patch or remove any out of date settings.
        """
        current_version = default_options['version']
        settings['version'] = current_version    

def LoadInstructionsFile(filepath):
    """
    Try to load instructions from a text file.
    Retry instructions can be added to the file after a line of at least 3 # characters.
    """
    if filepath and os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8", newline='') as f:
            lines = [l.strip() for l in f.readlines()]

        if lines:
            for idx, item in enumerate(lines):
                if len(item) >= 3 and all(c == '#' for c in item):
                    return linesep.join(lines[:idx]), linesep.join(lines[idx + 1:])

            return linesep.join(lines), []
        
    return None, None

