import logging
from GUI.ProjectViewModel import ProjectViewModel
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.Subtitle import Subtitle

class ProjectDataModel:
    def __init__(self, project = None):
        self.project = project
        self.model = {}
        self.viewmodel : ProjectViewModel = None
        self.options = Options({
            'project': 'resume'
        })

        if project and project.options:
            if isinstance(project.options, Options):
                self.options = project.options
            else:
              self.options.update(project.options)

    def CreateViewModel(self):
        viewmodel = ProjectViewModel()
        viewmodel.CreateFromDataModel(self.model)
        self.viewmodel = viewmodel
        return viewmodel

    def CreateDataModel(self, data, number = None):
        if isinstance(data, SubtitleFile):
            model = {
                'scenes': []
            }
            for number, scene in enumerate(data.scenes):
                model['scenes'].append(self.CreateDataModel(scene, number + 1))

            self.model = model

        elif isinstance(data, SubtitleScene):
            model = {
                'scene': number,
                'start': None,
                'end': None,
                'duration': None,
                'subtitle_count': None,
                'batch_count': None,
                'batches': []
            }
            
            for number, batch in enumerate(data.batches):
                model['batches'].append(self.CreateDataModel(batch, number + 1))

            if model['batches']:
                batches = model['batches']
                model['batch_count'] = len(batches)
                model['subtitle_count'] = sum(batch['subtitle_count'] for batch in batches)
                model['start'] = batches[0]['start']
                model['end'] = batches[-1]['end']

        elif isinstance(data, SubtitleBatch):
            model = {
                'batch': number,
                'start': None,
                'end': None,
                'subtitles': [],
                'translated': [],
                'context': None,
            }

            for subtitle in data.subtitles:
                model['subtitles'].append(self.CreateDataModel(subtitle, subtitle.index))

            for subtitle in data.translated:
                model['translated'].append(self.CreateDataModel(subtitle, subtitle.index))

            if model['subtitles']:
                subtitles = model['subtitles']
                model['subtitle_count'] = len(subtitles)
                model['start'] = subtitles[0]['start']
                model['end'] = subtitles[-1]['end']

            model['context'] = data.context
            model['summary'] = data.summary

        elif isinstance(data, Subtitle):
            model = {
                'index': number,
                'start': str(data.start),
                'end': str(data.end),
                'text': str(data.text),
                'translated.index': data.translated.index if data.translated else None
            }

        else:
            raise ValueError(f"Unable to create DataModel for {type(data).__name__}")
        
        return model
