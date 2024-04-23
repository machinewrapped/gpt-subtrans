import datetime
import logging
import regex
import srt

def TimeDeltaToText(time: datetime.timedelta) -> str:
    """
    Convert a timedelta to a string
    """
    return srt.timedelta_to_srt_timestamp(time).replace('00:', '') if time is not None else None


def GetTimeDelta(time : datetime.timedelta | str | None) -> datetime.timedelta:
    """
    Ensure the input value is a timedelta, as best we can
    """
    if time is None:
        return None

    if isinstance(time, datetime.timedelta):
        return time

    try:
        return srt.srt_timestamp_to_timedelta(str(time))

    except Exception as e:
        time = str(time).strip()
        parts = regex.split('[:,]', time)

        if len(parts) == 3:
            if len(parts[-1]) == 3:
                logging.warning(f"Adding hour to time '{time}'")
                return GetTimeDelta(f"00:{parts[0]}:{parts[1]},{parts[2]}")
            else:
                logging.warning(f"Adding milliseconds to time '{time}'")
                return GetTimeDelta(f"{parts[0]}:{parts[1]}:{parts[2],000}")

        if len(parts) >= 4:
            if len(parts[-1]) == 3:
                logging.warning(f"Using last four parts of '{time}' as time")
                return GetTimeDelta(f"{parts[-4]}:{parts[-3]}:{parts[-2]},{parts[-1]}")

            logging.warning(f"Using first four parts of '{time}' as time")
            return GetTimeDelta(f"{parts[0]}:{parts[1]}:{parts[2]},{parts[3]}")

    raise ValueError(f"Unable to interpret time '{str(time)}'")

