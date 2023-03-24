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
        self.translations = {}

    def ProcessTranslation(self):
        """
        Extract subtitle lines from a batched translation, using the
        pre-defined pattern to match each line, or a list of fallbacks
        if the match fails.
        """
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

