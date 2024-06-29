from copy import deepcopy
import json
import logging
import os
import dotenv

from PySubtitle.Instructions import Instructions, LoadInstructions
from PySubtitle.Helpers.Resources import config_dir
from PySubtitle.Helpers.Text import standard_filler_words
from PySubtitle.version import __version__

MULTILINE_OPTION = 'multiline'

settings_path = os.path.join(config_dir, 'settings.json')
default_user_prompt = "Translate these subtitles [ for movie][ to language]"

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
    'scene_threshold': float(os.getenv('SCENE_THRESHOLD', 30.0)),
    'min_batch_size': int(os.getenv('MIN_BATCH_SIZE', 10)),
    'max_batch_size': int(os.getenv('MAX_BATCH_SIZE', 30)),
    'max_context_summaries': int(os.getenv('MAX_CONTEXT_SUMMARIES', 10)),
    'max_characters': int(os.getenv('MAX_CHARACTERS', 120)),
    'max_newlines': int(os.getenv('MAX_NEWLINES', 2)),
    'max_single_line_length': int(os.getenv('MAX_SINGLE_LINE_LENGTH', 44)),
    'min_single_line_length': int(os.getenv('MIN_SINGLE_LINE_LENGTH', 8)),
    'postprocess_translation': env_bool('POSTPROCESS_TRANSLATION', False),
    'preprocess_subtitles': env_bool('PREPROCESS_SUBTITLES', False),
    'save_preprocessed_subtitles': env_bool('SAVE_PREPROCESSED_SUBTITLES', False),
    'break_long_lines': env_bool('BREAK_LONG_LINES', True),
    'break_dialog_on_one_line': env_bool('break_dialog_on_one_line', True),
    'max_line_duration': float(os.getenv('MAX_LINE_DURATION', 4.0)),
    'min_line_duration': float(os.getenv('MIN_LINE_DURATION', 0.8)),
    'merge_line_duration': float(os.getenv('MERGE_LINE_DURATION', 0.0)),
    'min_split_chars': int(os.getenv('MIN_SPLIT_CHARS', 3)),
    'normalise_dialog_tags': env_bool('NORMALISE_DIALOG_TAGS', True),
    'remove_filler_words': env_bool('REMOVE_FILLER_WORDS', True),
    'filler_words': standard_filler_words,
    'substitution_mode': os.getenv('SUBSTITUTION_MODE', "Auto"),
    'whitespaces_to_newline' : env_bool('WHITESPACES_TO_NEWLINE', False),
    'full_width_punctuation': env_bool('FULL_WIDTH_PUNCTUATION', False),
    'retry_on_error': env_bool('RETRY_ON_ERROR', True),
    # 'autosplit_incomplete': env_bool('AUTOSPLIT_INCOMPLETE', True),
    'max_lines': int(os.getenv('MAX_LINES')) if os.getenv('MAX_LINES') else None,
    'max_threads': int(os.getenv('MAX_THREADS', 4)),
    'max_retries': int(os.getenv('MAX_RETRIES', 2)),
    'max_summary_length': int(os.getenv('MAX_SUMMARY_LENGTH', 240)),
    'backoff_time': float(os.getenv('BACKOFF_TIME', 5.0)),
    'project' : os.getenv('PROJECT', None),
    'autosave': env_bool('AUTOSAVE', True),
    'last_used_path': None,
    'stop_on_error' : env_bool('STOP_ON_ERROR'),
    'write_backup' : env_bool('WRITE_BACKUP_FILE', True),
    'theme' : os.getenv('THEME', None),
    'firstrun' : False
}

def serialize(value):
    return value.serialize() if hasattr(value, 'serialize') else value

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
    def target_language(self) -> str:
        return self.get('target_language')

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
        """
        Load the settings from a JSON file
        """
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
        """
        Save the settings to a JSON file
        """
        try:
            settings : dict = self.GetSettings()

            if not settings:
                return False

            save_dict = { key : value for key, value in settings.items() if value != default_options.get(key) }

            if save_dict:
                os.makedirs(config_dir, exist_ok=True)

                save_dict['version'] = default_options['version']

                with open(settings_path, "w", encoding="utf-8") as settings_file:
                    json.dump(save_dict, settings_file, ensure_ascii=False, indent=4, sort_keys=True, default=serialize)

            return True

        except Exception as e:
            logging.error(f"Error saving settings to {settings_path}")
            return False

    def BuildUserPrompt(self) -> str:
        """
        Generate the user prompt to use for requesting translations
        """
        target_language = self.get('target_language')
        movie_name = self.get('movie_name')
        prompt : str = self.get('prompt', default_user_prompt)
        prompt = prompt.replace('[ to language]', f" to {target_language}" if target_language else "")
        prompt = prompt.replace('[ for movie]', f" for {movie_name}" if movie_name else "")

        for k,v in self.options.items():
            if v:
                prompt = prompt.replace(f"[{k}]", str(v))

        return prompt.strip()

    def InitialiseInstructions(self):
        """
        Load options from instructions file if specified
        """
        instruction_file = self.get('instruction_file')
        if instruction_file:
            try:
                instructions = LoadInstructions(instruction_file)
                self.options['prompt'] = instructions.prompt
                self.options['instructions'] = instructions.instructions
                self.options['retry_instructions'] = instructions.retry_instructions

            except Exception as e:
                logging.error(f"Unable to load instructions from {instruction_file}: {e}")

    def InitialiseProviderSettings(self, provider : str, settings : dict):
        """
        Create or update the settings for a provider
        """
        if provider not in self.provider_settings:
            self.provider_settings[provider] = deepcopy(settings)

        self.MoveSettingsToProvider(provider, settings.keys())

    def MoveSettingsToProvider(self, provider : str, keys : list):
        """
        Move settings from the main options to a provider's settings
        """
        if provider not in self.provider_settings:
            self.provider_settings[provider] = {}

        settings_to_move = {key: self.options.pop(key) for key in keys if key in self.options}
        if settings_to_move:
            self.provider_settings[provider].update(settings_to_move)

    def _update_version(self):
        """
        Update settings from older versions of the application
        """
        if 'gpt_model' in self.options:
            self.options['model'] = self.options['gpt_model']
            del self.options['gpt_model']

        if not self.provider_settings:
            self.options['provider_settings'] = {'OpenAI': {}} if self.options.get('api_key') else {}
            self.MoveSettingsToProvider('OpenAI', ['api_key', 'api_base', 'model', 'free_plan', 'max_instruct_tokens', 'temperature', 'rate_limit'])

        current_version = default_options['version']
        self.options['version'] = current_version

