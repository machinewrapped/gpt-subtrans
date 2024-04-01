class ModelUpdateSection:
    def __init__(self):
        self.updates = {}
        self.replacements = {}
        self.additions = {}
        self.removals = []

    def update(self, key, item_update):
        self.updates[key] = item_update

    def replace(self, key, item):
        self.replacements[key] = item

    def add(self, key, item):
        self.additions[key] = item

    def remove(self, key):
        self.removals.append(key)

    def HasUpdate(self) -> bool:
        return True if (self.updates or self.replacements or self.additions or self.removals) else False

    @property
    def size_changed(self) -> bool:
        return True if (self.removals or self.additions) else False