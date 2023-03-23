import logging
import re

from pysrt import SubRipItem
from PySubtitleGPT.Helpers import MergeTranslations
from PySubtitleGPT.Subtitle import Subtitle
from PySubtitleGPT.ChatGPTTranslation import ChatGPTTranslation

template = re.compile(r"<translation\s+index='(?P<index>.+?)'\s+start='(?P<start>[\d:,]+)'\s+end='(?P<end>[\d:,]+)'>\s*(?P<body>.*?)\s*<\/translation>")

#TODO: update fallback patterns with start and end groups
fallback_patterns = [
    r'<translation\s*line=(\d+)\s*>(?:")?(.*?)(?:")?\s*(?:" /)?</translation>',
    r'<original\s*line=(\d+)\s*>(?:")?(.*?)(?:")?\s*(?:" /)?</original>',
    r'<line\s*number=(\d+).+?translation=(?:")?(.*?)(?:")?\s*(?:" /)?>',
    r'<line number=(\d+)>(?:")?(.*?)(?:")?</line>',
    r'(\d+)[:.]\s*"(.+?)"', 
    r'(?:^|\n|\\n)(\d+)[:.]\s*(.+?)(?:$|\n|\\n)',
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
        
        logging.debug(f"Response:\n{self.text}")

        matches = template.findall(self.text)
        results = { 
            match[0]:
                Subtitle.construct(match[0], match[1].strip(), match[2].strip(), match[3].strip())
            for match in matches 
            }
        
        if not results:
            raise Exception("Failed to extract translations from response")

        for index, values in results.items():
            try:
                index = int(index)

            except Exception as e:
                logging.error("Received non-numeric index field")

                #TODO figure out what to do if lines get merged
                indices = re.split(',|-', index)
                index = int(indices[0])

            self.translations[index] = values

        self.translated = MergeTranslations(self.translated, self.translations.values())
        
        return self.translated

    def MatchTranslations(self, subtitles):
        """
        Match lines in the translation with the original subtitles
        """
        if not subtitles:
            raise ValueError("Original subtitles not provided")
        
        untranslated = []

        #TODO match on start and end times instead
        for item in subtitles:
            translation = self.translations.get(item.index)
            if translation:
                item.translation = translation.text
            else:
                untranslated.append(item)

        return untranslated

