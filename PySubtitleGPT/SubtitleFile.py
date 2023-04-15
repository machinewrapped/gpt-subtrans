import os
import logging
import pysrt
from pysrt import SubRipFile
from PySubtitleGPT.Helpers import ParseCharacters, ParseSubstitutions, UnbatchScenes
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.SubtitleLine import SubtitleLine
from PySubtitleGPT.SubtitleBatcher import SubtitleBatcher
from PySubtitleGPT.SubtitleError import TranslationError

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')
fallback_encoding = os.getenv('DEFAULT_ENCODING', 'iso-8859-1')

# High level class for manipulating subtitle files
class SubtitleFile:
    def __init__(self, filename = None):
        self.filename = filename
        self.originals : list[SubtitleLine] = None
        self.translated : list[SubtitleLine] = None
        self.context = {}
        self._scenes : list[SubtitleScene] = []

    @property
    def has_subtitles(self):
        return self.linecount > 0 or self.scenecount > 0
    
    @property
    def linecount(self):
        return len(self.originals) if self.originals else 0
    
    @property
    def scenecount(self):
        return len(self.scenes) if self.scenes else 0
    
    @property
    def scenes(self):
        return self._scenes

    @scenes.setter
    def scenes(self, scenes : list[SubtitleScene]):
        self._scenes = scenes
        self.originals, self.translated, _ = UnbatchScenes(scenes)
        self.Renumber()

    def GetScene(self, scene_number : int) -> SubtitleScene:
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

        self.originals = [ SubtitleLine(item) for item in srt ]
        
    # Write original subtitles to an SRT file
    def SaveOriginals(self, filename : str = None):
        self.filename = filename or self.filename 
        if not self.filename:
            raise ValueError("No filename set")

        srtfile = SubRipFile(items=self.originals)
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

        context['characters'] = ParseCharacters(context.get('characters'))
        options['characters'] = ParseCharacters(options.get('characters'))

        context['substitutions'] = ParseSubstitutions(context.get('substitutions'))
        options['substitutions'] = ParseSubstitutions(options.get('substitutions'))

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

        self.scenes = batcher.BatchSubtitles(self.originals)

    def AddScene(self, scene):
        self.scenes.append(scene)

        logging.debug("Added a new scene")

    def MergeScenes(self, scene_numbers: list[int]):
        """
        Merge several (sequential) scenes into one scene 
        """
        if not scene_numbers:
            raise ValueError("No scene numbers supplied to MergeScenes")

        scene_numbers = sorted(scene_numbers)
        if scene_numbers != list(range(scene_numbers[0], scene_numbers[0] + len(scene_numbers))):
            raise ValueError("Scene numbers to be merged are not sequential")

        scenes = [scene for scene in self.scenes if scene.number in scene_numbers]
        if len(scenes) != len(scene_numbers):
            raise ValueError(f"Could not find scenes {','.join(scene_numbers)}")

        # Merge all scenes into the first
        scenes[0].MergeScenes(scenes[1:])

        # Slice out the merged scenes
        start_index = self.scenes.index(scenes[0])
        end_index = self.scenes.index(scenes[-1])
        self.scenes = self.scenes[:start_index + 1] + self.scenes[end_index+1:]

        for number, scene in enumerate(self.scenes, start = 1):
            scene.number = number

    def MergeBatches(self, scene_number : int, batch_numbers: list[int]):
        """
        Merge several (sequential) batches from a scene into one batch 
        """
        if not batch_numbers:
            raise ValueError("No batch numbers supplied to MergeBatches")

        scene : SubtitleScene = next((scene for scene in self.scenes if scene.number == scene_number), None)
        if not scene:
            raise ValueError(f"Scene {str(scene_number)} not found")

        scene.MergeBatches(batch_numbers)

    def Renumber(self):
        """
        Force monotonic numbering of scenes, batches, lines and translated lines
        """
        for scene_number, scene in enumerate(self.scenes, start=1):
            scene.number = scene_number
            for batch_number, batch in enumerate(scene.batches, start=1):
                batch.number = batch_number
                batch.scene = scene.number

        # Renumber lines sequentially and remap translated indexes
        translated_map = { translated.number: translated for translated in self.translated }

        for number, line in enumerate(self.originals, start=1):
            if line.number in translated_map:
                translated = translated_map[line.number]
                translated.number = number
                del translated_map[line.number]

            line.number = number

