from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import polars as pl
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from .dataframe_formatting import format_table_cell
from .report_block import DEFERRED_BLOCK_TOKEN_TYPE, BlockContent, DeferredReportBlock

if TYPE_CHECKING:
    from .markdown_parser import MarkdownParser

__all__ = [
    "NestedListItem",
    "append_tokens",
    "block_tokens",
    "bold_paragraph_tokens",
    "deferred_block_token",
    "fence_token",
    "frontmatter_token",
    "heading_tokens",
    "horizontal_rule_token",
    "html_block_token",
    "line_break_token",
    "list_item_tokens",
    "list_tokens",
    "nested_list_tokens",
    "paragraph_tokens",
    "raw_token",
    "table_cell_tokens",
    "table_tokens",
]

type NestedListItem = str | list[NestedListItem]


def append_tokens(document: SyntaxTreeNode, tokens: Sequence[Token]) -> None:
    """Append a valid token fragment to a report syntax tree."""
    fragment = SyntaxTreeNode(list(tokens))
    for child in fragment.children:
        child.parent = document
        document.children.append(child)


def block_tokens(parser: MarkdownParser, content: BlockContent) -> list[Token]:
    """Normalize block content into a token stream, parsing Markdown text."""
    if isinstance(content, str):
        return parser.parse(content)
    if isinstance(content, Token):
        return [content]
    return list(content)


def paragraph_tokens(
    parser: MarkdownParser,
    content: str,
    *,
    is_hidden: bool = False,
) -> list[Token]:
    """Build a paragraph token pair containing parsed inline Markdown."""
    return [
        Token("paragraph_open", "p", 1, block=True, hidden=is_hidden),
        parser.parse_inline(content),
        Token("paragraph_close", "p", -1, block=True, hidden=is_hidden),
    ]


def bold_paragraph_tokens(parser: MarkdownParser, content: str) -> list[Token]:
    """Build a paragraph whose complete inline content is strong text."""
    inline = parser.parse_inline(content)
    inline.children = [
        Token("strong_open", "strong", 1, markup="**"),
        *(inline.children or []),
        Token("strong_close", "strong", -1, markup="**"),
    ]
    return [
        Token("paragraph_open", "p", 1, block=True),
        inline,
        Token("paragraph_close", "p", -1, block=True),
    ]


def heading_tokens(parser: MarkdownParser, content: str, level: int) -> list[Token]:
    """Build a heading at a level from one through six.

    Raises:
        ValueError: if level is outside the Markdown heading range.
    """
    if not 1 <= level <= 6:
        raise ValueError("Heading level must be between 1 and 6")

    markup = "#" * level
    return [
        Token("heading_open", f"h{level}", 1, markup=markup, block=True),
        parser.parse_inline(content),
        Token("heading_close", f"h{level}", -1, markup=markup, block=True),
    ]


def list_tokens(parser: MarkdownParser, items: Sequence[str], *, is_ordered: bool) -> list[Token]:
    """Build a flat ordered or unordered list token stream."""
    list_type = "ordered_list" if is_ordered else "bullet_list"
    list_tag = "ol" if is_ordered else "ul"
    marker = "." if is_ordered else "-"
    tokens = [Token(f"{list_type}_open", list_tag, 1, markup=marker, block=True)]

    for index, item in enumerate(items, 1):
        tokens.append(
            Token(
                "list_item_open",
                "li",
                1,
                markup=marker,
                info=str(index) if is_ordered else "",
                block=True,
            )
        )
        tokens.extend(paragraph_tokens(parser, item, is_hidden=True))
        tokens.append(Token("list_item_close", "li", -1, markup=marker, block=True))

    tokens.append(Token(f"{list_type}_close", list_tag, -1, markup=marker, block=True))
    return tokens


