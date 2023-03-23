import os
import logging
import pysrt
from pysrt import SubRipFile
from PySubtitleGPT.Helpers import UnbatchScenes
from PySubtitleGPT.Subtitle import Subtitle
from PySubtitleGPT.SubtitleTranslator import SubtitleTranslator

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')
fallback_encoding = os.getenv('DEFAULT_ENCODING', 'iso-8859-1')

# High level class for manipulating subtitle files
class SubtitleFile:
    def __init__(self, filename = None):
        self.filename = filename
        self.subtitles = None
        self.translations = None
        self.context = {}
        self._scenes = []

    @property
    def has_subtitles(self):
        return self.linecount > 0 or self.scenecount > 0
    
    @property
    def linecount(self):
        return len(self.subtitles) if self.subtitles else 0
    
    @property
    def scenecount(self):
        return len(self.scenes) if self.scenes else 0
    
    @property
    def scenes(self):
        return self._scenes

    @scenes.setter
    def scenes(self, scenes):
        self._scenes = scenes
        self.subtitles, self.translations, _ = UnbatchScenes(scenes)

    # Load subtitles from an SRT file
    def LoadSubtitles(self, filename):
        if not self.filename:
            self.filename = f"{os.path.basename(filename)}-ChatGPT.srt"

        try:
            srt = pysrt.open(filename)
            
        except UnicodeDecodeError as e:
            srt = pysrt.open(filename, encoding=fallback_encoding)

        self.subtitles = [ Subtitle(item) for item in srt ]
        
    # Write original subtitles to an SRT file
    def SaveSubtitles(self, filename = None):
        self.filename = filename or self.filename 
        if not self.filename:
            raise ValueError("No filename set")

        srtfile = SubRipFile(items=self.subtitles)
        srtfile.save(filename)

    # Write translated subtitles to an SRT file
    def SaveTranslation(self, filename = None):
        filename = filename or self.filename 
        if not filename:
            raise ValueError("No filename set")

        logging.info(f"Saving translation to {str(filename)}")

        srtfile = SubRipFile(items=self.translations)
        srtfile.save(filename)

    # Translate subtitles using the provided options
    def Translate(self, options, project):
        self.context = {
            'synopsis': options.get('synopsis', ""),
            'characters': options.get('characters', ""),
            'instructions': options.get('instructions', ""),
        }

        self.substitutions = options.get('substitutions')

        # Prime new project files
        if project.write_project:
            project.WriteProjectFile(self)

        try:
            #Perform the translation
            translator = SubtitleTranslator(options, project)
    
            self._scenes = translator.TranslateSubtitles(self.subtitles, self.context)

            self.SaveTranslation()

        except Exception as e:
            logging.error(f"Failed to translate subtitles")
            raise

    def AddScene(self, scene):
        self.scenes.append(scene)

        logging.debug("Added a new scene")
