import logging
from GUI.ProjectViewModel import ProjectViewModel
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleFile import SubtitleFile
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.Subtitle import Subtitle

class ProjectDataModel:
    _action_handlers = {}

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

    @classmethod
    def RegisterActionHandler(cls, action_name : str, handler : callable):
        handlers = cls._action_handlers.get(action_name) or []
        handlers.append(handler)
        cls._action_handlers[action_name] = handlers

    def PerformModelAction(self, action_name : str, params):
        handlers = self._action_handlers.get(action_name)
        if handlers:
            for handler in handlers:
                handler(self, *params)
        else:
            raise ValueError(f"No handler defined for action {action_name}")

    def CreateViewModel(self):
        viewmodel = ProjectViewModel()
        viewmodel.CreateFromModel(self.model)
        self.viewmodel = viewmodel
        return viewmodel

    def CreateModel(self, data):
        #TODO This layer of the model is probably redundant, mapping directly from PySubtitleGPT to the view model might make more sense
        if isinstance(data, SubtitleFile):
            model = {
                'scenes': []
            }
            for scene in data.scenes:
                model['scenes'].append(self.CreateModel(scene))

            self.model = model

        elif isinstance(data, SubtitleScene):
            model = {
                'scene': data.number,
                'start': None,
                'end': None,
                'duration': None,
                'subtitle_count': None,
                'batch_count': None,
                'batches': []
            }
            
            for batch in data.batches:
                model['batches'].append(self.CreateModel(batch))

            if model['batches']:
                batches = model['batches']
                model['batch_count'] = len(batches)
                model['subtitle_count'] = sum(batch['subtitle_count'] for batch in batches)
                model['start'] = batches[0]['start']
                model['end'] = batches[-1]['end']

        elif isinstance(data, SubtitleBatch):
            model = {
                'batch': data.number,
                'start': None,
                'end': None,
                'subtitles': [],
                'translated': [],
                'context': None,
            }

            for subtitle in data.subtitles:
                model['subtitles'].append(self.CreateModel(subtitle))

            if data.translated:
                for subtitle in data.translated:
                    model['translated'].append(self.CreateModel(subtitle))

            if model['subtitles']:
                subtitles = model['subtitles']
                model['subtitle_count'] = len(subtitles)
                model['start'] = subtitles[0]['start']
                model['end'] = subtitles[-1]['end']

            model['context'] = data.context
            model['summary'] = data.summary

        elif isinstance(data, Subtitle):
            model = {
                'index': data.index,
                'start': str(data.start),
                'end': str(data.end),
                'text': str(data.text),
                'translated.index': data.translated.index if data.translated else None
            }

        else:
            raise ValueError(f"Unable to create DataModel for {type(data).__name__}")
        
        return model
