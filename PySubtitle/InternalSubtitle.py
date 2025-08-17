from datetime import timedelta
from typing import Any

class InternalSubtitle:
    """
    Format-agnostic internal representation of a subtitle item.
    Replaces srt.Subtitle for business logic while maintaining compatibility.
    """
    
    def __init__(self, index: int | None = None, start: timedelta | None = None, 
                 end: timedelta | None = None, content: str = "", proprietary: str = ""):
        self.index = index
        self.start = start or timedelta(seconds=0)
        self.end = end or timedelta(seconds=0)
        self.content = content
        self.proprietary = proprietary
    
    def __str__(self) -> str:
        return self.to_srt()
    
    def __repr__(self) -> str:
        return f"InternalSubtitle(index={self.index}, start={self.start}, end={self.end}, content={repr(self.content)})"
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, InternalSubtitle):
            return False
        return (self.index == other.index and 
                self.start == other.start and 
                self.end == other.end and 
                self.content == other.content and
                self.proprietary == other.proprietary)
    
    def to_srt(self, strict: bool = True) -> str:
        """
        Convert to SRT format string for output.
        This method maintains compatibility with srt.Subtitle.to_srt()
        """
        from PySubtitle.Helpers.Time import TimedeltaToSrtTimestamp
        
        if self.start is None or self.end is None:
            if strict:
                raise ValueError("Cannot convert subtitle with missing timestamps to SRT")
            return ""
        
        start_str = TimedeltaToSrtTimestamp(self.start) or "00:00:00,000"
        end_str = TimedeltaToSrtTimestamp(self.end) or "00:00:00,000"
        
        # Format: number\nstart --> end\ncontent\n\n
        parts = []
        if self.index is not None:
            parts.append(str(self.index))
        parts.append(f"{start_str} --> {end_str}")
        if self.content:
            parts.append(self.content)
        if self.proprietary:
            parts.append(self.proprietary)
        
        return "\n".join(parts)

    @classmethod
    def make_legal_content(cls, content: str) -> str:
        """
        Make content legal for subtitle format.
        Maintains compatibility with srt.make_legal_content()
        """
        if not content:
            return ""
        
        # Remove or replace problematic characters that could break subtitle parsing
        # Based on srt library's make_legal_content function
        content = content.strip()
        
        # Replace problematic sequences that could interfere with SRT parsing
        content = content.replace("-->", "→")  # Replace SRT timestamp separator
        
        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        
        return content

    def copy(self) -> 'InternalSubtitle':
        """Create a copy of this subtitle."""
        return InternalSubtitle(
            index=self.index,
            start=self.start,
            end=self.end,
            content=self.content,
            proprietary=self.proprietary
        )