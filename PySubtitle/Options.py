from copy import deepcopy
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
    'provider': os.getenv('PROVIDER', None),
    'provider_settings': {},
    'prompt': os.getenv('PROMPT', "Please translate these subtitles[ for movie][ to language]."),
    'instruction_file': os.getenv('INSTRUCTION_FILE', "instructions.txt"),
    'target_language': os.getenv('TARGET_LANGUAGE', 'English'),
    'include_original': env_bool('INCLUDE_ORIGINAL', False),
    'allow_retranslations': env_bool('ALLOW_RETRANSLATIONS', True),
    'use_simple_batcher': env_bool('USE_SIMPLE_BATCHER', False),
    'scene_threshold': float(os.getenv('SCENE_THRESHOLD', 30.0)),
    'batch_threshold': float(os.getenv('BATCH_THRESHOLD', 7.0)),
    'min_batch_size': int(os.getenv('MIN_BATCH_SIZE', 10)),
    'max_batch_size': int(os.getenv('MAX_BATCH_SIZE', 30)),
    'max_context_summaries': int(os.getenv('MAX_CONTEXT_SUMMARIES', 10)),
    'max_characters': int(os.getenv('MAX_CHARACTERS', 120)),
    'max_newlines': int(os.getenv('MAX_NEWLINES', 2)),
    'match_partial_words': env_bool('MATCH_PARTIAL_WORDS', False),
    'whitespaces_to_newline' : env_bool('WHITESPACES_TO_NEWLINE', False),
    'max_lines': int(os.getenv('MAX_LINES')) if os.getenv('MAX_LINES') else None,
    'max_threads': int(os.getenv('MAX_THREADS', 4)),
    'max_retries': int(os.getenv('MAX_RETRIES', 2)),
    'max_summary_length': int(os.getenv('MAX_SUMMARY_LENGTH', 240)),
    'backoff_time': float(os.getenv('BACKOFF_TIME', 5.0)),
    'project' : os.getenv('PROJECT', None),
    'autosave': env_bool('AUTOSAVE', True),
    'stop_on_error' : env_bool('STOP_ON_ERROR'),
    'write_backup' : env_bool('WRITE_BACKUP_FILE', True),
    'theme' : os.getenv('THEME', None),
    'firstrun' : False
}

class Options:
    def __init__(self, options=None, **kwargs):
        # Initialise from defaults
        self.options = deepcopy(default_options)

        if isinstance(options, Options):
            options = options.options

        if options:
            # Remove None values from options and merge with defaults
            options = {k: deepcopy(v) for k, v in options.items() if v is not None}
            self.options = {**self.options, **options}

        # Apply any explicit parameters
        self.options.update(kwargs)

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
    def theme(self) -> str:
        return self.get('theme')

    @property
    def version(self) -> str:
        return self.get('version')

    @property
    def provider(self) -> str:
        """ the name of the translation provider """
        return self.get('provider')
    
    @provider.setter
    def provider(self, value: str):
        self.options['provider'] = value

    @property
    def provider_settings(self) -> dict:
        """ settings sections for each provider """
        return self.get('provider_settings', {})

    @property
    def current_provider_settings(self) -> dict:
        if not self.provider:
            return None
        
        return self.provider_settings.get(self.provider, {})
    
    @property
    def available_providers(self) -> list:
        return self.get('available_providers', [])

    @property
    def model(self) -> str:
        if not self.provider:
            return None
        
        return self.current_provider_settings.get('model')
    
    @property
    def allow_multithreaded_translation(self):
        return self.get('max_threads') and self.get('max_threads') > 1
    
    def GetInstructions(self) -> Instructions:
        """ Construct an Instructions object from the settings """
        return Instructions(self.options)

    def GetSettings(self) -> dict:
        """
        Get a copy of the settings dictionary with only the default keys included
        """
        settings = { key: deepcopy(self.get(key)) for key in self.options.keys() & default_options.keys() }
        return settings
    
    def LoadSettings(self):
        if not os.path.exists(settings_path) or self.get('firstrun'):
            return False
        
        try:
            with open(settings_path, "r", encoding="utf-8") as settings_file:
                settings = json.load(settings_file)
            
            if not settings:
                return False
            
            if not self.options:
                self.options = deepcopy(default_options)

            self.options.update(settings)

            if settings.get('version') != default_options['version']:
                self._update_version()

            return True
        
        except Exception as e:
            logging.error(f"Error loading settings from {settings_path}")
            return False

    def SaveSettings(self):
        try:
            settings : dict = self.GetSettings()

            if not settings:
                return False
            
            save_dict = { key : value for key, value in settings.items() if value != default_options.get(key) }

            if save_dict:
                os.makedirs(config_dir, exist_ok=True)

                save_dict['version'] = default_options['version']

                with open(settings_path, "w", encoding="utf-8") as settings_file:
                    json.dump(save_dict, settings_file, ensure_ascii=False, indent=4, sort_keys=True)

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

    def InitialiseProviderSettings(self, provider : str, settings : dict):
        """ Create or update the settings for a provider"""
        if provider not in self.provider_settings:
            self.provider_settings[provider] = deepcopy(settings)

        self.MoveSettingsToProvider(provider, settings.keys())

    def MoveSettingsToProvider(self, provider : str, keys : list):
        """ Move settings from the main options to a provider's settings """
        if provider not in self.provider_settings:
            self.provider_settings[provider] = {}

        settings_to_move = {key: self.options.pop(key) for key in keys if key in self.options}
        if settings_to_move:
            self.provider_settings[provider].update(settings_to_move)

    def _update_version(self):
        """ Update settings from older versions of the application """
        if 'gpt_model' in self.options:
            self.options['model'] = self.options['gpt_model']
            del self.options['gpt_model']

        if not self.provider_settings:
            self.options['provider_settings'] = {'OpenAI': {}} if self.options.get('api_key') else {}
            self.MoveSettingsToProvider('OpenAI', ['api_key', 'api_base', 'model', 'free_plan', 'max_instruct_tokens', 'temperature', 'rate_limit'])

        current_version = default_options['version']
        self.options['version'] = current_version
