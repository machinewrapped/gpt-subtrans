"""
Type-safe settings retrieval and coercion functions.

This module provides helper functions to safely retrieve and coerce settings
from dictionaries to specific types, with proper error handling for type
incompatibilities.
"""

from typing import Any, TypeVar, Union, overload
from datetime import timedelta

from PySubtitle.Options import SettingsType, Options

T = TypeVar('T')


class SettingsError(Exception):
    """Raised when a setting cannot be coerced to the expected type."""
    pass


@overload
def get_bool_setting(settings: SettingsType | Options, key: str) -> bool: ...

@overload
def get_bool_setting(settings: SettingsType | Options, key: str, default: bool) -> bool: ...

def get_bool_setting(settings: SettingsType | Options, key: str, default: bool = False) -> bool:
    """
    Safely retrieve a boolean setting from a settings dictionary.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        default: Default value if key is not present
        
    Returns:
        Boolean value of the setting
        
    Raises:
        SettingsError: If the setting cannot be converted to bool
    """
    value = settings.get(key, default)
    
    if isinstance(value, bool):
        return value
    elif isinstance(value, (int, float)):
        return bool(value)
    elif isinstance(value, str):
        lower_val = value.lower()
        if lower_val == 'true':
            return True
        elif lower_val == 'false':
            return False
        else:
            raise SettingsError(f"Cannot convert setting '{key}' value '{value}' to bool")
    else:
        raise SettingsError(f"Cannot convert setting '{key}' of type {type(value).__name__} to bool")


@overload
def get_int_setting(settings: SettingsType | Options, key: str) -> int: ...

@overload 
def get_int_setting(settings: SettingsType | Options, key: str, default: int) -> int: ...

def get_int_setting(settings: SettingsType | Options, key: str, default: int = 0) -> int:
    """
    Safely retrieve an integer setting from a settings dictionary.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        default: Default value if key is not present
        
    Returns:
        Integer value of the setting
        
    Raises:
        SettingsError: If the setting cannot be converted to int
    """
    value = settings.get(key, default)
    
    if isinstance(value, int):
        return value
    elif isinstance(value, float):
        if value.is_integer():
            return int(value)
        else:
            raise SettingsError(f"Cannot convert setting '{key}' float value '{value}' to int (not a whole number)")
    elif isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                float_val = float(value)
                if float_val.is_integer():
                    return int(float_val)
                else:
                    raise SettingsError(f"Cannot convert setting '{key}' string value '{value}' to int (not a whole number)")
            except ValueError:
                raise SettingsError(f"Cannot convert setting '{key}' string value '{value}' to int")
    elif isinstance(value, bool):
        return int(value)
    else:
        raise SettingsError(f"Cannot convert setting '{key}' of type {type(value).__name__} to int")


@overload
def get_float_setting(settings: SettingsType | Options, key: str) -> float: ...

@overload
def get_float_setting(settings: SettingsType | Options, key: str, default: float) -> float: ...

def get_float_setting(settings: SettingsType | Options, key: str, default: float = 0.0) -> float:
    """
    Safely retrieve a float setting from a settings dictionary.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        default: Default value if key is not present
        
    Returns:
        Float value of the setting
        
    Raises:
        SettingsError: If the setting cannot be converted to float
    """
    value = settings.get(key, default)
    
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise SettingsError(f"Cannot convert setting '{key}' string value '{value}' to float")
    elif isinstance(value, bool):
        return float(value)
    else:
        raise SettingsError(f"Cannot convert setting '{key}' of type {type(value).__name__} to float")


@overload
def get_str_setting(settings: SettingsType | Options, key: str) -> str: ...

@overload
def get_str_setting(settings: SettingsType | Options, key: str, default: str) -> str: ...

