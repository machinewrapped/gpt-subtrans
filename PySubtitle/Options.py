from copy import deepcopy
import json
import logging
from math import e
import os
from typing import Any
import dotenv

from PySubtitle.Helpers.Version import VersionNumberLessThan
from PySubtitle.Instructions import Instructions, LoadInstructions, default_user_prompt
from PySubtitle.Helpers.Localization import _
from PySubtitle.Helpers.Resources import config_dir, old_config_dir
from PySubtitle.Helpers.Text import standard_filler_words
from PySubtitle.version import __version__

MULTILINE_OPTION = 'multiline'

settings_path = os.path.join(config_dir, 'settings.json')

# Load environment variables from .env file
dotenv.load_dotenv()

def env_bool(key, default=False) -> bool:
    var = os.getenv(key, default)
    return True if var and str(var).lower() in ('true', 'yes', '1') else False

def env_int(key, default : int|None = None) -> int|None:
    value = os.getenv(key, default)
    return int(value) if value is not None else None

def env_float(key, default : float|None = None) -> float|None:
    value = os.getenv(key, default)
    return float(value) if value is not None else None

default_options : dict[str, Any] = {
    'version': __version__,
    'provider': os.getenv('PROVIDER', None),
    'provider_settings': {},
    'prompt': os.getenv('PROMPT', default_user_prompt),
    'instruction_file': os.getenv('INSTRUCTION_FILE', "instructions.txt"),
    'target_language': os.getenv('TARGET_LANGUAGE', 'English'),
    'include_original': env_bool('INCLUDE_ORIGINAL', False),
    'add_right_to_left_markers': env_bool('add_right_to_left_markers', False),
    'scene_threshold': env_float('SCENE_THRESHOLD', 30.0),
    'min_batch_size': env_int('MIN_BATCH_SIZE', 10),
    'max_batch_size': env_int('MAX_BATCH_SIZE', 30),
    'max_context_summaries': env_int('MAX_CONTEXT_SUMMARIES', 10),
    'max_characters': env_int('MAX_CHARACTERS', 120),
    'max_newlines': env_int('MAX_NEWLINES', 2),
    'max_single_line_length': env_int('MAX_SINGLE_LINE_LENGTH', 44),
    'min_single_line_length': env_int('MIN_SINGLE_LINE_LENGTH', 8),
    'postprocess_translation': env_bool('POSTPROCESS_TRANSLATION', False),
    'preprocess_subtitles': env_bool('PREPROCESS_SUBTITLES', False),
    'save_preprocessed_subtitles': env_bool('SAVE_PREPROCESSED_SUBTITLES', False),
    'break_long_lines': env_bool('BREAK_LONG_LINES', True),
    'break_dialog_on_one_line': env_bool('break_dialog_on_one_line', True),
    'max_line_duration': env_float('MAX_LINE_DURATION', 4.0),
    'min_line_duration': env_float('MIN_LINE_DURATION', 0.8),
    'merge_line_duration': env_float('MERGE_LINE_DURATION', 0.0),
    'min_split_chars': env_int('MIN_SPLIT_CHARS', 3),
    'normalise_dialog_tags': env_bool('NORMALISE_DIALOG_TAGS', True),
    'remove_filler_words': env_bool('REMOVE_FILLER_WORDS', True),
    'filler_words': standard_filler_words,
    'substitution_mode': os.getenv('SUBSTITUTION_MODE', "Auto"),
    'whitespaces_to_newline' : env_bool('WHITESPACES_TO_NEWLINE', False),
    'full_width_punctuation': env_bool('FULL_WIDTH_PUNCTUATION', False),
    'convert_wide_dashes': env_bool('CONVERT_WIDE_DASHES', True),
    'retry_on_error': env_bool('RETRY_ON_ERROR', True),
    # 'autosplit_incomplete': env_bool('AUTOSPLIT_INCOMPLETE', True),
    'max_lines': env_int('MAX_LINES', None),
    'max_threads': env_int('MAX_THREADS', 4),
    'max_retries': env_int('MAX_RETRIES', 1),
    'max_summary_length': env_int('MAX_SUMMARY_LENGTH', 240),
    'backoff_time': env_float('BACKOFF_TIME', 3.0),
    'project' : os.getenv('PROJECT', None),
    'autosave': env_bool('AUTOSAVE', True),
    'last_used_path': None,
    'stop_on_error' : env_bool('STOP_ON_ERROR'),
    'write_backup' : env_bool('WRITE_BACKUP_FILE', True),
    'theme' : os.getenv('THEME', None),
    'ui_language': os.getenv('UI_LANGUAGE', 'en'),
    'firstrun' : False
}

