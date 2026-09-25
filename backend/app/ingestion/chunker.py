from dataclasses import dataclass

from app.ingestion.base import ParsedBlock


@dataclass
class Chunk:
    text: str
    source_name: str
    chunk_index: int
    page: int | None = None
    heading: str | None = None


def chunk_blocks(blocks: list[ParsedBlock], chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    chunks: list[Chunk] = []
    index = 0
    for block in blocks:
        words = block.text.split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            piece = " ".join(words[start:end])
            chunks.append(
                Chunk(
                    text=piece,
                    source_name=block.source_name,
                    chunk_index=index,
                    page=block.page,
                    heading=block.heading,
                )
            )
            index += 1
            if end == len(words):
                break
            start = end - chunk_overlap if end - chunk_overlap > start else end

    return chunks
