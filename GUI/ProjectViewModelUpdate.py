class ModelUpdateSection:
    def __init__(self):
        self.updates = {}
        self.replacements = {}
        self.removals = []
        self.additions = {}

    def update(self, key, item_update):
        self.updates[key] = item_update

    def replace(self, key, item):
        self.replacements[key] = item

    def add(self, key, item):
        self.additions[key] = item

    def remove(self, key):
        self.removals.append(key)

    def HasUpdate(self) -> bool:
        return self.updates or self.replacements or self.additions or self.removals
    
    @property
    def size_changed(self) -> bool:
        return self.removals or self.additions

class ModelUpdate:
    def __init__(self):
        self.rebuild = False
        self.scenes = ModelUpdateSection()
        self.batches = ModelUpdateSection()
        self.lines = ModelUpdateSection()

    def HasUpdate(self) -> bool:
        return self.scenes.HasUpdate() or self.batches.HasUpdate() or self.lines.HasUpdate()

