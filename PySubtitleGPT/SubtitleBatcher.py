from datetime import timedelta
from PySubtitleGPT.SubtitleBatch import SubtitleBatch
from PySubtitleGPT.SubtitleScene import SubtitleScene
from PySubtitleGPT.SubtitleLine import SubtitleLine

class OldSubtitleBatcher:
    def __init__(self, options):
        self.options = options

    def BatchSubtitles(self, lines : list[SubtitleLine]):
        options = self.options
        max_batch_size = options.get('max_batch_size')
        min_batch_size = options.get('min_batch_size')

        scene_threshold_seconds = options.get('scene_threshold', 30.0)
        scene_threshold = timedelta(seconds=scene_threshold_seconds)

        batch_threshold_seconds = options.get('batch_threshold', 2.0)
        batch_threshold = timedelta(seconds=batch_threshold_seconds)

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

            batch.AddLine(line)

            last_endtime = line.end

        return scenes

class SubtitleBatcher:
    def __init__(self, options):
        self.options = options

        self.min_batch_size = self.options.get('min_batch_size', 0)
        self.max_batch_size = self.options.get('max_batch_size', 99)

    def BatchSubtitles(self, lines : list[SubtitleLine]):
        if self.min_batch_size >= self.max_batch_size:
            raise ValueError("min_batch_size must be less than max_batch_size.")

        scene_threshold_seconds = self.options.get('scene_threshold', 30.0)
        scene_threshold = timedelta(seconds=scene_threshold_seconds)

        scenes = []
        current_lines = []
        last_endtime = None

        for line in lines:
            # Fix overlapping display times
            if last_endtime and line.start < last_endtime:
                line.start = last_endtime + timedelta(milliseconds=10)

            gap = line.start - last_endtime if last_endtime else None

            if gap is not None and gap > scene_threshold:
                if current_lines:
                    scene = self._create_scene(current_lines)
                    
                    scenes.append(scene)
                    current_lines = []

            current_lines.append(line)
            last_endtime = line.end

        # Handle any remaining lines
        if current_lines:
            scene = self._create_scene(current_lines)
            scenes.append(scene)

        return scenes

    def _create_scene(self, current_lines : list[SubtitleLine]):
        """
        Create a scene and lines to it in batches
        """
        scene = SubtitleScene()
        split_lines = self._split_lines(current_lines)

        for lines in split_lines:
            batch = scene.AddNewBatch()
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

