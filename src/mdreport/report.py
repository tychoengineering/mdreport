from __future__ import annotations

import copy
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Self, cast

import polars as pl
import yaml
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from .code_block import CodeBlock
from .dataframe_formatting import format_dataframe_csv
from .markdown_parser import create_parser
from .markdown_tokens import (
    NestedListItem,
    append_tokens,
    block_tokens,
    bold_paragraph_tokens,
    deferred_block_token,
    fence_token,
    frontmatter_token,
    heading_tokens,
    horizontal_rule_token,
    html_block_token,
    line_break_token,
    list_tokens,
    nested_list_tokens,
    raw_token,
)
from .report_block import (
    DEFERRED_BLOCK_TOKEN_TYPE,
    DeferredReportBlock,
    ReportBlock,
)
from .table import Table
from .table_of_contents import TableOfContents
from .template_rendering import (
    render_nested_template_items,
    render_template,
    render_template_items,
)

__all__ = ["MarkdownReport"]


def dict_to_yaml(data: Mapping[str, Any]) -> str:
    """Serialize report metadata as safe YAML."""
    if not data:
        return ""
    return yaml.safe_dump(
        dict(data),
        allow_unicode=True,
        sort_keys=False,
    ).rstrip("\n")


class MarkdownReport:
    """Build a Markdown document."""

    def __init__(self) -> None:
        """Create an empty report."""
        self.parser = create_parser()
        self.document = SyntaxTreeNode()
        self.frontmatter_data: dict[str, Any] = {}

    def append(self, block: ReportBlock | DeferredReportBlock) -> MarkdownReport:
        """Append a block's content to this report.

        A block implementing `__resolve__` is stored as a placeholder and
        resolved during `render`; every other block contributes its content
        immediately.
        """
        if isinstance(block, DeferredReportBlock):
            append_tokens(self.document, [deferred_block_token(block)])
            return self
        append_tokens(self.document, block_tokens(self.parser, block.__report__(self)))
        return self

    def copy(self) -> Self:
        """Return an independent report holding the same content and metadata."""
        duplicate = type(self)()
        duplicate.document = SyntaxTreeNode(self.document.to_tokens())
        duplicate.parser.environment = copy.deepcopy(self.parser.environment)
        duplicate.frontmatter_data = copy.deepcopy(self.frontmatter_data)
        return duplicate

    def __add__(self, block: ReportBlock | DeferredReportBlock) -> Self:
        """Return a copy of this report with a block appended, leaving it unchanged."""
        duplicate = self.copy()
        duplicate.append(block)
        return duplicate

    def __iadd__(self, block: ReportBlock | DeferredReportBlock) -> Self:
        """Append a block to this report in place."""
        self.append(block)
        return self

    def frontmatter(self, data: Mapping[str, Any] | None = None, **kwargs: Any) -> MarkdownReport:
        """Merge YAML frontmatter fields into the report metadata."""
        self.frontmatter_data.update({**(data or {}), **kwargs})
        return self

    def markdown(self, content: str, params: Mapping[str, Any] | None = None) -> MarkdownReport:
        """Parse and append raw Markdown content."""
        append_tokens(self.document, self.parser.parse(render_template(content, params)))
        return self

    def directive(self, name: str, value: str | None = None) -> MarkdownReport:
        """Append a smolslides HTML-comment directive."""
        directive = f"<!-- _{name}: {value} -->" if value is not None else f"<!-- _{name} -->"
        append_tokens(self.document, [html_block_token(directive)])
        return self

    def title(self, text: str, params: Mapping[str, Any] | None = None) -> MarkdownReport:
        """Append an H1 heading."""
        return self.heading(text, level=1, params=params)

    def heading(
        self,
        text: str,
        level: int = 2,
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a heading at a level from one through six.

        Raises:
            ValueError: if level is outside the Markdown heading range.
        """
        tokens = heading_tokens(self.parser, render_template(text, params), level)
        append_tokens(self.document, tokens)
        return self

    def text(
        self,
        content: str | list[str],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Parse and append one or more Markdown text blocks."""
        blocks = [content] if isinstance(content, str) else content
        for block in blocks:
            self.markdown(str(block), params)
        return self

    def bullet_list(
        self,
        items: list[str],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append an unordered list."""
        rendered_items = render_template_items(items, params)
        append_tokens(self.document, list_tokens(self.parser, rendered_items, is_ordered=False))
        return self

    def numbered_list(
        self,
        items: list[str],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a consecutively numbered list."""
        rendered_items = render_template_items(items, params)
        append_tokens(self.document, list_tokens(self.parser, rendered_items, is_ordered=True))
        return self

    def nested_list(
        self,
        items: list[NestedListItem],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a recursively nested unordered list."""
        rendered_items = render_nested_template_items(items, params)
        append_tokens(self.document, nested_list_tokens(self.parser, rendered_items))
        return self

    def table(
        self,
        df: pl.DataFrame,
        title: str | None = None,
        params: Mapping[str, Any] | None = None,
        decimal_places: int = 2,
    ) -> MarkdownReport:
        """Append every DataFrame column and row as a GFM Markdown table."""
        return self.append(
            Table(df, title=title, params=params, decimal_places=decimal_places)
        )

    def csv(
        self,
        df: pl.DataFrame,
        title: str | None = None,
        params: Mapping[str, Any] | None = None,
        decimal_places: int = 2,
        wrap_code: bool = True,
    ) -> MarkdownReport:
        """Append a DataFrame as CSV, optionally inside a fenced code block."""
        if title:
            append_tokens(
                self.document,
                bold_paragraph_tokens(self.parser, render_template(title, params)),
            )

        csv_content = format_dataframe_csv(df, decimal_places=decimal_places)
        content_token = (
            fence_token(csv_content, "csv") if wrap_code else raw_token(csv_content)
        )
        append_tokens(self.document, [content_token])
        return self

    def code_block(
        self,
        code: str,
        language: str = "",
        title: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a syntax-highlighted fenced code block."""
        return self.append(CodeBlock(code, language=language, title=title, params=params))

    def line_break(self) -> MarkdownReport:
        """Append one additional blank line between document blocks."""
        append_tokens(self.document, [line_break_token()])
        return self

    def horizontal_rule(self) -> MarkdownReport:
        """Append a thematic break."""
        append_tokens(self.document, [horizontal_rule_token()])
        return self

    def table_of_contents(self) -> MarkdownReport:
        """Append a deferred table of contents resolved from the final tree."""
        return self.append(TableOfContents())

    def render(self) -> str:
        """Serialize the complete report syntax tree as Markdown."""
        document = SyntaxTreeNode(self.document.to_tokens())
        resolved_tokens: list[Token] = []
        for token in document.to_tokens():
            if token.type == DEFERRED_BLOCK_TOKEN_TYPE:
                block = cast(DeferredReportBlock, token.meta["block"])
                resolved_tokens.extend(
                    block_tokens(self.parser, block.__resolve__(document, self))
                )
            else:
                resolved_tokens.append(token)

        if self.frontmatter_data:
            resolved_tokens.insert(0, frontmatter_token(dict_to_yaml(self.frontmatter_data)))

        return self.parser.render(SyntaxTreeNode(resolved_tokens).to_tokens())

    def save(self, filename: str | Path) -> MarkdownReport:
        """Write the rendered report as UTF-8 Markdown."""
        Path(filename).write_text(self.render(), encoding="utf-8")
        return self

    def __str__(self) -> str:
        """Return the rendered Markdown report."""
        return self.render()
