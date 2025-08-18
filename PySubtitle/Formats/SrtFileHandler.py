import srt # type: ignore
from typing import Iterator, TextIO

from PySubtitle.SubtitleFileHandler import SubtitleFileHandler
from PySubtitle.SubtitleLine import SubtitleLine
from PySubtitle.SubtitleError import SubtitleParseError
from PySubtitle.Helpers.Localization import _

class SrtFileHandler(SubtitleFileHandler):
    """
    File handler for SRT subtitle format.
    Encapsulates all SRT library usage for file I/O operations.
    """
    
    def parse_file(self, file_obj: TextIO) -> Iterator[SubtitleLine]:
        """
        Parse SRT file content and yield SubtitleLine objects.
        
        Args:
            file_obj: Open file object to read from
            
        Yields:
            SubtitleLine: Parsed subtitle lines
            
        Raises:
            SubtitleParseError: If file cannot be parsed
        """
        try:
            srt_items = list(srt.parse(file_obj))
            for srt_item in srt_items:
                line = SubtitleLine.Contruct(
                    number=srt_item.index, 
                    start=srt_item.start, 
                    end=srt_item.end, 
                    text=srt_item.content,
                    metadata={
                        "proprietary": getattr(srt_item, 'proprietary', '')
                    }
                )
                yield line
        except srt.SRTParseError as e:
            raise SubtitleParseError(_("Failed to parse SRT file: {}").format(str(e)), e)
        except Exception as e:
            raise SubtitleParseError(_("Unexpected error parsing SRT file: {}").format(str(e)), e)
    
    def parse_string(self, content: str) -> Iterator[SubtitleLine]:
        """
        Parse SRT string content and yield SubtitleLine objects.
        
        Args:
            content: String content to parse
            
        Yields:
            SubtitleLine: Parsed subtitle lines
            
        Raises:
            SubtitleParseError: If content cannot be parsed
        """
        try:
            srt_items = list(srt.parse(content))
            for srt_item in srt_items:
                line = SubtitleLine.Construct(
                    number=srt_item.index, 
                    start=srt_item.start, 
                    end=srt_item.end, 
                    text=srt_item.content,
                    metadata={
                        "proprietary": getattr(srt_item, 'proprietary', '')
                    }
                )
                yield line
        except srt.SRTParseError as e:
            raise SubtitleParseError(_("Failed to parse SRT string: {}").format(str(e)), e)
        except Exception as e:
            raise SubtitleParseError(_("Unexpected error parsing SRT string: {}").format(str(e)), e)
    
    def compose_lines(self, lines: list[SubtitleLine], reindex: bool = True) -> str:
        """
        Compose subtitle lines into SRT format string.
        
        Args:
            lines: List of SubtitleLine objects to compose
            reindex: Whether to renumber lines sequentially
            
        Returns:
            str: SRT formatted subtitle content
        """
        # Convert SubtitleLine objects to srt.Subtitle objects for composition
        srt_items = []
        for i, line in enumerate(lines):
            if line.text and line.start is not None and line.end is not None:
                # Create srt.Subtitle object
                index = i + 1 if reindex else line.number
                srt_item = srt.Subtitle(
                    index=index,
                    start=line.start,
                    end=line.end,
                    content=line.text,
                    proprietary=""
                )
                srt_items.append(srt_item)
        
        return srt.compose(srt_items, reindex=False)  # We handle reindexing above
    
    def get_file_extensions(self) -> list[str]:
        """
        Get file extensions supported by this handler.
        
        Returns:
            list[str]: List of file extensions
        """
        return ['.srt']