def get_str_setting(settings: SettingsType | Options, key: str, default: str = "") -> str:
    """
    Safely retrieve a string setting from a settings dictionary.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        default: Default value if key is not present
        
    Returns:
        String value of the setting
        
    Raises:
        SettingsError: If the setting cannot be converted to str
    """
    value = settings.get(key, default)
    
    if isinstance(value, str):
        return value
    elif isinstance(value, (int, float, bool)):
        return str(value)
    elif value is None:
        return default
    else:
        # Try to convert other types to string
        try:
            return str(value)
        except Exception:
            raise SettingsError(f"Cannot convert setting '{key}' of type {type(value).__name__} to str")


@overload
def get_list_setting(settings: SettingsType | Options, key: str) -> list[Any]: ...

@overload
def get_list_setting(settings: SettingsType | Options, key: str, default: list[Any]) -> list[Any]: ...

def get_list_setting(settings: SettingsType | Options, key: str, default: list[Any] | None = None) -> list[Any]:
    """
    Safely retrieve a list setting from a settings dictionary.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        default: Default value if key is not present
        
    Returns:
        List value of the setting
        
    Raises:
        SettingsError: If the setting cannot be converted to list
    """
    if default is None:
        default = []
        
    value = settings.get(key, default)
    
    if isinstance(value, list):
        return value
    elif isinstance(value, (tuple, set)):
        return list(value)
    elif isinstance(value, str):
        # Try to split string by common separators
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        elif ';' in value:
            return [item.strip() for item in value.split(';')]
        else:
            return [value] if value else []
    elif value is None:
        return default
    else:
        # Try to wrap single values in a list
        return [value]


def get_timedelta_setting(settings: SettingsType | Options, key: str, default: float = 0.0) -> timedelta:
    """
    Safely retrieve a timedelta setting from a settings dictionary.
    The setting value is expected to be in seconds as a float.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        default: Default value in seconds if key is not present
        
    Returns:
        timedelta object
        
    Raises:
        SettingsError: If the setting cannot be converted to timedelta
    """
    try:
        seconds = get_float_setting(settings, key, default)
        return timedelta(seconds=seconds)
    except SettingsError as e:
        raise SettingsError(f"Cannot convert setting '{key}' to timedelta: {e}")


def get_optional_setting(settings: SettingsType | Options, key: str, setting_type: type[T]) -> T | None:
    """
    Safely retrieve an optional setting that may not be present.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        setting_type: The expected type of the setting
        
    Returns:
        The setting value of the specified type, or None if not present
        
    Raises:
        SettingsError: If the setting is present but cannot be converted to the expected type
    """
    if isinstance(settings, Options):
        settings = settings.options

    if key not in settings:
        return None
        
    value = settings[key]
    if value is None:
        return None
        
    # Map types to appropriate getter functions
    if setting_type == bool:
        return get_bool_setting(settings, key)  # type: ignore
    elif setting_type == int:
        return get_int_setting(settings, key)  # type: ignore
    elif setting_type == float:
        return get_float_setting(settings, key)  # type: ignore
    elif setting_type == str:
        return get_str_setting(settings, key)  # type: ignore
    elif setting_type == list:
        return get_list_setting(settings, key)  # type: ignore
    else:
        # For other types, try direct conversion
        if isinstance(value, setting_type):
            return value
        else:
            raise SettingsError(f"Cannot convert setting '{key}' of type {type(value).__name__} to {setting_type.__name__}")


def validate_setting_type(settings: SettingsType | Options, key: str, expected_type: type[T], required: bool = False) -> bool:
    """
    Validate that a setting can be converted to the expected type without actually converting it.
    
    Args:
        settings: The settings dictionary
        key: The setting key
        expected_type: The expected type
        required: Whether the setting is required to be present
        
    Returns:
        True if the setting is valid or not present (when not required)
        
    Raises:
        SettingsError: If validation fails
    """
    if isinstance(settings, Options):
        settings = settings.options

    if key not in settings:
        if required:
            raise SettingsError(f"Required setting '{key}' is missing")
        return True
    
    try:
        get_optional_setting(settings, key, expected_type)
        return True
    except SettingsError:
        return False