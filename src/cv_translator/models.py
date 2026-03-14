from dataclasses import dataclass


@dataclass
class Segment:
    start: int
    end: int
    text: str
