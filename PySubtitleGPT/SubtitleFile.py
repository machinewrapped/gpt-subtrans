import os
import logging
import pysrt
from pysrt import SubRipFile
from PySubtitleGPT import SubtitleScene
from PySubtitleGPT.Helpers import ParseCharacters, ParseSubstitutions, UnbatchScenes
from PySubtitleGPT.Subtitle import Subtitle
from PySubtitleGPT.SubtitleBatcher import SubtitleBatcher
from PySubtitleGPT.SubtitleError import TranslationError
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

    def LoadSubtitles(self, filename):
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
    def SaveSubtitles(self, filename = None):
        self.filename = filename or self.filename 
        if not self.filename:
            raise ValueError("No filename set")

        srtfile = SubRipFile(items=self.subtitles)
        srtfile.save(filename)

    def SaveTranslation(self, filename = None):
        """
        Write translated subtitles to an SRT file
        """
        filename = filename or self.filename 
        if not filename:
            raise ValueError("No filename set")
        
        if not self.translations:
            logging.error("No subtitles translated")
            return

        logging.info(f"Saving translation to {str(filename)}")

        srtfile = SubRipFile(items=self.translations)
        srtfile.save(filename)

    def UpdateContext(self, options):
        """
        Update the project context from options,
        and set any unspecified options from the project context.
        """
        if hasattr(options, 'options'):
            self.UpdateContext(options.options)
            return
        
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

        if isinstance(context['characters'], str):
            context['characters'] = ParseCharacters(context['characters'])

        if isinstance(context['substitutions'], str):
            context['substitutions'] = ParseSubstitutions(context['substitutions'])

        # Update the context dictionary with matching fields from options, and vice versa
        for key in context.keys():
            if options.get(key):
                context[key] = options[key]
            if context[key]:
                options[key] = context[key]

        self.context = context

    def Translate(self, options, project):
        """
        Translate subtitles using the provided options
        """
        self.UpdateContext(options)

        translator = SubtitleTranslator(options, project)

        self.scenes = translator.TranslateSubtitles(self.subtitles, self.context)

    def TranslateBatch(self, batch_number, options):
        """
        Translate a batch of subtitles using the provided options
        """
        if not self.scenes:
            raise TranslationError("Subtitles have not been batched")

        scene, batch = self.FindBatch(batch_number)
        if not scene:
            raise TranslationError(f"Cannot find scene with batch {batch_number} to translate it")

        # TODO: Really need to build context from the entire scene
        context = batch.context
        context['scene_number'] = scene.number

        # TODO: eliminate the dependency on SubtitleProject by using events/observer
        translator = SubtitleTranslator(options, self.project)

        batches = [ batch ]
        translator.TranslateBatches(scene, batches, context)

    def AutoBatch(self, options, project):
        """
        Divide subtitles into scenes and batches based on threshold options
        """
        batcher = SubtitleBatcher(options)

        self.scenes = batcher.BatchSubtitles(self.subtitles)

        if project:
            project.UpdateProjectFile(self.scenes)

    def AddScene(self, scene):
        self.scenes.append(scene)

        logging.debug("Added a new scene")

    def FindBatch(self, batch_number):
        for scene in self.scenes:
            for batch in scene.batches:
                if batch.number == batch_number:
                    return scene, batch
                
        return None, None