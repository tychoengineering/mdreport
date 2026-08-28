from __future__ import annotations

import base64
import html
import mimetypes
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from .markdown_tokens import html_block_token
from .report_block import DEFERRED_BLOCK_TOKEN_TYPE
from .template_rendering import render_template

if TYPE_CHECKING:
    from .markdown_parser import MarkdownParser
    from .report import MarkdownReport

__all__ = ["Figure", "FigureEmbeddingError"]


class FigureEmbeddingError(ValueError):
    """A figure source cannot be embedded as an image in the report."""


def image_tokens(parser: MarkdownParser, source: str, alt_text: str) -> list[Token]:
    """Build a paragraph containing one image with literal alternative text."""
    escaped_alt_text = alt_text.replace("\\", "\\\\").replace("]", "\\]")
    image = Token(
        "image",
        "img",
        0,
        attrs={"src": source, "alt": ""},
        children=[Token("text", "", 0, content=escaped_alt_text)],
        content=escaped_alt_text,
    )
    inline = Token("inline", "", 0, children=[image], block=True)
    return [
        Token("paragraph_open", "p", 1, block=True),
        inline,
        Token("paragraph_close", "p", -1, block=True),
    ]


def caption_tokens(parser: MarkdownParser, number: int, caption: str) -> list[Token]:
    """Build an emphasized, numbered figure caption."""
    content = f"Figure {number}: {caption}" if caption else f"Figure {number}"
    inline = parser.parse_inline(content)
    inline.children = [
        Token("em_open", "em", 1, markup="*"),
        *(inline.children or []),
        Token("em_close", "em", -1, markup="*"),
    ]
    return [
        Token("paragraph_open", "p", 1, block=True),
        inline,
        Token("paragraph_close", "p", -1, block=True),
    ]


def embedded_figure_tokens(
    parser: MarkdownParser,
    source: str,
    alt_text: str,
) -> list[Token]:
    """Read a local image and return inline SVG or a base64 Markdown image.

    Raises:
        FigureEmbeddingError: if source is not a local image file or its media
            type cannot be determined.
    """
    if source.startswith("data:image/"):
        return image_tokens(parser, source, alt_text)

    source_path = Path(source)
    if not source_path.is_file():
        raise FigureEmbeddingError(f"Embedded figure source {source!r} must be an existing local file")

    media_type, encoding = mimetypes.guess_type(source_path.name)
    if encoding is not None or media_type is None or not media_type.startswith("image/"):
        raise FigureEmbeddingError(f"Embedded figure source {source!r} does not have a recognized image type")

    if media_type == "image/svg+xml":
        try:
            svg = source_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            raise FigureEmbeddingError(f"Embedded SVG source {source!r} must be UTF-8 text") from error
        accessible_svg = f'<div role="img" aria-label="{html.escape(alt_text, quote=True)}">\n{svg.rstrip()}\n</div>'
        return [html_block_token(accessible_svg)]

    encoded_image = base64.b64encode(source_path.read_bytes()).decode("ascii")
    data_url = f"data:{media_type};base64,{encoded_image}"
    return image_tokens(parser, data_url, alt_text)


def figure_number(document: SyntaxTreeNode, target: Figure) -> int:
    """Return a figure's one-based position in the completed document.

    Raises:
        ValueError: if target is absent or the same figure instance was appended
            more than once.
    """
    target_number: int | None = None
    number = 0
    for token in document.to_tokens():
        if token.type != DEFERRED_BLOCK_TOKEN_TYPE:
            continue
        block: object = token.meta["block"]
        if not isinstance(block, Figure):
            continue
        number += 1
        if block is not target:
            continue
        if target_number is not None:
            raise ValueError(
                "The same Figure instance cannot be appended more than once; "
                "construct a separate figure for each position"
            )
        target_number = number

    if target_number is None:
        raise ValueError("Figure is not present in the completed report")
    return target_number


@dataclass(frozen=True)
class Figure:
    """An image with alternative text and an optional numbered caption.

    Figures are numbered in document order during rendering.

    Attributes:
        source: Image path or URL written into the Markdown image destination.
        alt_text: Literal alternative text describing the image.
        caption: Optional inline-Markdown caption, prefixed with its figure number.
        params: Template variables applied to source, alternative text, and caption.
        is_embedded: True reads a local raster image into a base64 data URL or
            inserts a local SVG as inline markup. False leaves source as a link.
    """

    source: str | Path
    alt_text: str
    caption: str | None = None
    params: Mapping[str, Any] | None = None
    is_embedded: bool = False

    def __resolve__(self, document: SyntaxTreeNode, report: MarkdownReport) -> list[Token]:
        """Return the image and its number-aware caption."""
        number = figure_number(document, self)
        source = render_template(str(self.source), self.params)
        alt_text = render_template(self.alt_text, self.params)
        tokens: list[Token] = []
        if self.is_embedded:
            tokens.extend(embedded_figure_tokens(report.parser, source, alt_text))
        else:
            tokens.extend(image_tokens(report.parser, source, alt_text))
        if self.caption is not None:
            tokens.extend(
                caption_tokens(
                    report.parser,
                    number,
                    render_template(self.caption, self.params),
                )
            )
        return tokens
