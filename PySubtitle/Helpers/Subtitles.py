import logging
import srt

from PySubtitle.SubtitleLine import SubtitleLine

def MergeSubtitles(merged_lines : list[SubtitleLine]) -> SubtitleLine:
    """
    Merge multiple lines into a single line with the same start and end times.
    """
    first_line = merged_lines[0]
    last_line = merged_lines[-1]
    merged_number = first_line.number
    merged_start = first_line.start
    merged_end = last_line.end
    merged_content = "\n".join(line.text for line in merged_lines)
    subtitle = srt.Subtitle(merged_number, merged_start, merged_end, merged_content)
    return SubtitleLine(subtitle)

def MergeTranslations(lines : list[SubtitleLine], translated : list[SubtitleLine]) -> list[SubtitleLine]:
    """
    Replace lines with corresponding lines in translated
    """
    line_dict = {item.key: item for item in lines if item.key}

    for item in translated:
        line_dict[item.key] = item

    lines = sorted(line_dict.values(), key=lambda item: item.key)

    return lines

def ResyncTranslatedLines(original_lines : list[SubtitleLine], translated_lines : list[SubtitleLine]):
    """
    Copy number, start and end from original lines to matching translated lines.
    """
    num_original = len(original_lines)
    num_translated = len(translated_lines)
    min_lines = min(num_original, num_translated)

    for i in range(min_lines):
        translated_lines[i].start = original_lines[i].start
        translated_lines[i].end = original_lines[i].end
        translated_lines[i].number = original_lines[i].number

    if num_original < num_translated:
        logging.warning(f"Number of translated lines exceeds the number of original lines. "
                        f"Removed {num_translated - num_original} extra translated lines.")
        del translated_lines[num_original:]

    elif num_original > num_translated:
        logging.warning(f"Number of lines in original and translated subtitles don't match. Synced {min_lines} lines.")

