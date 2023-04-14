import logging
from GUI.ProjectViewModel import ProjectViewModel
from PySubtitleGPT.Helpers import UpdateFields
from PySubtitleGPT.Options import Options
from PySubtitleGPT.SubtitleProject import SubtitleProject

class ProjectDataModel:
    _action_handlers = {}

    def __init__(self, project = None):
        self.project : SubtitleProject = project
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
        self.viewmodel = ProjectViewModel()
        self.viewmodel.CreateModel(self.project.subtitles)
        return self.viewmodel

    def UpdateModel(self, update):
        """
        Incrementally update the model and viewmodel
        """

        if not self.model or not self.model['scenes']:
            raise Exception("Unable to update model - no model")

        for scene_update in update['scenes']:
            scene = self.model['scenes'].get(scene_update['scene'])

            if not scene:
                # TODO: add a new scene? Support scene removal? Probably not with this method.
                logging.error(f"Model update for unknown scene {scene_update['scene']}")
                continue

            UpdateFields(scene, scene_update, ['summary', 'context', 'start', 'end'])

            scene_batches = scene['batches']
            for batch_update in scene_update['batches']:
                batch = scene_batches.get(batch_update['batch'])
                if not batch:
                    logging.error(f"Model update for unknown batch {batch_update['batch']}")
                    continue

                UpdateFields(batch, batch_update, ['summary', 'context', 'start', 'end'])

                dict = { line['index']: line for line in batch['translated'] }
                dict.update({ line['index']: line for line in batch_update['translated'] })
                batch['translated'] = list(dict.values())

                if self.viewmodel:
                    self.viewmodel.UpdateBatch(batch)
