import json
import os
import logging
from PySubtitleGPT.SubtitleFile import SubtitleFile

from PySubtitleGPT.SubtitleSerialisation import SubtitleDecoder, SubtitleEncoder

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')

class SubtitleProject:
    def __init__(self, options):
        self.options = options
        self.subtitles = None
        
        project_mode = options.get('project', '')
        if project_mode:
            project_mode = project_mode.lower() 

        self.read_project = project_mode in ["true", "read", "resume", "retranslate", "reparse"]
        self.write_project = project_mode in ["true", "write", "preview", "resume", "retranslate", "reparse"]
        self.update_project = self.write_project and not project_mode in ['reparse']
        self.load_subtitles = project_mode is None or project_mode in ["true", "write", "reload", "preview"]
        self.preview = project_mode in ["preview"]
        self.resume = project_mode in ["resume"]
        self.reparse = project_mode in ["reparse"]
        self.retranslate = project_mode in ["retranslate"]
        self.stop_on_error = options.get('stop_on_error', False)

        options.add('write_project', self.write_project)
        options.add('preview', self.preview)
        options.add('resume', self.resume)

    def Initialise(self, filename):
        """
        Initialize the project by either loading an existing project file or creating a new one.
        Load the subtitles to be translated, either from the project file or the source file.

        :param filename: the path to the source subtitle file (in .srt format) to be translated
        """ 
        self.projectfile = self.GetProjectFilename(filename or "subtitles")

        if self.read_project:
            # Try to load the project file
            subtitles = self.ReadProjectFile()

            if subtitles:
                logging.info(f"Project file loaded, saving backup copy")
                self.WriteBackupFile(subtitles)
            else:
                logging.warning(f"Unable to read project file, starting afresh")
                self.load_subtitles = True

        if self.load_subtitles:
            # (re)load the source subtitle file if required
            subtitles = self.LoadSubtitleFile(filename)

        if not subtitles.has_subtitles:
            raise ValueError(f"No subtitles to translate in {filename}")

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
            self.subtitles.Translate(self.options, self)

            self.subtitles.SaveTranslation()

        except Exception as e:
            if self.subtitles and self.stop_on_error:
                self.subtitles.SaveTranslation()

            logging.error(f"Failed to translate subtitles")
            raise

    def GetProjectFilename(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join(os.getcwd(), f"{name}.subtrans")
    
    def LoadSubtitleFile(self, filename):
        """
        Load subtitles from an SRT file
        """
        self.subtitles = SubtitleFile()
        self.subtitles.LoadSubtitles(filename)
        return self.subtitles

    def WriteProjectFile(self, filename = None):
        """
        Write a set of subtitles to a project file
        """
        if not self.subtitles:
            raise ValueError("Can't write project file, no subtitles")
        
        if not isinstance(self.subtitles, SubtitleFile):
            raise Exception("Asked to write a project file with the wrong content type")

        filename = filename or self.filename

        logging.debug(f"Writing project data to {str(filename)}")

        with open(filename, 'w', encoding=default_encoding) as f:
            project_json = json.dumps(self.subtitles, cls=SubtitleEncoder, ensure_ascii=False, indent=4)
            f.write(project_json)

    def WriteBackupFile(self, subtitles):
        """
        Save a backup copy of the project
        """
        if self.filename:
            self.WriteProjectFile(subtitles, f"{self.filename}-backup")

    def ReadProjectFile(self):
        """
        Load scenes, subtitles and context from a project file (really a project file)
        """
        logging.info(f"Reading project data from {str(self.filename)}")

        try:
            with open(self.filename, 'r', encoding=default_encoding) as f:
                subtitles = json.load(f, cls=SubtitleDecoder)

            subtitles.project = self
            self.subtitles = subtitles
            return subtitles

        except FileNotFoundError:
            logging.error(f"Project file {self.filename} not found")
            return None

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON file: {e}")
            return None

    def UpdateProjectFile(self, scenes):
        """
        Write current state of scenes to the project file
        """
        if self.update_project:
            if not self.subtitles:
                raise Exception("Unable to update project file, no subtitles")
            
            self.subtitles.scenes = scenes
            self.WriteProjectFile(self.subtitles)