def nested_list_tokens(parser: MarkdownParser, items: Sequence[NestedListItem]) -> list[Token]:
    """Build recursively nested unordered-list tokens."""
    tokens = [Token("bullet_list_open", "ul", 1, markup="-", block=True)]
    has_open_item = False

    for item in items:
        if isinstance(item, list):
            if has_open_item:
                tokens.extend(nested_list_tokens(parser, item))
            else:
                leading_items = [entry for entry in item if isinstance(entry, str)]
                for leading_item in leading_items:
                    tokens.extend(list_item_tokens(parser, leading_item))
            continue

        if has_open_item:
            tokens.append(Token("list_item_close", "li", -1, markup="-", block=True))
        tokens.append(Token("list_item_open", "li", 1, markup="-", block=True))
        tokens.extend(paragraph_tokens(parser, item, is_hidden=True))
        has_open_item = True

    if has_open_item:
        tokens.append(Token("list_item_close", "li", -1, markup="-", block=True))
    tokens.append(Token("bullet_list_close", "ul", -1, markup="-", block=True))
    return tokens


def list_item_tokens(parser: MarkdownParser, content: str) -> list[Token]:
    """Build one complete unordered-list item."""
    return [
        Token("list_item_open", "li", 1, markup="-", block=True),
        *paragraph_tokens(parser, content, is_hidden=True),
        Token("list_item_close", "li", -1, markup="-", block=True),
    ]


def table_tokens(parser: MarkdownParser, dataframe: pl.DataFrame) -> list[Token]:
    """Build a GFM table from every DataFrame column and row."""
    if dataframe.width == 0:
        return [raw_token("||")]

    tokens = [
        Token("table_open", "table", 1, block=True),
        Token("thead_open", "thead", 1, block=True),
        Token("tr_open", "tr", 1, block=True),
    ]
    for column_name in dataframe.columns:
        tokens.extend(table_cell_tokens(parser, format_table_cell(column_name), is_header=True))
    tokens.extend(
        [
            Token("tr_close", "tr", -1, block=True),
            Token("thead_close", "thead", -1, block=True),
            Token("tbody_open", "tbody", 1, block=True),
        ]
    )

    for row in dataframe.iter_rows():
        tokens.append(Token("tr_open", "tr", 1, block=True))
        for cell in row:
            tokens.extend(table_cell_tokens(parser, format_table_cell(cell), is_header=False))
        tokens.append(Token("tr_close", "tr", -1, block=True))

    tokens.extend(
        [
            Token("tbody_close", "tbody", -1, block=True),
            Token("table_close", "table", -1, block=True),
        ]
    )
    return tokens


def table_cell_tokens(parser: MarkdownParser, content: str, *, is_header: bool) -> list[Token]:
    """Build one table header or body cell with inline Markdown."""
    cell_type = "th" if is_header else "td"
    return [
        Token(f"{cell_type}_open", cell_type, 1, block=True),
        parser.parse_inline(content),
        Token(f"{cell_type}_close", cell_type, -1, block=True),
    ]


def fence_token(content: str, language: str = "") -> Token:
    """Build a fenced code block, terminating the content with a newline."""
    if not content.endswith("\n"):
        content = f"{content}\n"
    return Token("fence", "code", 0, content=content, markup="```", info=language, block=True)


def raw_token(content: str) -> Token:
    """Build content that renders verbatim, bypassing Markdown formatting."""
    return Token("report_raw", "", 0, content=content, block=True)


def html_block_token(content: str) -> Token:
    """Build a raw HTML block."""
    return Token("html_block", "", 0, content=content, block=True)


def frontmatter_token(content: str) -> Token:
    """Build the YAML metadata block that opens a report."""
    return Token("report_frontmatter", "", 0, content=content, block=True)


def line_break_token() -> Token:
    """Build one additional blank line between document blocks."""
    return Token("report_line_break", "", 0, block=True)


def horizontal_rule_token() -> Token:
    """Build a thematic break."""
    return Token("hr", "hr", 0, markup="---", block=True)


def deferred_block_token(block: DeferredReportBlock) -> Token:
    """Build the placeholder standing in for a block resolved at render time."""
    meta: dict[str, Any] = {"block": block}
    return Token(DEFERRED_BLOCK_TOKEN_TYPE, "", 0, block=True, meta=meta)
