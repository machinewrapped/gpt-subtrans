"""
Example of using gpt-subtrans as a library for subtitle translation.
"""

from PySubtitle.Options import Options
from PySubtitle.SubtitleFile import SubtitleFile
from PySubtitle.SubtitleProject import SubtitleProject
from PySubtitle.TranslationProvider import TranslationProvider
from PySubtitle.SubtitleTranslator import SubtitleTranslator
import tempfile
import os


def example_translation():
    """Example showing how to use gpt-subtrans as a library."""
    
    # Create a simple SRT content for testing
    srt_content = """1
00:00:01,000 --> 00:00:03,000
Hello, how are you?

2
00:00:04,000 --> 00:00:06,000
I'm fine, thank you.

3
00:00:07,000 --> 00:00:09,000
What's your name?
"""
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write(srt_content)
        temp_srt_path = f.name
    
    try:
        # Step 1: Create options for translation
        options = Options()
        options.options['target_language'] = "Spanish"
        options.options['provider'] = "OpenAI"
        options.options['model'] = "gpt-4o"
        # Note: You would set your API key here or in environment variable
        # options.options['api_key'] = "your-openai-api-key"
        
        print("Created options for Spanish translation")
        
        # Step 2: Load subtitle file
        subtitle_file = SubtitleFile(temp_srt_path)
        print(f"Loaded subtitle file with {subtitle_file.linecount} lines")
        
        # Step 3: Create a translation project
        project = SubtitleProject(options, subtitle_file)
        print("Created translation project")
        
        # Step 4: Create translator (note: requires valid API key to actually translate)
        # translator = SubtitleTranslator(options)
        # project.TranslateSubtitles(translator)
        
        print("Library setup complete!")
        print("To perform actual translation, set up API credentials and uncomment translation lines")
        
        return True
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_srt_path):
            os.unlink(temp_srt_path)


if __name__ == "__main__":
    example_translation()