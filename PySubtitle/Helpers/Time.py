import datetime
import regex

delim = r"[,.:，．。：]"

timestamp_patterns = [
    # Handle standard SRT timestamps
    r"^(?P<hours>\d{1,3}):(?P<minutes>\d{1,2}):(?P<seconds>\d{2})(?:,(?P<milliseconds>\d{3}))?$",
    # Handle timestamps with non-standard delimiters but the same structure, with optional garbage at the end
    rf"^(?P<hours>\d{{1,3}}){delim}(?P<minutes>\d{{1,2}}){delim}(?P<seconds>\d{{1,2}})(?:{delim}(?P<milliseconds>\d{{3}}))?($|[^0-9])",
    # Handle timestamps with only minutes and seconds
    rf"^(?P<minutes>\d{{1,2}}){delim}(?P<seconds>\d{{1,2}})(?:{delim}(?P<milliseconds>\d{{3}}))?$",
    # Handle just seconds and optional milliseconds
    r"^(?P<seconds>\d{1,2})(?:,(?P<milliseconds>\d{3}))?$",
]

re_timestamps = [
    regex.compile(pattern) for pattern in timestamp_patterns
]

def GetTimeDelta(time : datetime.timedelta | str | None, raise_exception : bool = False) -> datetime.timedelta|Exception|None:
    """
    Ensure the input value is a timedelta, as best we can
    """
    if time is None:
        return None

    if isinstance(time, datetime.timedelta):
        return time

    timestamp = str(time).strip()

    for pattern in re_timestamps:
        time_match = pattern.match(timestamp)
        if time_match:
            hours = int(time_match.group("hours")) if "hours" in time_match.groupdict() else 0
            minutes = int(time_match.group("minutes")) if "minutes" in time_match.groupdict() else 0
            seconds = int(time_match.group("seconds") or 0)
            milliseconds = int(time_match.group("milliseconds") or 0)

            return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

    error = ValueError(f"Invalid time format: {time}")
    if raise_exception:
        raise error

    return error

def TimeDeltaToText(time: datetime.timedelta|None, include_milliseconds : bool = True) -> str:
    """
    Convert a timedelta to a minimal string representation, adhering to specific formatting rules:
    - Hours, minutes, and seconds may appear with leading zeros only as required.
    - Milliseconds are appended after a comma if they are present.
    - Seconds can be a single digit if no preceding hours or minutes are present.
    """
    if time is None:
        return ""

    total_seconds = int(time.total_seconds())
    milliseconds = time.microseconds // 1000

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        time_str = f"{hours}:{minutes:02d}:{seconds:02d}"
    elif minutes > 0:
        time_str = f"{minutes:02d}:{seconds:02d}"
    else:
        time_str = f"{seconds:02d}"

    if include_milliseconds:
        time_str += f",{milliseconds:03d}"

    return time_str.format(hours, minutes, seconds, milliseconds)

def TimedeltaToSrtTimestamp(time: datetime.timedelta|str|None) -> str|None:
    """
    Convert a timedelta to a string suitable for SRT timestamps.
    """
    if time is None:
        return None

    timedelta : datetime.timedelta|Exception|None = time if isinstance(time, datetime.timedelta) else GetTimeDelta(time, raise_exception=True)

    if not isinstance(timedelta, datetime.timedelta):
        raise ValueError(f"Invalid timedelta: {time}")

    total_seconds = int(timedelta.total_seconds())
    milliseconds = timedelta.microseconds // 1000

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def SrtTimestampToTimedelta(timestamp: str|None) -> datetime.timedelta|None:
    """
    Convert a string in SRT timestamp format to a timedelta.
    """
    if not timestamp:
        return None

    match = regex.match(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$", timestamp)
    if not match:
        raise ValueError(f"Invalid SRT timestamp format: {timestamp}")

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    milliseconds = int(match.group(4))

    return datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

