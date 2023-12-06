import logging
import re

from PySubtitle.Options import Options
from PySubtitle.Helpers import IsTextContentEqual, MergeTranslations
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleError import NoTranslationError
from PySubtitle.SubtitleValidator import SubtitleValidator
from PySubtitle.Translation import Translation

default_pattern = re.compile(r"#(?P<number>\d+)(?:[\s\r\n]+Original>[\s\r\n]+(?P<original>[\s\S]*?))?[\s\r\n]*(?:Translation>(?:[\s\r\n]+(?P<body>[\s\S]*?))?(?:(?=\n{2,})|\Z))", re.MULTILINE)

regex_patterns = [
    default_pattern,
    re.compile(r"#(?P<number>\d+)(?:[\s\r\n]+Original[>:][\s\r\n]+(?P<original>[\s\S]*?))?[\s\r\n]*(?:Translation[>:](?:[\s\r\n]+(?P<body>[\s\S]*?))?(?:(?=\n{2,})|\Z))", re.MULTILINE),
    re.compile(r"#(?P<number>\d+)(?:[\s\r\n]+Original[>:][\s\r\n]+(?P<original>[\s\S]*?))?[\s\r\n]*Translation[>:][\s\r\n]+(?P<body>[\s\S]*?)(?=(?:\n{2,}#)|\Z)", re.MULTILINE),
    re.compile(r"#(?P<number>\d+)(?:[\s\r\n]*Original[>:][\s\r\n]*(?P<original>[\s\S]*?))?[\s\r\n]*Translation[>:][\s\r\n]*(?P<body>[\s\S]*?)(?=(?:\n{2,}#)|\Z)", re.MULTILINE),
    re.compile(r"#(?P<number>\d+)(?:[\s\r\n]+(?P<body>[\s\S]*?))?(?:(?=\n{2,})|\Z)", re.MULTILINE)  # Just the number and translation
    ]


class TranslationParser:
    """
    Extract translated subtitles from a completion 
    """
    def __init__(self, options : Options):
        self.options = options
        self.text = None
        self.translations = {}
        self.translated = []

    def ProcessTranslation(self, translation : Translation):
        """
        Extract lines from a batched translation, using the
        pre-defined pattern to match each line, or a list of fallbacks
        if the match fails.
        """
        self.text = translation.text if isinstance(translation, Translation) else str(translation) 

        if not self.text:
            raise ValueError("No translated text provided")
        
        for template in regex_patterns:
            matches = self.FindMatches(f"{self.text}\n\n", template)

            if matches:
                break

        logging.debug(f"Matches: {str(matches)}")

        subs = [SubtitleLine.FromDictionary(match) for match in matches]
        self.translations = { 
            sub.key: sub for sub in subs 
            }
        
        if not self.translations:
            return None

        self.translated = MergeTranslations(self.translated, self.translations.values())
        
        return self.translated

    def FindMatches(self, text, template):
        """
        re.findall has some very unhelpful behaviour, so we use finditer instead.
        """
        return [{ 
            'body': match.group('body'),
            'number': match.groupdict().get('number'),
            'start': match.groupdict().get('start'), 
            'end': match.groupdict().get('end'), 
            'original': match.groupdict().get('original')
            } for match in template.finditer(text)]

    def MatchTranslations(self, originals : list[SubtitleLine]):
        """
        Match lines in the translation with the original subtitles
        """
        if not originals:
            raise ValueError("Original subtitles not provided")
        
        unmatched = []

        for item in originals:
            translation = self.translations.get(item.key)
            if translation:
                translation.number = item.number
                translation.start = item.start
                translation.end = item.end

                if translation.original and IsTextContentEqual(translation.text, item.text):
                    # Check for swapped original & translation
                    translation.text = translation.original
                    translation.original = item.text

                item.translation = translation.text
            else:
                item.translation = None
                unmatched.append(item)

        if unmatched:
            self.TryFuzzyMatches(unmatched)

        self.translated = MergeTranslations(self.translated, self.translations.values())

        return self.translated, unmatched

    def TryFuzzyMatches(self, unmatched : list [SubtitleLine]):
        """
        Try to match translations to their source lines using heuristics
        """
        possible_matches : list[(SubtitleLine,SubtitleLine)] = []
        for item in (item for item in unmatched if item.number is not None):
            for translation in self.translations.values():
                if translation.original:
                    if IsTextContentEqual(translation.original, item.text):
                        # A match on the original text is pretty compelling
                        possible_matches.append((item, translation))
                        continue
                    elif IsTextContentEqual(translation.text, item.text):
                        # GPT sometimes swaps the original and translated text - swap them back
                        translation.text = translation.original
                        translation.original = item.text
                        possible_matches.append((item, translation))
                        continue

                    #TODO: check for merged lines

                # This is not very convincing logic but let's try it
                if translation.start <= item.start and translation.end >= item.end:
                    possible_matches.append((item, translation))

        if possible_matches:
            for item, translation in possible_matches:
                logging.warn(f"Found fuzzy match for line {item.number} in translations")
                item.translation = f"#Fuzzy: {translation.text}"
                #unmatched.remove(item)

    def ValidateTranslations(self):
        """
        Check if the translation seems at least plausible
        """
        if not self.translated:
            raise NoTranslationError(f"Failed to extract any translations from {self.text}", self.text)
        
        validator = SubtitleValidator(self.options)
        validator.ValidateTranslations(self.translated)