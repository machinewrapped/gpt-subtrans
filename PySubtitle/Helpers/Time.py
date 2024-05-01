import srt
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

def GetTimeDelta(time : datetime.timedelta | str | None, raise_exception = False) -> datetime.timedelta:
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

def TimeDeltaToText(time: datetime.timedelta) -> str:
    """
    Convert a timedelta to a string
    """
    return srt.timedelta_to_srt_timestamp(time).replace('00:', '') if time is not None else None

