import json
import logging
import os
import dotenv
import appdirs
from GUI.GuiHelpers import LoadInstructionsResource
from PySubtitle.Instructions import Instructions

from PySubtitle.version import __version__

config_dir = appdirs.user_config_dir("GPTSubtrans", "MachineWrapped", roaming=True)
settings_path = os.path.join(config_dir, 'settings.json')

# Load environment variables from .env file
dotenv.load_dotenv()

def env_bool(key, default=False):
    var = os.getenv(key, default)
    return var and str(var).lower() in ('true', 'yes', '1')

default_options = {
    'version': __version__,
    'api_key': os.getenv('API_KEY', None),
    'api_base': os.getenv('API_BASE', 'https://api.openai.com/v1'),
    'model': os.getenv('MODEL', 'gpt-3.5-turbo'),
    'prompt': os.getenv('PROMPT', "Please translate these subtitles[ for movie][ to language]."),
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
    'max_characters': int(os.getenv('MAX_CHARACTERS', 120)),
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

        if 'gpt_model' in self.options:
            self.options['model'] = self.options['gpt_model']
            del self.options['gpt_model']

    def get(self, option, default=None):
        return self.options.get(option, default)
    
    def add(self, option, value):
        self.options[option] = value

    def update(self, options):
        if isinstance(options, Options):
            return self.update(options.options)

        options = {k: v for k, v in options.items() if v is not None}
        self.options.update(options)

    @property
    def api_key(self):
        return self.get('api_key')

    @property
    def api_base(self):
        return self.get('api_base')    
    
    @property
    def allow_multithreaded_translation(self):
        return self.get('max_threads') and self.get('max_threads') > 1

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
        instruction_file = self.get('instruction_file')
        if instruction_file:
            try:
                instructions = LoadInstructionsResource(instruction_file)
                self.options['prompt'] = instructions.prompt
                self.options['instructions'] = instructions.instructions
                self.options['retry_instructions'] = instructions.retry_instructions

            except Exception as e:
                logging.error(f"Unable to load instructions from {instruction_file}: {e}")

    def _update_settings_version(self, settings):
        """
        This is where we would patch or remove any out of date settings.
        """
        current_version = default_options['version']
        settings['version'] = current_version    
