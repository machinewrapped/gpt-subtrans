# Using GPT-Subtrans as a Library

As of version 1.1.2, GPT-Subtrans can be installed and used as a Python library, allowing developers to integrate subtitle translation capabilities into their own applications.

## Installation

### Core functionality only
```bash
pip install gpt-subtrans
```

### With GUI support
```bash
pip install gpt-subtrans[gui]
```

### With specific provider support
```bash
pip install gpt-subtrans[openai]  # OpenAI/GPT models
pip install gpt-subtrans[gemini]  # Google Gemini
pip install gpt-subtrans[claude]  # Anthropic Claude
pip install gpt-subtrans[mistral] # Mistral AI
pip install gpt-subtrans[bedrock] # Amazon Bedrock
```

### With all optional dependencies
```bash
pip install gpt-subtrans[all]
```

## Basic Usage

```python
from PySubtitle.Options import Options
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.SubtitleTranslator import SubtitleTranslator

# Create options for translation
options = Options()
options.options['target_language'] = "Spanish"
options.options['provider'] = "OpenAI"
options.options['model'] = "gpt-4o"
options.options['api_key'] = "your-openai-api-key"

# Load subtitle file
subtitle_file = SubtitleFile("path/to/your/subtitles.srt")

# Create a translation project
project = SubtitleProject(options, subtitle_file)

# Create translator and perform translation
translator = SubtitleTranslator(options)
project.TranslateSubtitles(translator)

# Save the translated subtitles
project.WriteTranslation()
```

## Available Providers

```python
from PySubtitle.TranslationProvider import TranslationProvider

# List all available providers
providers = TranslationProvider.get_providers()
print(providers)

# Get a specific provider
provider = TranslationProvider.get_provider(options)
```

## Command Line Tools

When installed as a package, the following command-line tools become available:

- `gpt-subtrans` - OpenAI/GPT translation
- `gui-subtrans` - Launch the GUI application  
- `gemini-subtrans` - Google Gemini translation

Example:
```bash
gpt-subtrans subtitles.srt --target_language Spanish --apikey your-key
```

## Configuration

Options can be set programmatically or via environment variables:

```python
# Programmatic configuration
options = Options()
options.options['api_key'] = "your-key"
options.options['model'] = "gpt-4o"
options.options['temperature'] = 0.1

# Or use environment variables
import os
os.environ['OPENAI_API_KEY'] = "your-key"
os.environ['OPENAI_MODEL'] = "gpt-4o"
```

## Features Available as Library

- **Multiple Provider Support**: OpenAI, Google Gemini, Anthropic Claude, Mistral, Amazon Bedrock
- **Intelligent Batching**: Automatically groups subtitle lines for efficient translation
- **Scene Detection**: Identifies scene breaks for better context
- **Preprocessing**: Cleans up subtitles (especially useful for Whisper-generated ones)
- **Postprocessing**: Fixes common translation issues
- **Project Files**: Save and resume translation progress
- **Substitutions**: Replace specific terms in source or translation
- **Custom Instructions**: Provide context about the source material

## Advanced Usage

See the `examples/library_usage.py` file in the repository for a complete example demonstrating the library usage.

## Requirements

- Python 3.10+
- Core dependencies are installed automatically
- Provider-specific SDKs are optional extras

## Support

For library usage questions, please open an issue on the [GitHub repository](https://github.com/machinewrapped/gpt-subtrans).