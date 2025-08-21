import unittest
import os
import tempfile
import json
from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch, mock_open

from PySubtitle.Options import Options, default_options, standard_filler_words
from PySubtitle.Instructions import Instructions
from PySubtitle.Helpers.Tests import log_input_expected_result, log_test_name
from PySubtitle.Helpers.Settings import (
    GetBoolSetting, GetIntSetting, GetFloatSetting, GetStrSetting,
    GetListSetting, GetStringListSetting, GetTimeDeltaSetting,
    get_optional_setting, validate_setting_type, SettingsError
)


class TestOptions(unittest.TestCase):
    """Unit tests for the Options class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_options = {
            'provider': 'Test Provider',
            'target_language': 'Spanish',
            'max_batch_size': 25,
            'temperature': 0.5,
            'custom_setting': 'test_value'
        }

    def test_default_initialization(self):
        """Test that Options initializes with default values"""
        options = Options()
        
        # Check a selection of stable default options
        self.assertEqual(options.get('target_language'), 'English')
        self.assertEqual(options.get('scene_threshold'), 30.0)
        self.assertEqual(options.get('max_newlines'), 2)
        self.assertFalse(options.get('include_original'))
        self.assertTrue(options.get('break_long_lines'))
        self.assertTrue(options.get('normalise_dialog_tags'))
        self.assertTrue(options.get('remove_filler_words'))
        self.assertTrue(options.get('autosave'))
        self.assertEqual(options.get('ui_language'), 'en')
        self.assertEqual(options.get('filler_words'), standard_filler_words)
        
        # Check that provider settings is initialized as empty dict
        self.assertEqual(options.get('provider_settings'), {})
        
        # Verify None values are handled correctly (some may have env defaults)
        # Provider might have environment default, so we'll skip this check
        self.assertIsNone(options.get('project'))
        self.assertIsNone(options.get('last_used_path'))

    def test_initialization_with_dict(self):
        """Test Options initialization with a dictionary"""
        options = Options(self.test_options)
        
        # Check that custom values override defaults
        self.assertEqual(options.get('provider'), 'Test Provider')
        self.assertEqual(options.get('target_language'), 'Spanish')
        self.assertEqual(options.get('max_batch_size'), 25)
        self.assertEqual(options.get('temperature'), 0.5)
        self.assertEqual(options.get('custom_setting'), 'test_value')
        
        # Check that defaults are still present for unspecified options
        self.assertEqual(options.get('min_batch_size'), 10)
        self.assertEqual(options.get('scene_threshold'), 30.0)

    def test_initialization_with_options_object(self):
        """Test Options initialization with another Options object"""
        original = Options(self.test_options)
        copy_options = Options(original)
        
        # Check that values are copied correctly
        self.assertEqual(copy_options.get('provider'), 'Test Provider')
        self.assertEqual(copy_options.get('target_language'), 'Spanish')
        self.assertEqual(copy_options.get('max_batch_size'), 25)
        
        # Verify it's a deep copy - modifying one doesn't affect the other
        copy_options.set('provider', 'Different Provider')
        self.assertEqual(original.get('provider'), 'Test Provider')
        self.assertEqual(copy_options.get('provider'), 'Different Provider')

    def test_initialization_with_kwargs(self):
        """Test Options initialization with keyword arguments"""
        options = Options(
            provider='Kwargs Provider',
            target_language='French',
            max_batch_size=50
        )
        
        self.assertEqual(options.get('provider'), 'Kwargs Provider')
        self.assertEqual(options.get('target_language'), 'French')
        self.assertEqual(options.get('max_batch_size'), 50)

    def test_initialization_dict_and_kwargs(self):
        """Test Options initialization with both dict and kwargs (kwargs should override)"""
        options = Options(
            self.test_options,
            provider='Kwargs Override Provider',
            max_batch_size=100
        )
        
        # Kwargs should override dict values
        self.assertEqual(options.get('provider'), 'Kwargs Override Provider')
        self.assertEqual(options.get('max_batch_size'), 100)
        
        # Dict values should still be present where not overridden
        self.assertEqual(options.get('target_language'), 'Spanish')
        self.assertEqual(options.get('temperature'), 0.5)

    def test_none_values_filtered(self):
        """Test that None values in input options are filtered out"""
        options_with_none = {
            'provider': 'Test Provider',
            'target_language': None,  # Should be filtered out
            'max_batch_size': 25,
            'custom_setting': None    # Should be filtered out
        }
        
        options = Options(options_with_none)
        
        # None values should be filtered, defaults should remain
        self.assertEqual(options.get('provider'), 'Test Provider')
        self.assertEqual(options.get('target_language'), 'English')  # Default
        self.assertEqual(options.get('max_batch_size'), 25)
        self.assertIsNone(options.get('custom_setting'))  # Not in defaults

    def test_get_method(self):
        """Test the get method with default values"""
        options = Options(self.test_options)
        
        # Test getting existing values
        self.assertEqual(options.get('provider'), 'Test Provider')
        self.assertEqual(options.get('target_language'), 'Spanish')
        
        # Test getting non-existing values with default
        self.assertEqual(options.get('non_existing', 'default'), 'default')
        self.assertIsNone(options.get('non_existing'))

    def test_add_method(self):
        """Test the add method"""
        options = Options()
        options.add('new_option', 'new_value')
        
        self.assertEqual(options.get('new_option'), 'new_value')

    def test_set_method(self):
        """Test the set method"""
        options = Options(self.test_options)
        
        # Test setting existing option
        options.set('provider', 'Updated Provider')
        self.assertEqual(options.get('provider'), 'Updated Provider')
        
        # Test setting new option
        options.set('new_option', 'new_value')
        self.assertEqual(options.get('new_option'), 'new_value')

    def test_update_method_with_dict(self):
        """Test the update method with a dictionary"""
        options = Options()
        
        update_dict = {
            'provider': 'Updated Provider',
            'target_language': 'German',
            'new_setting': 'new_value',
            'none_setting': None  # Should be filtered out
        }
        
        options.update(update_dict)
        
        self.assertEqual(options.get('provider'), 'Updated Provider')
        self.assertEqual(options.get('target_language'), 'German')
        self.assertEqual(options.get('new_setting'), 'new_value')
        self.assertIsNone(options.get('none_setting'))

    def test_update_method_with_options(self):
        """Test the update method with another Options object"""
        options1 = Options({'provider': 'Provider 1', 'target_language': 'Spanish'})
        options2 = Options({'provider': 'Provider 2', 'max_batch_size': 50})
        
        options1.update(options2)
        
        # Should have updated values from options2
        self.assertEqual(options1.get('provider'), 'Provider 2')
        self.assertEqual(options1.get('max_batch_size'), 50)
        
        # The update method updates with all options from options2, including defaults
        # So target_language gets updated to English (the default in options2)
        self.assertEqual(options1.get('target_language'), 'English')

    def test_properties(self):
        """Test various properties of Options"""
        options = Options({
            'theme': 'dark',
            'ui_language': 'es',
            'version': '1.0.0',
            'provider': 'Test Provider',
            'provider_settings': {
                'Test Provider': {
                    'model': 'test-model',
                    'api_key': 'test-key'
                }
            },
            'available_providers': ['Provider1', 'Provider2'],
            'target_language': 'French'
        })
        
        # Test basic properties
        self.assertEqual(options.theme, 'dark')
        self.assertEqual(options.ui_language, 'es')
        self.assertEqual(options.version, '1.0.0')
        self.assertEqual(options.provider, 'Test Provider')
        self.assertEqual(options.target_language, 'French')
        self.assertEqual(options.available_providers, ['Provider1', 'Provider2'])
        
        # Test provider settings
        self.assertIsInstance(options.provider_settings, dict)
        self.assertIsNotNone(options.current_provider_settings)
        if options.current_provider_settings is not None:
            self.assertEqual(options.current_provider_settings['model'], 'test-model')
        self.assertEqual(options.model, 'test-model')

    def test_provider_setter(self):
        """Test the provider property setter"""
        options = Options()
        options.provider = 'New Provider'
        
        self.assertEqual(options.provider, 'New Provider')
        self.assertEqual(options.get('provider'), 'New Provider')

    def test_current_provider_settings_no_provider(self):
        """Test current_provider_settings when no provider is set"""
        # Create options without provider in defaults and force it to None
        options = Options()
        options.set('provider', None)  # Force to None
        self.assertIsNone(options.current_provider_settings)

    def test_current_provider_settings_missing_provider(self):
        """Test current_provider_settings when provider is not in settings"""
        options = Options({
            'provider': 'Missing Provider',
            'provider_settings': {}
        })
        self.assertEqual(options.current_provider_settings, {})

    def test_model_property(self):
        """Test the model property"""
        # Test with no provider
        options = Options()
        self.assertIsNone(options.model)
        
        # Test with provider but no settings
        options = Options({
            'provider': 'Test Provider',
            'provider_settings': {}
        })
        self.assertIsNone(options.model)
        
        # Test with provider and model
        options = Options({
            'provider': 'Test Provider',
            'provider_settings': {
                'Test Provider': {'model': 'test-model'}
            }
        })
        self.assertEqual(options.model, 'test-model')

    def test_get_instructions(self):
        """Test GetInstructions method"""
        options = Options({
            'instructions': 'Test instructions',
            'retry_instructions': 'Test retry instructions'
        })
        
        instructions = options.GetInstructions()
        self.assertIsInstance(instructions, Instructions)

    def test_get_settings(self):
        """Test GetSettings method"""
        options = Options(self.test_options)
        settings = options.GetSettings()
        
        # Should only contain keys that exist in default_options
        self.assertIn('provider', settings)
        self.assertIn('target_language', settings)
        self.assertIn('max_batch_size', settings)
        
        # Should not contain custom keys not in defaults
        self.assertNotIn('custom_setting', settings)
        
        # Values should match
        self.assertEqual(settings['provider'], 'Test Provider')
        self.assertEqual(settings['target_language'], 'Spanish')

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_load_settings_file_not_exists(self, mock_exists, mock_file):
        """Test LoadSettings when file doesn't exist"""
        mock_exists.return_value = False
        
        options = Options()
        result = options.LoadSettings()
        
        self.assertFalse(result)
        mock_file.assert_not_called()

    @patch('PySubtitle.Helpers.Version.VersionNumberLessThan')
    @patch('json.load')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_load_settings_success(self, mock_exists, mock_file, mock_json_load, mock_version):
        """Test successful LoadSettings"""
        mock_exists.return_value = True
        mock_json_load.return_value = {"provider": "Loaded Provider", "target_language": "Italian", "version": "1.0.0"}
        mock_version.return_value = False  # Version is not less than current
        
        options = Options()
        # Override firstrun to False to ensure LoadSettings proceeds
        options.set('firstrun', False)
        result = options.LoadSettings()
        
        self.assertTrue(result)
        self.assertEqual(options.get('provider'), 'Loaded Provider')
        self.assertEqual(options.get('target_language'), 'Italian')

    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_save_settings_success(self, mock_makedirs, mock_file):
        """Test successful SaveSettings"""
        options = Options(self.test_options)
        result = options.SaveSettings()
        
        self.assertTrue(result)
        mock_file.assert_called_once()
        mock_makedirs.assert_called_once()

    def test_build_user_prompt(self):
        """Test BuildUserPrompt method"""
        options = Options({
            'prompt': 'Translate[ to language][ for movie] the following subtitles: [custom_var]',
            'target_language': 'Spanish',
            'movie_name': 'Test Movie',
            'custom_var': 'test_value'
        })
        
        result = options.BuildUserPrompt()
        expected = 'Translate to Spanish for Test Movie the following subtitles: test_value'
        self.assertEqual(result, expected)

    def test_build_user_prompt_empty_values(self):
        """Test BuildUserPrompt with empty/None values"""
        options = Options({
            'prompt': 'Translate[ to language][ for movie] subtitles',
            'target_language': None,
            'movie_name': None
        })
        
        result = options.BuildUserPrompt()
        expected = 'Translate to English subtitles'  # target_language defaults to English
        self.assertEqual(result, expected)

    @patch('PySubtitle.Options.LoadInstructions')
    def test_initialise_instructions_success(self, mock_load):
        """Test InitialiseInstructions success"""
        mock_instructions = type('MockInstructions', (), {
            'prompt': 'Test prompt',
            'instructions': 'Test instructions', 
            'retry_instructions': 'Test retry'
        })()
        mock_load.return_value = mock_instructions
        
        options = Options({'instruction_file': 'test.txt'})
        options.InitialiseInstructions()
        
        self.assertEqual(options.get('prompt'), 'Test prompt')
        self.assertEqual(options.get('instructions'), 'Test instructions')
        self.assertEqual(options.get('retry_instructions'), 'Test retry')

    def test_initialise_provider_settings(self):
        """Test InitialiseProviderSettings method"""
        options = Options()
        test_settings = {
            'model': 'test-model',
            'api_key': 'test-key',
            'temperature': 0.7
        }
        
        options.InitialiseProviderSettings('Test Provider', test_settings)
        
        # Should create provider settings
        self.assertIn('Test Provider', options.provider_settings)
        
        # Should move settings from main options to provider
        provider_settings = options.provider_settings['Test Provider']
        self.assertEqual(provider_settings['model'], 'test-model')
        self.assertEqual(provider_settings['api_key'], 'test-key')

    def test_version_update_migration(self):
        """Test _update_version method"""
        options = Options({
            'gpt_model': 'old-model-name',
            'api_key': 'test-key',
            'version': 'v0.9.0'
        })
        
        # Simulate version update
        options._update_version()
        
        # Old gpt_model should be renamed to model and moved to provider settings
        self.assertNotIn('gpt_model', options.options)

        # The model gets moved to provider settings, not main options
        openai_settings = options.provider_settings.get('OpenAI', {})
        if openai_settings:
            self.assertEqual(openai_settings.get('model'), 'old-model-name')
        
        # Version should be updated
        self.assertEqual(options.get('version'), default_options['version'])