def serialize(value):
    return value.serialize() if hasattr(value, 'serialize') else value

class Options:
    def __init__(self, options : 'dict[str,Any]|Options|None'=None, **kwargs):
        # Initialise from defaults
        self.options : dict[str, Any] = deepcopy(default_options)

        if isinstance(options, Options):
            options = options.options

        if options:
            # Remove None values from options and merge with defaults
            options = {k: deepcopy(v) for k, v in options.items() if v is not None}
            self.options = {**self.options, **options}

        # Apply any explicit parameters
        self.options.update(kwargs)

    def get(self, option, default=None) -> Any:
        return self.options.get(option, default)

    def add(self, option, value):
        self.options[option] = value

    def update(self, options) -> None:
        if isinstance(options, Options):
            return self.update(options.options)

        options = {k: v for k, v in options.items() if v is not None}
        self.options.update(options)

    @property
    def theme(self) -> str:
        return self.get('theme')
    
    @property
    def ui_language(self) -> str:
        return self.get('ui_language', 'en')

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
    def current_provider_settings(self) -> dict[str,Any]|None:
        if not self.provider:
            return None

        return self.provider_settings.get(self.provider, {})

    @property
    def available_providers(self) -> list:
        return self.get('available_providers', [])

    @property
    def model(self) -> str|None:
        if not self.provider:
            return None

        current_provider_settings = self.current_provider_settings
        return current_provider_settings.get('model') if current_provider_settings else None

    @property
    def target_language(self) -> str:
        return self.get('target_language', default_options['target_language'])

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

            if VersionNumberLessThan(settings.get('version'), default_options['version']):
                self._update_version()

            return True

        except Exception as e:
            logging.debug("Error loading settings from {}: {}".format(settings_path, e))
            logging.error(_("Error loading settings from {}").format(settings_path))
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
            logging.debug("Error saving settings to {}: {}".format(settings_path, e))
            logging.error(_("Error saving settings to {}").format(settings_path))
            return False
        
    def MigrateSettings(self) -> bool:
        """
        Migrate settings from the old config directory to the new one
        """
        if os.path.exists(settings_path):
            return False
        
        old_settings_path = os.path.join(old_config_dir, 'settings.json')
        if not os.path.exists(old_settings_path):
            return False

        try:
            if not os.path.exists(config_dir):
                # Rename the old config directory to the new one
                os.rename(old_config_dir, config_dir)
                logging.info("Settings migrated to new location")
            else:
                os.rename(old_settings_path, settings_path)
                logging.info("Settings file migrated to new location")

                old_custom_instructions_path = os.path.join(old_config_dir, 'instructions')
                if os.path.exists(old_custom_instructions_path):
                    new_custom_instructions_path = os.path.join(config_dir, 'instructions')
                    if not os.path.exists(new_custom_instructions_path):
                        os.rename(old_custom_instructions_path, new_custom_instructions_path)
                        logging.info("Custom instructions migrated to new location")                
                
            return True

        except Exception as e:
            logging.debug(f"Error migrating settings from {old_config_dir} to {config_dir}: {e}")
            logging.error(_("Error migrating settings from {} to {}. You can copy the files manually and restart the application.").format(old_config_dir, config_dir))
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
                logging.error(_("Unable to load instructions from {}: {}").format(instruction_file, e))

    def InitialiseProviderSettings(self, provider : str, settings : dict[str, Any]) -> None:
        """
        Create or update the settings for a provider
        """
        if provider not in self.provider_settings:
            self.provider_settings[provider] = deepcopy(settings)

        self.MoveSettingsToProvider(provider, list(settings.keys()))

    def MoveSettingsToProvider(self, provider : str, keys : list[str]) -> None:
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

        previous_version = self.options.get('version', 'v0.0.0')
        latest_version = default_options['version']

        # Move settings from Local Server to Custom Server
        if 'Local Server' in self.provider_settings and VersionNumberLessThan(previous_version, "v1.0.7"):
            self.provider_settings['Custom Server'] = self.provider_settings['Local Server']
            del self.provider_settings['Local Server']

        self.options['version'] = latest_version

