from GUI.ProjectViewModel import ProjectViewModel
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.Subtitle import Subtitle

class ProjectDataModel:
    def __init__(self):
        self.project = None
        self.options = Options({
            'project': 'resume'            
        })

        self.model = {}
        self.viewmodel = None

    def CreateViewModel(self):
        viewmodel = ProjectViewModel()
        viewmodel.createFromDataModel(self.model)
        self.viewmodel = viewmodel
        return viewmodel

    def CreateDataModel(self, data, index = None):
        if isinstance(data, SubtitleFile):
            model = {
                'scenes': []
            }
            for index, scene in enumerate(data.scenes):
                model['scenes'].append(self.CreateDataModel(scene, index + 1))

            self.model = model

        elif isinstance(data, SubtitleScene):
            model = {
                'scene': index,
                'start': None,
                'end': None,
                'duration': None,
                'subtitle_count': None,
                'batch_count': None,
                'batches': []
            }
            
            for index, batch in enumerate(data.batches):
                model['batches'].append(self.CreateDataModel(batch, index + 1))

            if model['batches']:
                batches = model['batches']
                model['batch_count'] = len(batches)
                model['subtitle_count'] = sum(batch['subtitle_count'] for batch in batches)
                model['start'] = batches[0]['start']
                model['end'] = batches[-1]['end']

        elif isinstance(data, SubtitleBatch):
            model = {
                'batch': index,
                'start': None,
                'end': None,
                'subtitles': [],
                'translated': []
            }

            for index, subtitle in enumerate(data.subtitles):
                model['subtitles'].append(self.CreateDataModel(subtitle, index + 1))

            for index, subtitle in enumerate(data.translated):
                model['translated'].append(self.CreateDataModel(subtitle, index + 1))

            if model['subtitles']:
                subtitles = model['subtitles']
                model['subtitle_count'] = len(subtitles)
                model['start'] = subtitles[0]['start']
                model['end'] = subtitles[-1]['end']

        elif isinstance(data, Subtitle):
            model = {
                'index': index,
                'start': str(data.start),
                'end': str(data.end),
                'text': str(data.text)
            }

        else:
            raise ValueError(f"Unable to create DataModel for {type(data).__name__}")
        
        return model
