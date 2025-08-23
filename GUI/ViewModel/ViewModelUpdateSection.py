from __future__ import annotations
from typing import TypeAlias

from PySubtitle.SubtitleBatch import SubtitleBatch
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleScene import SubtitleScene
from PySubtitle.Translation import Translation
from PySubtitle.TranslationPrompt import TranslationPrompt

SceneKey = int
BatchKey = tuple[int, int]
LineKey = tuple[int, int, int]

Key : TypeAlias = SceneKey | BatchKey | LineKey
Value : TypeAlias = str | int | float | list[str] | dict[str, str|list|dict] | Translation | TranslationPrompt | None
UpdateValue : TypeAlias = dict[str, 'UpdateValue'] | dict[int, 'UpdateValue'] | Value
UpdateType : TypeAlias = dict[Key, UpdateValue]
ModelTypes : TypeAlias = SubtitleLine | SubtitleBatch | SubtitleScene

class ModelUpdateSection:
    def __init__(self):
        self.updates: UpdateType = {}
        self.replacements: dict[Key, ModelTypes] = {}
        self.additions: dict[Key, ModelTypes] = {}
        self.removals: list[Key] = []

    def update(self, key: Key, item_update: UpdateValue) -> None:
        self.updates[key] = item_update

    def replace(self, key: Key, item: ModelTypes) -> None:
        self.replacements[key] = item

    def add(self, key: Key, item: ModelTypes) -> None:
        self.additions[key] = item

    def remove(self, key: Key) -> None:
        self.removals.append(key)

    @property
    def has_updates(self) -> bool:
        return bool(self.updates or self.replacements or self.additions or self.removals)

    @property
    def size_changed(self) -> bool:
        return bool(self.removals or self.additions)