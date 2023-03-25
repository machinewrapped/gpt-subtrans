import logging
import re

from PySubtitleGPT.Helpers import MergeTranslations
from PySubtitleGPT.Subtitle import Subtitle
from PySubtitleGPT.ChatGPTTranslation import ChatGPTTranslation

template = re.compile(r"<translation\s+start='(?P<start>[\d:,]+)'\s+end='(?P<end>[\d:,]+)'>(?P<body>[\s\S]*?)<\/translation>")

#TODO: update fallback patterns with start and end groups
fallback_patterns = [
    re.compile(r"<translation\s+index='(?P<index>.+?)'\s+start='(?P<start>[\d:,]+)'\s+end='(?P<end>[\d:,]+)'>\s*(?P<body>.*?)\s*<\/translation>", re.MULTILINE),
    re.compile(r'<translation\s*line=(\d+)\s*>(?:")?(.*?)(?:")?\s*(?:" /)?</translation>', re.MULTILINE),
    re.compile(r'<original\s*line=(\d+)\s*>(?:")?(.*?)(?:")?\s*(?:" /)?</original>', re.MULTILINE),
    re.compile(r'<line\s*number=(\d+).+?translation=(?:")?(.*?)(?:")?\s*(?:" /)?>', re.MULTILINE),
    re.compile(r'<line number=(\d+)>(?:")?(.*?)(?:")?</line>', re.MULTILINE),
    re.compile(r'(\d+)[:.]\s*"(.+?)"',  re.MULTILINE),
    re.compile(r'(?:^|\n|\\n)(\d+)[:.]\s*(.+?)(?:$|\n|\\n)', re.MULTILINE),
    ]


class ChatGPTTranslationParser:
    """
    Extract translated subtitles from a ChatGPT completion 
    """
    def __init__(self, translation):
        self.text = translation.text if isinstance(translation, ChatGPTTranslation) else str(translation) 
        self.translated = []
    def __init__(self, options):
        self.options = options
        self.text = None
        self.translations = {}
        self.translated = []

    def ProcessTranslation(self):
    def ProcessChatGPTResponse(self, translation):
        """
        Extract subtitle lines from a batched translation, using the
        pre-defined pattern to match each line, or a list of fallbacks
        if the match fails.
        """
        self.text = translation.text if isinstance(translation, ChatGPTTranslation) else str(translation) 

        if not self.text:
            raise ValueError("No translated text provided")
        
        matches = template.findall(self.text, re.DOTALL)

        logging.debug(f"Matches: {str(matches)}")

        self.translations = { 
            match[0]:
                Subtitle.from_match(match)
            for match in matches 
            }
        
        if not self.translations:
            return None

        self.translated = MergeTranslations(self.translated, self.translations.values())
        
        return self.translated

    def MatchTranslations(self, subtitles):
        """
        Match lines in the translation with the original subtitles
        """
        if not subtitles:
            raise ValueError("Original subtitles not provided")
        
        unmatched = []

        #Try to match subtitles on start and end times instead
        for item in subtitles:
            translation = self.translations.get(item.key)
            if translation:
                translation.index = item.index
                item.translation = translation.text
            else:
                unmatched.append(item)

        return unmatched

    def ValidateTranslations(self):
        """
        Check if the translation seems at least plausible
        """
        if not self.translated:
            raise NoTranslationError(f"Failed to extract any subtitles from {self.text}", self.text)
        
        max_characters = self.options.get('max_characters')
        max_newlines = self.options.get('max_newlines')

        too_long = []
        too_many_newlines = []

        for line in self.translated:
            if len(line.text) > max_characters:
                too_long.append(line)

            if line.text.count('\n') > max_newlines:
                too_many_newlines.append(line)

        if too_long:
            raise LineTooLongError(f"One or more lines exceeded {max_characters} characters", too_long)

        if too_many_newlines:
            raise TooManyNewlinesError(f"One or more lines contain more than {max_newlines} newlines", too_many_newlines)


