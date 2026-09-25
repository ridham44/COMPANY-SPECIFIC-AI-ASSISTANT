from dataclasses import dataclass


@dataclass
class ParsedBlock:
    text: str
    source_name: str
    page: int | None = None
    heading: str | None = None
