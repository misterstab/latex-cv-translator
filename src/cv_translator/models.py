from dataclasses import dataclass


@dataclass
class Segment:
    """Represents a translatable slice of text within a LaTeX document."""

    start: int
    end: int
    text: str
