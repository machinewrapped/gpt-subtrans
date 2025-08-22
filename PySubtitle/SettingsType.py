from __future__ import annotations
from collections.abc import Mapping
from typing import Any, TypeAlias

BasicType: TypeAlias = str | int | float | bool | list[str] | None
SettingType: TypeAlias = BasicType | dict[str, 'SettingType'] | dict[str, 'SettingsType']
GuiSettingsType: TypeAlias = dict[str, tuple[type|str|list[str], str]]

class SettingsType(dict[str, SettingType]):
    """
    Settings dictionary with restricted range of types allowed and type-safe getters
    """
    def __init__(self, settings : Mapping[str,SettingType]|None = None):
        if not isinstance(settings, SettingsType):
            settings = dict(settings or {})
        super().__init__(settings)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean setting with type safety"""
        from .Helpers.Settings import GetBoolSetting
        return GetBoolSetting(self, key, default)

    def get_int(self, key: str, default: int = 0) -> int|None:
        """Get an integer setting with type safety"""
        from .Helpers.Settings import GetIntSetting
        return GetIntSetting(self, key, default)

    def get_float(self, key: str, default: float|None = None) -> float|None:
        """Get a float setting with type safety"""
        from .Helpers.Settings import GetFloatSetting
        return GetFloatSetting(self, key, default)

    def get_str(self, key: str, default: str|None = None) -> str|None:
        """Get a string setting with type safety"""
        from .Helpers.Settings import GetStrSetting
        return GetStrSetting(self, key, default)

    def get_list(self, key: str, default: list[Any]|None = None) -> list[Any]:
        """Get a list setting with type safety"""
        from .Helpers.Settings import GetListSetting
        return GetListSetting(self, key, default or [])

    def get_dict(self, key: str, default: dict[str, SettingType]|None = None) -> dict[str, SettingType]:
        """Get a dict setting with type safety"""
        from .Helpers.Settings import GetDictSetting
        return GetDictSetting(self, key, default)