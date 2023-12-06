import json
import os
import logging
import threading
from PySubtitle.Helpers import GetOutputPath
from PySubtitle.SubtitleError import TranslationAbortedError
from PySubtitle.SubtitleTranslator import SubtitleTranslator
from PySubtitle.Options import Options
from PySubtitle.SubtitleFile import SubtitleFile

from PySubtitle.SubtitleSerialisation import SubtitleDecoder, SubtitleEncoder
from PySubtitle.TranslationEvents import TranslationEvents

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')

class SubtitleProject:
    def __init__(self, options : Options):
        self.options : Options = options or Options()
        self.subtitles : SubtitleFile = None
        self.events = TranslationEvents()
        self.projectfile = None
        self.needsupdate = False
        self.lock = threading.Lock()
        self.stop_event = None
        
        project_mode = self.options.get('project', '')
        if project_mode:
            project_mode = project_mode.lower() 

        self.read_project = project_mode in ["true", "read", "resume", "retranslate", "reparse"]
        self.write_project = project_mode in ["true", "write", "preview", "resume", "retranslate", "reparse"]
        self.update_project = self.write_project and not project_mode in ['reparse']
        self.load_subtitles = project_mode is None or project_mode in ["true", "write", "reload", "preview"]

        self.options.add('preview', project_mode in ["preview"])
        self.options.add('resume', project_mode in ["resume"])   #, "true"
        self.options.add('reparse', project_mode in ["reparse"])
        self.options.add('retranslate', project_mode in ["retranslate"])

        if self.update_project and options.get('autosave'):
            self._start_autosave_thread

    def __del__(self):
        if self.stop_event:
            self.stop_event.set()
            self.periodic_update_thread.join()

    def Initialise(self, filepath, outputpath = None):
        """
        Initialize the project by either loading an existing project file or creating a new one.
        Load the subtitles to be translated, either from the project file or the source file.

        :param filepath: the path to the project or a source subtitle file (in .srt format) to be translated
        :param outputpath: the path to write the translated subtitles too (a default path is used if None specified)
        """ 
        self.projectfile = self.GetProjectFilepath(filepath or "subtitles")
        if self.projectfile == filepath and not self.read_project:
            self.read_project = True
            self.write_project = True
            self.options.add('project', 'true')

        # Check if the project file exists
        if self.read_project and not os.path.exists(self.projectfile):
            logging.info(f"Project file {self.projectfile} does not exist")
            self.read_project = False
            self.load_subtitles = True

        if self.read_project:
            # Try to load the project file
            subtitles = self.ReadProjectFile()

            if subtitles and subtitles.scenes:
                self.load_subtitles = False
                write_backup = self.options.get('write_backup', False)
                if write_backup:
                    logging.info("Project file loaded, saving backup copy")
                    self.WriteBackupFile()
                else:
                    logging.info("Project file loaded")
            else:
                logging.warning(f"Unable to read project file, starting afresh")
                self.load_subtitles = True

        if self.load_subtitles:
            # (re)load the source subtitle file if required
            subtitles = self.LoadSubtitleFile(filepath)

        if outputpath:
            subtitles.outputpath = outputpath

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
            translator.events.scene_translated += self._on_scene_translated

            translator.TranslateSubtitles()

            self.SaveSubtitles()

        except TranslationAbortedError:
            logging.warning(f"Translation aborted")
            raise

        except Exception as e:
            if self.subtitles and self.options.get('stop_on_error'):
                self.SaveSubtitles()

            logging.error(f"Failed to translate subtitles")
            raise

    def SaveSubtitles(self, outputpath : str = None):
        """
        Write output file
        """
        include_original = self.options.get('include_original', False)
        self.subtitles.SaveTranslation(outputpath, include_original=include_original)

    def TranslateScene(self, scene_number, batch_numbers = None, translator : SubtitleTranslator = None):
        """
        Pass batches of subtitles to the translation engine.
        """
        if not self.subtitles:
            raise Exception("No subtitles to translate")

        try:
            if not translator:
                translator = SubtitleTranslator(self.subtitles, self.options)

            translator.events.preprocessed += self._on_preprocessed
            translator.events.batch_translated += self._on_batch_translated

            scene = self.subtitles.GetScene(scene_number)

            translator.TranslateScene(scene, batch_numbers=batch_numbers)

            self.SaveSubtitles()

            return scene
        
        except TranslationAbortedError:
            raise

        except Exception as e:
            if self.subtitles and self.options.get('stop_on_error'):
                self.SaveSubtitles()

            logging.error(f"Failed to translate subtitles")
            raise

    def AnyTranslated(self):
        """
        Have any subtitles been translated yet?
        """
        return True if self.subtitles and self.subtitles.translated else False

    def GetProjectFilepath(self, filepath):
        path, ext = os.path.splitext(filepath)
        filepath = filepath if ext == '.subtrans' else f"{path}.subtrans"
        return os.path.normpath(filepath)
    
    def GetBackupFilepath(self, filepath):
        projectfile = self.GetProjectFilepath(filepath)
        return f"{projectfile}-backup"
    
    def LoadSubtitleFile(self, filepath):
        """
        Load subtitles from an SRT file
        """
        with self.lock:
            self.subtitles = SubtitleFile(filepath)
            self.subtitles.LoadSubtitles()
            self.subtitles.project = self

            self.options.InitialiseInstructions()
            self.subtitles.UpdateContext(self.options)

        return self.subtitles

    def WriteProjectFile(self, projectfile = None):
        """
        Write a set of subtitles to a project file
        """
        with self.lock:
            if not self.subtitles:
                raise Exception("Can't write project file, no subtitles")

            if not isinstance(self.subtitles, SubtitleFile):
                raise Exception("Can't write project file, wrong content type")

            if not self.subtitles.scenes:
                raise Exception("Can't write project file, no scenes")

            if projectfile and not self.write_project:
                self.write_project = True
                self.read_project = True
                self.options.add('project', 'true')

            if not projectfile:
                projectfile = self.projectfile

            elif projectfile and not self.projectfile:
                self.projectfile = self.GetProjectFilepath(projectfile)
                self.subtitles.outputpath = GetOutputPath(projectfile)

            if not projectfile:
                raise Exception("No file path provided")
            
            projectfile = os.path.normpath(projectfile)

            logging.info(f"Writing project data to {str(projectfile)}")

            with open(projectfile, 'w', encoding=default_encoding) as f:
                project_json = json.dumps(self.subtitles, cls=SubtitleEncoder, ensure_ascii=False, indent=4)
                f.write(project_json)

    def WriteBackupFile(self):
        """
        Save a backup copy of the project
        """
        if self.subtitles and self.projectfile:
            backupfile = self.GetBackupFilepath(self.projectfile)
            self.WriteProjectFile(backupfile)

    def ReadProjectFile(self):
        """
        Load scenes, subtitles and context from a project file
        """
        try:
            with self.lock:
                logging.info(f"Reading project data from {str(self.projectfile)}")

                with open(self.projectfile, 'r', encoding=default_encoding, newline='') as f:
                    subtitles: SubtitleFile = json.load(f, cls=SubtitleDecoder)

                subtitles.Sanitise()
                subtitles.project = self
                self.subtitles = subtitles
                self.options.update(subtitles.context)
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

        if self.subtitles.scenes:
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
        self.SaveSubtitles()
        self.needsupdate = self.update_project
        self.events.scene_translated(scene)
