from pathlib import Path

import fitz

from app.ingestion.base import ParsedBlock


def parse(file_path: Path) -> list[ParsedBlock]:
    blocks: list[ParsedBlock] = []
    with fitz.open(str(file_path)) as doc:
        for page_number, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():
                blocks.append(ParsedBlock(text=text, source_name=file_path.name, page=page_number))
    return blocks
