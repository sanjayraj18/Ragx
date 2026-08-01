"""Parsing: the port, the canonical shape, and the content-type registry.

The registry is the single source of truth for what the system can
ingest — the upload allowlist derives from it, so accepting a format
and parsing it can never drift apart."""

from ragx.parsing.base import BlockType, ParsedBlock, ParsedDocument, Parser
from ragx.parsing.markdown import MarkdownParser
from ragx.parsing.pdf import PdfParser
from ragx.parsing.plain_text import PlainTextParser

__all__ = ["PARSERS", "BlockType", "ParsedBlock", "ParsedDocument", "Parser", "parser_for"]

PARSERS: dict[str, Parser] = {
    "text/plain": PlainTextParser(),
    "text/markdown": MarkdownParser(),
    "application/pdf" : PdfParser()
}


def parser_for(content_type: str) -> Parser:
    try:
        return PARSERS[content_type]
    except KeyError:
        raise ValueError(f"no parser registered for '{content_type}'") from None
