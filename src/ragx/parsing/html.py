"""HTML: declared structure in tag soup. Chrome (nav, footers, scripts) is
removed before reading — indexed navigation menus poison every query."""

from bs4 import BeautifulSoup
from bs4.element import Tag

from ragx.parsing.base import BlockType, ParsedBlock, ParsedDocument

_NOISE = ["script", "style", "nav", "header", "footer", "aside", "noscript"]
_CONTENT = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "table"]


class HtmlParser:
    def parse(self, data: bytes) -> ParsedDocument:
        soup = BeautifulSoup(data, "html.parser")
        for noise in soup(_NOISE):
            noise.decompose()

        blocks: list[ParsedBlock] = []
        for tag in soup.find_all(_CONTENT):
            if not isinstance(tag, Tag):
                continue
            if tag.name != "table" and tag.find_parent("table"):
                continue  # cell contents are captured by their table
            if tag.name == "p" and tag.find_parent("li"):
                continue  # paragraph inside a list item — the li captures it

            if tag.name == "table":
                rows = [
                    " | ".join(
                        " ".join(cell.get_text(" ", strip=True).split())
                        for cell in tr.find_all(["td", "th"])
                    )
                    for tr in tag.find_all("tr")
                ]
                text = "\n".join(row for row in rows if row.strip(" |"))
                if text:
                    blocks.append(ParsedBlock(text=text, type=BlockType.TABLE))
                continue

            if tag.name == "pre":
                text = tag.get_text("\n", strip=True)
                if text:
                    blocks.append(ParsedBlock(text=text, type=BlockType.CODE))
                continue

            text = " ".join(tag.get_text(" ", strip=True).split())
            if not text:
                continue
            if tag.name.startswith("h"):
                blocks.append(
                    ParsedBlock(text=text, type=BlockType.HEADING, heading_level=int(tag.name[1]))
                )
            elif tag.name == "li":
                blocks.append(ParsedBlock(text=text, type=BlockType.LIST_ITEM))
            else:
                blocks.append(ParsedBlock(text=text))

        return ParsedDocument(blocks=blocks)
