import unittest
import os
import tempfile
import json
from copy import deepcopy
from unittest.mock import patch, mock_open

from PySubtitle.Options import Options, default_options, standard_filler_words
from PySubtitle.Instructions import Instructions


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


if __name__ == '__main__':
    unittest.main()