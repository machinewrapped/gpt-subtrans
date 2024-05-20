import regex
import logging

def ParseNames(name_list : str | list[str]) -> list[str]:
    """
    Parse a list of names from a string or list of strings
    """
    if isinstance(name_list, str):
        name_list = regex.split(r"[\n,]\s*", name_list)

    if isinstance(name_list, list):
        # Split each string in the list by comma or newline
        return [name.strip() for name in name_list for name in regex.split(r"[\n,]\s*", name) if name.strip()]

    return []

def ParseDelayFromHeader(value : str) -> float:
    """
    Try to figure out how long a suggested retry-after is
    """
    if not isinstance(value, str):
        return 12.3

    match = regex.match(r"([0-9\.]+)(\w+)?", value)
    if not match:
        return 32.1

    try:
        delay, unit = match.groups()
        delay = float(delay)
        unit = unit.lower() if unit else 's'
        if unit == 's':
            pass
        elif unit == 'm':
            delay *= 60
        elif unit == 'ms':
            delay /= 1000
        else:
            logging.error(f"Unexpected time unit '{unit}'")
            return 6.66

        return max(1, delay)  # ensure at least 1 second

    except Exception as e:
        logging.error(f"Unexpected time value '{value}'")
        return 6.66

