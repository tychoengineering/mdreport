from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from markdown_it.token import Token

if TYPE_CHECKING:
    from markdown_it.tree import SyntaxTreeNode

    from .report import MarkdownReport

__all__ = [
    "DEFERRED_BLOCK_TOKEN_TYPE",
    "BlockContent",
    "DeferredReportBlock",
    "ReportBlock",
]

type BlockContent = str | Token | Sequence[Token]

DEFERRED_BLOCK_TOKEN_TYPE = "report_deferred"


@runtime_checkable
class ReportBlock(Protocol):
    """A self-contained unit of report content."""

    def __report__(self, report: MarkdownReport) -> BlockContent:
        """Return this block's content, as Markdown text or as tokens.

        The report is passed for its `parser`, which the token builders in
        `markdown_tokens` (`paragraph_tokens`, `table_tokens`, `list_tokens`)
        take. Implementations must not append to it.
        """
        ...


@runtime_checkable
class DeferredReportBlock(Protocol):
    """Report content whose value depends on the completed document.

    A deferred block is appended as a placeholder and resolved once, at render
    time, against the document as it finally stands. Use it for content that
    reads the rest of the report — tables of contents, cross-references,
    figure numbering.
    """

    def __resolve__(self, document: SyntaxTreeNode, report: MarkdownReport) -> BlockContent:
        """Return this block's content for the completed document.

        The document excludes deferred placeholders' own content, so a
        deferred block never observes another deferred block's output.
        """
        ...
