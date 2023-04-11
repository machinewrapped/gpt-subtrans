import os
import logging
import pysrt
from pysrt import SubRipFile
from PySubtitleGPT.Helpers import ParseCharacters, ParseSubstitutions, UnbatchScenes
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.Subtitle import Subtitle
from PySubtitleGPT.SubtitleBatcher import SubtitleBatcher
from PySubtitleGPT.SubtitleError import TranslationError

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')
fallback_encoding = os.getenv('DEFAULT_ENCODING', 'iso-8859-1')

# High level class for manipulating subtitle files
class SubtitleFile:
    def __init__(self, filename = None):
        self.filename = filename
        self.subtitles : list[Subtitle] = None
        self.translated : list[Subtitle] = None
        self.context = {}
        self._scenes : list[SubtitleScene] = []

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
        self.subtitles, self.translated, _ = UnbatchScenes(scenes)
        self.Renumber()

    def GetScene(self, scene_number : int):
        if not self.scenes:
            raise ValueError("Subtitles have not been batched")
        
        matches = [scene for scene in self.scenes if scene.number == scene_number ]
        if not matches:
            raise ValueError(f"Scene {scene_number} does not exist")
        
        if len(matches) > 1:
            raise TranslationError(f"There is more than one scene {scene_number}!")
        
        return matches[0]

    def LoadSubtitles(self, filename : str):
        """
        Load subtitles from an SRT file
        """
        if not self.filename:
            inputname, _ = os.path.splitext(os.path.basename(filename))
            self.filename = f"{inputname}-ChatGPT.srt"

        try:
            srt = pysrt.open(filename)
            
        except UnicodeDecodeError as e:
            srt = pysrt.open(filename, encoding=fallback_encoding)

        self.subtitles = [ Subtitle(item) for item in srt ]
        
    # Write original subtitles to an SRT file
    def SaveSubtitles(self, filename : str = None):
        self.filename = filename or self.filename 
        if not self.filename:
            raise ValueError("No filename set")

        srtfile = SubRipFile(items=self.subtitles)
        srtfile.save(filename)

    def SaveTranslation(self, filename : str = None):
        """
        Write translated subtitles to an SRT file
        """
        filename = filename or self.filename 
        if not filename:
            raise ValueError("No filename set")
        
        if not self.translated:
            logging.error("No subtitles translated")
            return

        logging.info(f"Saving translation to {str(filename)}")

        srtfile = SubRipFile(items=self.translated)
        srtfile.save(filename)

    def UpdateContext(self, options):
        """
        Update the project context from options,
        and set any unspecified options from the project context.
        """
        if hasattr(options, 'options'):
            return self.UpdateContext(options.options)
    
        context = {
            'gpt_model': "",
            'gpt_prompt': "",
            'instructions': "",
            'movie_name': "",
            'synopsis': "",
            'characters': None,
            'substitutions': None
        }

        if self.context:
            context = {**context, **self.context}

        if isinstance(context.get('characters'), str):
            context['characters'] = ParseCharacters(context['characters'])

        if isinstance(context.get('substitutions'), str):
            context['substitutions'] = ParseSubstitutions(context['substitutions'])

        # Update the context dictionary with matching fields from options, and vice versa
        for key in context.keys():
            if options.get(key):
                context[key] = options[key]
            if context[key]:
                options[key] = context[key]


    def AutoBatch(self, options):
        """
        Divide subtitles into scenes and batches based on threshold options
        """
        batcher = SubtitleBatcher(options)

        self.scenes = batcher.BatchSubtitles(self.subtitles)

    def AddScene(self, scene):
        self.scenes.append(scene)

        logging.debug("Added a new scene")

    def Renumber(self):
        """
        Force monotonic numbering of scenes, batches, subtitles and translated subtitles
        """
        for scene_index, scene in enumerate(self.scenes):
            scene.number = scene_index + 1
            for batch_index, batch in enumerate(scene.batches):
                batch.number = batch_index + 1
                batch.scene = scene.number

        for subtitle_index, subtitle in enumerate(self.subtitles):
            subtitle.index = subtitle_index + 1

        for translated_index, translated in enumerate(self.translated):
            translated.index = translated_index + 1
            #TODO: fix the index of any subtitles associated with us
