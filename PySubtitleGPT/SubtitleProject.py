import json
import os
import logging
from PySubtitleGPT.SubtitleFile import SubtitleFile

from PySubtitleGPT.SubtitleSerialisation import SubtitleDecoder, SubtitleEncoder

default_encoding = os.getenv('DEFAULT_ENCODING', 'utf-8')

class SubtitleProject:
    def __init__(self, options, filename):
        self.filename = self.GetProjectFilename(filename or "subtitles")
        self.subtitles = None

        project_mode = options.get('project', '').lower()
        self.read_project = project_mode in ["true", "read", "resume", "retranslate", "reparse"]
        self.write_project = project_mode in ["true", "write", "preview", "resume", "retranslate", "reparse"]
        self.update_project = self.write_project and not project_mode in ['reparse']
        self.load_subtitles = project_mode in ["reload", "true", "write", "preview"]
        self.preview = project_mode in ["preview"]
        self.resume = project_mode in ["resume"]
        self.reparse = project_mode in ["reparse"]
        self.retranslate = project_mode in ["retranslate"]

        options.add('write_project', self.write_project)
        options.add('preview', self.preview)
        options.add('resume', self.resume)

    def GetProjectFilename(self, filename):
        name, ext = os.path.splitext(filename)
        return os.path.join(os.getcwd(), f"{name}.subtrans")

    def WriteProjectFile(self, subtitles, filename = None):
        """
        Write a set of subtitles to a project file (really a project file)
        """
        if not subtitles:
            raise ValueError("Can't write project file, no subtitles")
        
        if not isinstance(subtitles, SubtitleFile):
            raise Exception("Asked to write a project file with the wrong content type")

        self.subtitles = subtitles

        filename = filename or self.filename

        logging.info(f"Writing project data to {str(filename)}")

        with open(filename, 'w', encoding=default_encoding) as f:
            project_json = json.dumps(subtitles, cls=SubtitleEncoder, ensure_ascii=False, indent=4)
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

