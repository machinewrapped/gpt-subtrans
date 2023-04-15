from pysrt import SubRipTime
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleLine import SubtitleLine

class SubtitleBatcher:
    def __init__(self, options):
        self.options = options

    def BatchSubtitles(self, lines : list[SubtitleLine]):
        options = self.options
        max_batch_size = options.get('max_batch_size')
        min_batch_size = options.get('min_batch_size')

        scene_threshold_us = options.get('scene_threshold', 30.0) * SubRipTime.SECONDS_RATIO
        scene_threshold = SubRipTime.from_ordinal(scene_threshold_us)

        batch_threshold_us = options.get('batch_threshold', 2.0) * SubRipTime.SECONDS_RATIO
        batch_threshold = SubRipTime.from_ordinal(batch_threshold_us)

        scenes = []
        last_endtime = None

        for line in lines:
            gap = line.start - last_endtime if last_endtime else None 

            if gap is None or gap > scene_threshold:
                scene = SubtitleScene()
                scenes.append(scene)
                scene.number = len(scenes)
                batch = None

            if batch is None or (batch.size >= max_batch_size) or (batch.size >= min_batch_size and gap > batch_threshold):
                batch = scene.AddNewBatch()
                batch.AddContext('summary', "New Scene")

            batch.AddLine(line)

            last_endtime = line.end

        return scenes



