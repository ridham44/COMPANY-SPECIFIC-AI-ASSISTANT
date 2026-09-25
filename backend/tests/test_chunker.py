from app.ingestion.base import ParsedBlock
from app.ingestion.chunker import chunk_blocks


def test_chunk_blocks_splits_long_text_with_overlap() -> None:
    words = [f"word{i}" for i in range(25)]
    block = ParsedBlock(text=" ".join(words), source_name="doc.txt", page=1)

    chunks = chunk_blocks([block], chunk_size=10, chunk_overlap=3)

    assert len(chunks) == 4
    assert chunks[0].text.split() == words[0:10]
    assert chunks[1].text.split() == words[7:17]
    assert chunks[2].text.split() == words[14:24]
    assert chunks[3].text.split() == words[21:25]
    assert [c.chunk_index for c in chunks] == [0, 1, 2, 3]


def test_chunk_blocks_keeps_short_block_as_single_chunk() -> None:
    block = ParsedBlock(text="just a few words here", source_name="doc.txt", page=1)
    chunks = chunk_blocks([block], chunk_size=500, chunk_overlap=75)
    assert len(chunks) == 1
    assert chunks[0].text == "just a few words here"


def test_chunk_blocks_carries_metadata_through() -> None:
    block = ParsedBlock(text="hello world", source_name="policy.docx", page=None, heading="Leave Policy")
    chunks = chunk_blocks([block], chunk_size=500, chunk_overlap=75)
    assert chunks[0].source_name == "policy.docx"
    assert chunks[0].heading == "Leave Policy"


def test_chunk_blocks_skips_empty_blocks() -> None:
    blocks = [ParsedBlock(text="   ", source_name="doc.txt"), ParsedBlock(text="real content", source_name="doc.txt")]
    chunks = chunk_blocks(blocks, chunk_size=500, chunk_overlap=75)
    assert len(chunks) == 1
    assert chunks[0].text == "real content"
