import re
import unicodedata
from dataclasses import replace

from app.ingestion.base import ParsedBlock


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("­", "")
    text = re.sub(r"-\n(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def strip_repeated_lines(blocks: list[ParsedBlock]) -> list[ParsedBlock]:
    """Drops lines (headers/footers) that show up on most pages of a multi-page doc."""
    pages = {b.page for b in blocks if b.page is not None}
    if len(pages) < 3:
        return blocks

    line_pages: dict[str, set[int]] = {}
    for block in blocks:
        if block.page is None:
            continue
        for line in block.text.split("\n"):
            stripped = line.strip()
            if stripped:
                line_pages.setdefault(stripped, set()).add(block.page)

    threshold = max(3, len(pages) // 2)
    repeated = {line for line, pgs in line_pages.items() if len(pgs) >= threshold}
    if not repeated:
        return blocks

    result = []
    for block in blocks:
        kept = [line for line in block.text.split("\n") if line.strip() not in repeated]
        result.append(replace(block, text="\n".join(kept)))
    return result
