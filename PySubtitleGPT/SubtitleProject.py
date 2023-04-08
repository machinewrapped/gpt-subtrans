import json
import os
import logging
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleFile import SubtitleFile

from PySubtitleGPT.SubtitleSerialisation import SubtitleDecoder, SubtitleEncoder

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')

class SubtitleProject:
    subtitles : SubtitleFile
    options : Options

    def __init__(self, options):
        self.options = options.GetNonProjectSpecificOptions() if options else Options()
        self.subtitles = None
        
        project_mode = options.get('project', '')
        if project_mode:
            project_mode = project_mode.lower() 

        self.read_project = project_mode in ["true", "read", "resume", "retranslate", "reparse"]
        self.write_project = project_mode in ["true", "write", "preview", "resume", "retranslate", "reparse"]
        self.update_project = self.write_project and not project_mode in ['reparse']
        self.load_subtitles = project_mode is None or project_mode in ["true", "write", "reload", "preview"]
        self.preview = project_mode in ["preview"]
        self.resume = project_mode in ["resume", "true"]
        self.reparse = project_mode in ["reparse"]
        self.retranslate = project_mode in ["retranslate"]
        self.stop_on_error = options.get('stop_on_error', False)
        self.write_backup_file = options.get('write_backup_file', False)

        options.add('write_project', self.write_project)
        options.add('write_backup_file', self.write_backup_file)
        options.add('preview', self.preview)
        options.add('resume', self.resume)

    def Initialise(self, filename, outfilename = None):
        """
        Initialize the project by either loading an existing project file or creating a new one.
        Load the subtitles to be translated, either from the project file or the source file.

        :param filename: the path to the source subtitle file (in .srt format) to be translated
        """ 
        self.projectfile = self.GetProjectFilename(filename or "subtitles")

        if self.read_project:
            # Try to load the project file
            subtitles = self.ReadProjectFile()

            if subtitles and subtitles.scenes:
                logging.info("Project file loaded, saving backup copy" if self.write_backup_file else "Project file loaded")
                if self.write_backup_file:
                    self.WriteBackupFile()
            else:
                logging.warning(f"Unable to read project file, starting afresh")
                self.load_subtitles = True

        if self.load_subtitles:
            # (re)load the source subtitle file if required
            subtitles = self.LoadSubtitleFile(filename)

        if outfilename:
            subtitles.filename = outfilename

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
        if ext == 'subtrans':
            return filename
        return os.path.join(os.getcwd(), f"{name}.subtrans")
    
    def LoadSubtitleFile(self, filename):
        """
        Load subtitles from an SRT file
        """
        self.subtitles = SubtitleFile()
        self.subtitles.LoadSubtitles(filename)
        self.subtitles.UpdateContext(self.options)
        return self.subtitles

    def WriteProjectFile(self, projectfile = None):
        """
        Write a set of subtitles to a project file
        """
        if not self.subtitles:
            raise ValueError("Can't write project file, no subtitles")

        if not isinstance(self.subtitles, SubtitleFile):
            raise ValueError("Asked to write a project file with the wrong content type")

        if not self.subtitles.scenes:
            raise ValueError("Asked to write a project file with no scenes")

        projectfile = projectfile or self.projectfile

        logging.debug(f"Writing project data to {str(projectfile)}")

        with open(projectfile, 'w', encoding=default_encoding) as f:
            project_json = json.dumps(self.subtitles, cls=SubtitleEncoder, ensure_ascii=False, indent=4)
            f.write(project_json)

        self.projectfile = projectfile

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
        logging.info(f"Reading project data from {str(self.projectfile)}")

        try:
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

    def UpdateProjectFile(self, scenes = None):
        """
        Write current state of scenes to the project file
        """
        scenes = scenes or self.subtitles.scenes

        if not scenes:
            return
        
        if self.update_project:
            if not self.subtitles:
                raise Exception("Unable to update project file, no subtitles")
            
            self.subtitles.scenes = scenes
            self.WriteProjectFile()

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

        # Update "self.options"
        self.options.update(options)

        if self.subtitles:
            self.subtitles.UpdateContext(self.options)

        self.UpdateProjectFile()
