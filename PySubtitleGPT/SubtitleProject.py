import json
import os
import logging
import threading
from PySubtitleGPT.SubtitleTranslator import SubtitleTranslator
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleFile import SubtitleFile

from PySubtitleGPT.SubtitleSerialisation import SubtitleDecoder, SubtitleEncoder
from PySubtitleGPT.TranslationEvents import TranslationEvents

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')

class SubtitleProject:
    def __init__(self, options : Options):
        self.options = options.GetNonProjectSpecificOptions() if options else Options()
        self.subtitles : SubtitleFile = None
        self.events = TranslationEvents()
        self.projectfile = None
        self.needsupdate = False
        self.lock = threading.Lock()
        
        project_mode = options.get('project', '')
        if project_mode:
            project_mode = project_mode.lower() 

        self.read_project = project_mode in ["true", "read", "resume", "retranslate", "reparse"]
        self.write_project = project_mode in ["true", "write", "preview", "resume", "retranslate", "reparse"]
        self.update_project = self.write_project and not project_mode in ['reparse']
        self.load_subtitles = project_mode is None or project_mode in ["true", "write", "reload", "preview"]

        options.add('read_project', self.read_project)
        options.add('write_project', self.write_project)

        options.add('preview', project_mode in ["preview"])
        options.add('resume', project_mode in ["resume"])   #, "true"
        options.add('reparse', project_mode in ["reparse"])
        options.add('retranslate', project_mode in ["retranslate"])

        if self.update_project:
            self._start_autosave_thread

    def __del__(self):
        if self.update_project:
            self.stop_event.set()
            self.periodic_update_thread.join()

    def Initialise(self, filepath, outfilename = None):
        """
        Initialize the project by either loading an existing project file or creating a new one.
        Load the subtitles to be translated, either from the project file or the source file.

        :param filename: the path to the source subtitle file (in .srt format) to be translated
        """ 
        self.projectfile = self.GetProjectFilename(filepath or "subtitles")

        options : Options = self.options

        if self.read_project:
            # Try to load the project file
            subtitles = self.ReadProjectFile()

            if subtitles and subtitles.scenes:
                self.load_subtitles = False
                write_backup = options.get('write_backup', False)
                logging.info("Project file loaded, saving backup copy" if write_backup else "Project file loaded")
                if write_backup:
                    self.WriteBackupFile()
            else:
                logging.warning(f"Unable to read project file, starting afresh")
                self.load_subtitles = True

        if self.load_subtitles:
            # (re)load the source subtitle file if required
            subtitles = self.LoadSubtitleFile(filepath)

        if outfilename:
            subtitles.outputpath = outfilename

        if not subtitles.has_subtitles:
            raise ValueError(f"No subtitles to translate in {filepath}")

    def TranslateSubtitles(self):
        """
        Pass the subtitles to the translation engine.
        """
        if not self.subtitles:
            raise Exception("No subtitles to translate")
        
        # Prime new project files
        if self.write_project:
            self.WriteProjectFile()

        try:
            translator : SubtitleTranslator = SubtitleTranslator(self.subtitles, self.options)

            translator.events.preprocessed += self._on_preprocessed
            translator.events.batch_translated += self._on_batch_translated

            translator.TranslateSubtitles()

            self.subtitles.SaveTranslation()

        except Exception as e:
            if self.subtitles and self.options.get('stop_on_error'):
                self.subtitles.SaveTranslation()

            logging.error(f"Failed to translate subtitles")
            raise

    def TranslateScene(self, scene_number, batch_numbers = None):
        """
        Pass batches of subtitles to the translation engine.
        """
        if not self.subtitles:
            raise Exception("No subtitles to translate")

        try:
            translator : SubtitleTranslator = SubtitleTranslator(self.subtitles, self.options)

            translator.events.preprocessed += self._on_preprocessed
            translator.events.batch_translated += self._on_batch_translated

            scene = self.subtitles.GetScene(scene_number)

            translator.TranslateScene(scene, batch_numbers=batch_numbers)

            self.subtitles.SaveTranslation()

            return scene

        except Exception as e:
            if self.subtitles and self.options.get('stop_on_error'):
                self.subtitles.SaveTranslation()

            logging.error(f"Failed to translate subtitles")
            raise

    def GetProjectFilename(self, filename):
        name, ext = os.path.splitext(filename)
        if ext == 'subtrans':
            return filename
        return os.path.join(os.getcwd(), f"{name}.subtrans")
    
    def LoadSubtitleFile(self, filepath):
        """
        Load subtitles from an SRT file
        """
        with self.lock:
            self.subtitles = SubtitleFile()
            self.subtitles.LoadSubtitles(filepath)
            self.subtitles.UpdateContext(self.options)
            self.subtitles.project = self
        return self.subtitles

    def WriteProjectFile(self, projectfile = None):
        """
        Write a set of subtitles to a project file
        """
        with self.lock:
            if not self.subtitles:
                raise ValueError("Can't write project file, no subtitles")

            if not isinstance(self.subtitles, SubtitleFile):
                raise ValueError("Asked to write a project file with the wrong content type")

            if not self.subtitles.scenes:
                raise ValueError("Asked to write a project file with no scenes")

            projectfile = projectfile or self.projectfile

            logging.info(f"Writing project data to {str(projectfile)}")

            with open(projectfile, 'w', encoding=default_encoding) as f:
                project_json = json.dumps(self.subtitles, cls=SubtitleEncoder, ensure_ascii=False, indent=4)
                f.write(project_json)

    def WriteBackupFile(self):
        """
        Save a backup copy of the project
        """
        if self.subtitles and self.projectfile:
            self.WriteProjectFile(f"{self.projectfile}-backup")

    def ReadProjectFile(self):
        """
        Load scenes, subtitles and context from a project file
        """
        try:
            with self.lock:
                logging.info(f"Reading project data from {str(self.projectfile)}")

                with open(self.projectfile, 'r', encoding=default_encoding) as f:
                    subtitles: SubtitleFile = json.load(f, cls=SubtitleDecoder)

                subtitles.project = self
                self.subtitles = subtitles
                self.subtitles.UpdateContext(self.options)
                return subtitles

        except FileNotFoundError:
            logging.error(f"Project file {self.projectfile} not found")
            return None

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON file: {e}")
            return None

    def UpdateProjectFile(self):
        """
        Write current state of scenes to the project file
        """
        if self.update_project:
            if not self.subtitles:
                raise Exception("Unable to update project file, no subtitles")
            
            self.needsupdate = True
            # self.WriteProjectFile()

    def UpdateProjectOptions(self, options: dict):
        """
        Replace options if the provided dictionary has an entry with the same key
        """
        if not self.options:
            self.options = options
            return

        # Check if all values in "options" are the same as existing values in "self.options"
        if all(options.get(key) == self.options.get(key) for key in options.keys()):
            return

        with self.lock:
            # Update "self.options"
            self.options.update(options)

            if self.subtitles:
                self.subtitles.UpdateContext(self.options)

        self.WriteProjectFile()

    def _start_autosave_thread(self):
        self.stop_event = threading.Event()
        self.periodic_update_thread = threading.Thread(target=self._background_autosave)
        self.periodic_update_thread.daemon = True
        self.periodic_update_interval = 20  # Autosave interval in seconds
        self.periodic_update_thread.start()

    def _background_autosave(self):
        while not self.stop_event.is_set():
            if self.needsupdate:
                self.needsupdate = False
                self.WriteProjectFile()
            self.stop_event.wait(self.periodic_update_interval)

    def _on_preprocessed(self, scenes):
        logging.debug("Pre-processing finished")
        self.needsupdate = self.update_project
        self.events.preprocessed(scenes)

    def _on_batch_translated(self, batch):
        logging.debug("Batch translated")
        self.needsupdate = self.update_project
        self.events.batch_translated(batch)

    def _on_scene_translated(self, scene):
        logging.debug("Scene translated")
        self.subtitles.SaveTranslation()
        self.needsupdate = self.update_project
        self.events.scene_translated(scene)
