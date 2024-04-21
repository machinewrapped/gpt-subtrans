import regex
from PySubtitle.Helpers.Text import LimitTextLength

def SanitiseSummary(summary : str, movie_name : str = None, max_summary_length : int = None):
    """
    Remove trivial parts of summary text
    """
    if not summary:
        return None

    summary = regex.sub(r'^(?:(?:Scene|Batch)[\s\d:\-]*)+', '', summary, flags=regex.IGNORECASE)
    summary = summary.replace("Summary of the batch", "")
    summary = summary.replace("Summary of the scene", "")

    if movie_name:
        # Remove movie name and any connectors (-,: or whitespace)
        summary = regex.sub(r'^' + regex.escape(movie_name) + r'\s*[:\-]\s*', '', summary)

    summary = summary.strip()

    if max_summary_length:
        summary = LimitTextLength(summary, max_summary_length)

    return summary or None