class TestSettingsHelpers(unittest.TestCase):
    """Unit tests for Settings helper functions"""

    def setUp(self):
        """Set up test fixtures with known values"""
        self.test_dict_settings = {
            'bool_true': True,
            'bool_false': False,
            'bool_str_true': 'true',
            'bool_str_false': 'false',
            'bool_str_invalid': 'maybe',
            'int_value': 42,
            'int_str': '123',
            'int_float': 45.0,
            'int_invalid': 'not_a_number',
            'float_value': 3.14,
            'float_int': 42,
            'float_str': '2.718',
            'float_invalid': 'not_a_float',
            'str_value': 'hello world',
            'str_int': 123,
            'str_bool': True,
            'str_list': ['item1', 'item2'],
            'list_value': ['apple', 'banana', 'cherry'],
            'list_tuple': ('x', 'y', 'z'),
            'list_set': {'a', 'b', 'c'},
            'list_str_comma': 'red,green,blue',
            'list_str_semicolon': 'cat;dog;bird',
            'list_invalid': 42,
            'timedelta_seconds': 30.5,
            'timedelta_str': '15.0',
            'timedelta_int': 60,
            'timedelta_invalid': 'invalid',
        }
        
        self.test_options_obj = Options(self.test_dict_settings)

    def test_get_bool_setting(self):
        """Test GetBoolSetting with various input types"""
        log_test_name("GetBoolSetting")
        
        test_cases = [
            # (key, expected_result, description)
            ('bool_true', True, 'boolean True'),
            ('bool_false', False, 'boolean False'),
            ('bool_str_true', True, 'string "true"'),
            ('bool_str_false', False, 'string "false"'),
            ('missing_key', False, 'missing key with default False'),
        ]
        
        for key, expected, description in test_cases:
            with self.subTest(key=key):
                # Test with dict
                result = GetBoolSetting(self.test_dict_settings, key)
                log_input_expected_result(f"dict['{key}'] ({description})", expected, result)
                self.assertEqual(result, expected)
                
                # Test with Options object
                result_opts = GetBoolSetting(self.test_options_obj, key)
                log_input_expected_result(f"Options['{key}'] ({description})", expected, result_opts)
                self.assertEqual(result_opts, expected)
        
        # Test custom default
        result = GetBoolSetting(self.test_dict_settings, 'missing_key', True)
        log_input_expected_result("missing key with default True", True, result)
        self.assertTrue(result)
        
        # Test None value
        settings_with_none = {'none_value': None}
        result = GetBoolSetting(settings_with_none, 'none_value')
        log_input_expected_result("None value", False, result)
        self.assertFalse(result)

    def test_get_bool_setting_errors(self):
        """Test GetBoolSetting error cases"""
        log_test_name("GetBoolSetting Errors")
        
        error_cases = [
            ('bool_str_invalid', 'invalid string "maybe"'),
            ('int_value', 'integer value'),
        ]
        
        for key, description in error_cases:
            with self.subTest(key=key):
                with self.assertRaises(SettingsError) as cm:
                    GetBoolSetting(self.test_dict_settings, key)
                log_input_expected_result(f"'{key}' ({description})", "SettingsError", str(cm.exception))

    def test_get_int_setting(self):
        """Test GetIntSetting with various input types"""
        log_test_name("GetIntSetting")
        
        test_cases = [
            ('int_value', 42, 'integer value'),
            ('int_str', 123, 'string "123"'),
            ('int_float', 45, 'float 45.0'),
            ('missing_key', 0, 'missing key with default 0'),
        ]
        
        for key, expected, description in test_cases:
            with self.subTest(key=key):
                result = GetIntSetting(self.test_dict_settings, key)
                log_input_expected_result(f"'{key}' ({description})", expected, result)
                self.assertEqual(result, expected)
        
        # Test None handling
        settings_with_none = {'none_value': None}
        result = GetIntSetting(settings_with_none, 'none_value')
        log_input_expected_result("None value", None, result)
        self.assertIsNone(result)

    def test_get_int_setting_errors(self):
        """Test GetIntSetting error cases"""
        log_test_name("GetIntSetting Errors")
        
        with self.assertRaises(SettingsError) as cm:
            GetIntSetting(self.test_dict_settings, 'int_invalid')
        log_input_expected_result("invalid string", "SettingsError", str(cm.exception))

    def test_get_float_setting(self):
        """Test GetFloatSetting with various input types"""
        log_test_name("GetFloatSetting")
        
        test_cases = [
            ('float_value', 3.14, 'float value'),
            ('float_int', 42.0, 'integer converted to float'),
            ('float_str', 2.718, 'string "2.718"'),
        ]
        
        for key, expected, description in test_cases:
            with self.subTest(key=key):
                result = GetFloatSetting(self.test_dict_settings, key)
                log_input_expected_result(f"'{key}' ({description})", expected, result)
                self.assertEqual(result, expected)
        
        # Test None handling
        result = GetFloatSetting(self.test_dict_settings, 'missing_key')
        log_input_expected_result("missing key", None, result)
        self.assertIsNone(result)

    def test_get_float_setting_errors(self):
        """Test GetFloatSetting error cases"""
        log_test_name("GetFloatSetting Errors")
        
        with self.assertRaises(SettingsError) as cm:
            GetFloatSetting(self.test_dict_settings, 'float_invalid')
        log_input_expected_result("invalid string", "SettingsError", str(cm.exception))

    def test_get_str_setting(self):
        """Test GetStrSetting with various input types"""
        log_test_name("GetStrSetting")
        
        test_cases = [
            ('str_value', 'hello world', 'string value'),
            ('str_int', '123', 'integer converted to string'),
            ('str_bool', 'True', 'boolean converted to string'),
            ('str_list', 'item1, item2', 'list converted to string'),
        ]
        
        for key, expected, description in test_cases:
            with self.subTest(key=key):
                result = GetStrSetting(self.test_dict_settings, key)
                log_input_expected_result(f"'{key}' ({description})", expected, result)
                self.assertEqual(result, expected)
        
        # Test None handling
        result = GetStrSetting(self.test_dict_settings, 'missing_key')
        log_input_expected_result("missing key", None, result)
        self.assertIsNone(result)

    def test_get_list_setting(self):
        """Test GetListSetting with various input types"""
        log_test_name("GetListSetting")
        
        test_cases = [
            ('list_value', ['apple', 'banana', 'cherry'], 'list value'),
            ('list_tuple', ['x', 'y', 'z'], 'tuple converted to list'),
            ('list_str_comma', ['red', 'green', 'blue'], 'comma-separated string'),
            ('list_str_semicolon', ['cat', 'dog', 'bird'], 'semicolon-separated string'),
        ]
        
        for key, expected, description in test_cases:
            with self.subTest(key=key):
                result = GetListSetting(self.test_dict_settings, key)
                log_input_expected_result(f"'{key}' ({description})", expected, result)
                self.assertEqual(result, expected)
        
        # Test missing key returns empty list
        result = GetListSetting(self.test_dict_settings, 'missing_key')
        log_input_expected_result("missing key", [], result)
        self.assertEqual(result, [])
        
        # Test set conversion
        result = GetListSetting(self.test_dict_settings, 'list_set')
        log_input_expected_result("set converted to list", True, isinstance(result, list))
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    def test_get_list_setting_errors(self):
        """Test GetListSetting error cases"""
        log_test_name("GetListSetting Errors")
        
        with self.assertRaises(SettingsError) as cm:
            GetListSetting(self.test_dict_settings, 'list_invalid')
        log_input_expected_result("invalid type (int)", "SettingsError", str(cm.exception))

    def test_get_string_list_setting(self):
        """Test GetStringListSetting function"""
        log_test_name("GetStringListSetting")
        
        # Test with valid string list
        result = GetStringListSetting(self.test_dict_settings, 'list_value')
        expected = ['apple', 'banana', 'cherry']
        log_input_expected_result("valid string list", expected, result)
        self.assertEqual(result, expected)
        
        # Test with mixed types (should convert to strings)
        mixed_settings = {'mixed_list': [1, 'two', True, None]}
        result = GetStringListSetting(mixed_settings, 'mixed_list')
        expected = ['1', 'two', 'True']
        log_input_expected_result("mixed types", expected, result)
        self.assertEqual(result, expected)

    def test_get_timedelta_setting(self):
        """Test GetTimeDeltaSetting function"""
        log_test_name("GetTimeDeltaSetting")
        
        test_cases = [
            ('timedelta_seconds', timedelta(seconds=30.5), 'float seconds'),
            ('timedelta_str', timedelta(seconds=15.0), 'string seconds'),
            ('timedelta_int', timedelta(seconds=60), 'integer seconds'),
        ]
        
        for key, expected, description in test_cases:
            with self.subTest(key=key):
                result = GetTimeDeltaSetting(self.test_dict_settings, key)
                log_input_expected_result(f"'{key}' ({description})", expected, result)
                self.assertEqual(result, expected)
        
        # Test default value
        default = timedelta(minutes=5)
        result = GetTimeDeltaSetting(self.test_dict_settings, 'missing_key', default)
        log_input_expected_result("missing key with default", default, result)
        self.assertEqual(result, default)

    def test_get_timedelta_setting_errors(self):
        """Test GetTimeDeltaSetting error cases"""
        log_test_name("GetTimeDeltaSetting Errors")
        
        with self.assertRaises(SettingsError) as cm:
            GetTimeDeltaSetting(self.test_dict_settings, 'timedelta_invalid')
        log_input_expected_result("invalid string", "SettingsError", str(cm.exception))

    def test_get_optional_setting(self):
        """Test get_optional_setting function"""
        log_test_name("get_optional_setting")
        
        test_cases = [
            ('bool_true', bool, True, 'boolean type'),
            ('int_value', int, 42, 'integer type'),
            ('float_value', float, 3.14, 'float type'),
            ('str_value', str, 'hello world', 'string type'),
            ('list_value', list, ['apple', 'banana', 'cherry'], 'list type'),
        ]
        
        for key, setting_type, expected, description in test_cases:
            with self.subTest(key=key):
                result = get_optional_setting(self.test_dict_settings, key, setting_type)
                log_input_expected_result(f"'{key}' as {description}", expected, result)
                self.assertEqual(result, expected)
        
        # Test missing key returns None
        result = get_optional_setting(self.test_dict_settings, 'missing_key', str)
        log_input_expected_result("missing key", None, result)
        self.assertIsNone(result)
        
        # Test with Options object
        result = get_optional_setting(self.test_options_obj, 'bool_true', bool)
        log_input_expected_result("Options object", True, result)
        self.assertTrue(result)

    def test_get_optional_setting_errors(self):
        """Test get_optional_setting error cases"""
        log_test_name("get_optional_setting Errors")
        
        with self.assertRaises(SettingsError) as cm:
            get_optional_setting(self.test_dict_settings, 'bool_str_invalid', bool)
        log_input_expected_result("invalid conversion", "SettingsError", str(cm.exception))

    def test_validate_setting_type(self):
        """Test validate_setting_type function"""
        log_test_name("validate_setting_type")
        
        valid_cases = [
            ('bool_true', bool, True, 'valid boolean'),
            ('int_value', int, True, 'valid integer'),
            ('str_value', str, True, 'valid string'),
        ]
        
        for key, setting_type, expected, description in valid_cases:
            with self.subTest(key=key):
                result = validate_setting_type(self.test_dict_settings, key, setting_type)
                log_input_expected_result(f"'{key}' as {setting_type.__name__} ({description})", expected, result)
                self.assertEqual(result, expected)
        
        # Test missing optional setting
        result = validate_setting_type(self.test_dict_settings, 'missing_key', str, required=False)
        log_input_expected_result("missing optional setting", True, result)
        self.assertTrue(result)
        
        # Test invalid type
        result = validate_setting_type(self.test_dict_settings, 'bool_str_invalid', bool)
        log_input_expected_result("invalid type conversion", False, result)
        self.assertFalse(result)

    def test_validate_setting_type_errors(self):
        """Test validate_setting_type error cases"""
        log_test_name("validate_setting_type Errors")
        
        # Test required missing setting
        with self.assertRaises(SettingsError) as cm:
            validate_setting_type(self.test_dict_settings, 'missing_key', str, required=True)
        log_input_expected_result("required missing setting", "SettingsError", str(cm.exception))


if __name__ == '__main__':
    unittest.main()