from pathlib import Path

from app.ingestion.base import ParsedBlock
from app.ingestion.parsers import docx_parser, pdf_parser, txt_parser

_PARSERS = {
    ".pdf": pdf_parser.parse,
    ".docx": docx_parser.parse,
    ".txt": txt_parser.parse,
}

SUPPORTED_EXTENSIONS = tuple(_PARSERS.keys())


class UnsupportedFileType(ValueError):
    pass


def parse_file(file_path: Path) -> list[ParsedBlock]:
    parser = _PARSERS.get(file_path.suffix.lower())
    if parser is None:
        raise UnsupportedFileType(f"Unsupported file type: {file_path.suffix}")
    return parser(file_path)
