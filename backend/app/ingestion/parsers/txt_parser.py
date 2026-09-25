from pathlib import Path

from app.ingestion.base import ParsedBlock


def parse(file_path: Path) -> list[ParsedBlock]:
    text = file_path.read_text(encoding="utf-8", errors="replace")
    return [ParsedBlock(text=text, source_name=file_path.name, page=1)]
