from datetime import timedelta
from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.SubtitleLine import SubtitleLine

class SubtitleBatcher:
    def __init__(self, settings):
        self.min_batch_size = settings.get('min_batch_size', 0)
        self.max_batch_size = settings.get('max_batch_size', 99)

        scene_threshold_seconds = settings.get('scene_threshold', 30.0)
        self.scene_threshold = timedelta(seconds=scene_threshold_seconds)

    def BatchSubtitles(self, lines : list[SubtitleLine]):
        if self.min_batch_size > self.max_batch_size:
            raise ValueError("min_batch_size must be less than max_batch_size.")

        scenes = []
        current_lines = []
        last_endtime = None

        for line in lines:
            # Fix overlapping display times
            if last_endtime and line.start < last_endtime:
                line.start = last_endtime + timedelta(milliseconds=10)

            gap = line.start - last_endtime if last_endtime is not None else None

            if gap is not None and gap > self.scene_threshold:
                if current_lines:
                    self.CreateNewScene(scenes, current_lines)
                    current_lines = []

            current_lines.append(line)
            last_endtime = line.end

        # Handle any remaining lines
        if current_lines:
            self.CreateNewScene(scenes, current_lines)

        return scenes

    def CreateNewScene(self, scenes : list[SubtitleScene], current_lines : list[SubtitleLine]):
        """
        Create a scene and lines to it in batches
        """
        scene = SubtitleScene()
        scenes.append(scene)
        scene.number = len(scenes)

        split_lines = self._split_lines(current_lines)

        for lines in split_lines:
            batch : SubtitleBatch = scene.AddNewBatch()
            batch.originals = lines

        return scene

    def _split_lines(self, lines : list[SubtitleLine]):
        """
        Recursively divide the lines at the largest gap until there is no batch larger than the maximum batch size
        """
        # If the batch is small enough, we're done
        if len(lines) <= self.max_batch_size:
            return [ lines ]

        # Find the longest gap starting from the min_batch_size index
        longest_gap = timedelta(seconds=0)
        split_index = self.min_batch_size
        last_split_index = len(lines) - self.min_batch_size

        if last_split_index > split_index:
            for i in range(split_index, last_split_index):
                gap = lines[i].start - lines[i - 1].end
                if gap > longest_gap:
                    longest_gap = gap
                    split_index = i

        # Split the batch into two
        left = lines[:split_index]
        right = lines[split_index:]

        # Recursively split the batches and concatenate the lists
        return self._split_lines(left) + self._split_lines(right)

