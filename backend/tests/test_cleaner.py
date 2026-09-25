from app.ingestion.base import ParsedBlock
from app.ingestion.cleaner import clean_text, strip_repeated_lines


def test_clean_text_collapses_whitespace_and_dehyphenates() -> None:
    raw = "This is a sen-\ntence with   extra   spaces.\n\n\n\nAnd another line."
    cleaned = clean_text(raw)
    assert "sentence" in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned


def test_clean_text_normalizes_unicode() -> None:
    assert clean_text("café­") == "café"


def test_strip_repeated_lines_removes_header_footer_across_pages() -> None:
    blocks = [
        ParsedBlock(text="Company Confidential\nActual content for page 1\nPage 1", source_name="doc.pdf", page=1),
        ParsedBlock(text="Company Confidential\nActual content for page 2\nPage 2", source_name="doc.pdf", page=2),
        ParsedBlock(text="Company Confidential\nActual content for page 3\nPage 3", source_name="doc.pdf", page=3),
    ]
    result = strip_repeated_lines(blocks)
    for block in result:
        assert "Company Confidential" not in block.text
        assert "Actual content" in block.text


def test_strip_repeated_lines_leaves_short_docs_alone() -> None:
    blocks = [ParsedBlock(text="Header\nBody", source_name="doc.pdf", page=1)]
    assert strip_repeated_lines(blocks) == blocks
