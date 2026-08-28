from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from .heading_anchors import anchor_link_inline, document_anchors

if TYPE_CHECKING:
    from .report import MarkdownReport

__all__ = ["TableOfContents", "TableOfContentsEntry"]

MAXIMUM_HEADING_LEVEL = 6


@dataclass
class TableOfContentsEntry:
    """A heading, the anchor linking to it, and the headings nested beneath it."""

    level: int
    inline: Token
    slug: str
    children: list[TableOfContentsEntry] = field(default_factory=list)


@dataclass(frozen=True)
class TableOfContents:
    """A nested list of the report's headings, linked to their anchors.

    The block behind ``MarkdownReport.table_of_contents``, and the reference
    ``DeferredReportBlock``: it is appended as a placeholder and resolved during
    ``render``, so it lists headings added after it as well as before. Entries
    nest by heading level.

    Entries link to the anchor a renderer derives from the heading text, which
    resolves as-is on GitHub, GitLab, Pandoc, and MkDocs. Where the renderer
    generates no anchors, build the report with a ``MarkdownReport``
    ``anchor_style`` that writes them into the document.

    Args:
        start_level: Shallowest heading level listed; headings above it are
            skipped along with the nesting they would have introduced.
        depth: How many heading levels to list, counting from ``start_level``.
        is_linked: False renders entries as plain text, for a document whose
            anchors cannot be relied on.

    Raises:
        ValueError: if start_level is outside the Markdown heading range, or
            depth is less than one.

    Example:

        .. code-block:: python

           report.append(TableOfContents())
           report.append(TableOfContents(start_level=2, depth=2))  # h2 and h3 only
    """

    start_level: int = 1
    depth: int = MAXIMUM_HEADING_LEVEL
    is_linked: bool = True

    def __post_init__(self) -> None:
        """Reject a scope that no heading could fall in."""
        if not 1 <= self.start_level <= MAXIMUM_HEADING_LEVEL:
            raise ValueError("Table of contents start_level must be between 1 and 6")
        if self.depth < 1:
            raise ValueError("Table of contents depth must be at least 1")

    @property
    def end_level(self) -> int:
        """Deepest heading level listed, clamped to the Markdown heading range."""
        return min(MAXIMUM_HEADING_LEVEL, self.start_level + self.depth - 1)

    def __resolve__(self, document: SyntaxTreeNode, report: MarkdownReport) -> list[Token]:
        """Return list tokens mirroring the document's heading hierarchy."""
        return self.contents_tokens(self.entries(document))

    def entries(self, document: SyntaxTreeNode) -> list[TableOfContentsEntry]:
        """Collect the headings in scope into a hierarchy, in document order.

        Raises:
            ValueError: if a heading node contains no inline token.
        """
        root_entries: list[TableOfContentsEntry] = []
        ancestors: list[TableOfContentsEntry] = []

        for anchor in document_anchors(document):
            if not self.start_level <= anchor.level <= self.end_level:
                continue

            entry = TableOfContentsEntry(
                level=anchor.level,
                inline=anchor.inline,
                slug=anchor.slug,
            )
            while ancestors and ancestors[-1].level >= entry.level:
                ancestors.pop()
            if ancestors:
                ancestors[-1].children.append(entry)
            else:
                root_entries.append(entry)
            ancestors.append(entry)
        return root_entries

    def contents_tokens(self, entries: Sequence[TableOfContentsEntry]) -> list[Token]:
        """Build nested unordered-list tokens for table-of-contents entries."""
        if not entries:
            return []

        tokens = [Token("bullet_list_open", "ul", 1, markup="-", block=True)]
        for entry in entries:
            tokens.append(Token("list_item_open", "li", 1, markup="-", block=True))
            tokens.extend(
                [
                    Token("paragraph_open", "p", 1, block=True, hidden=True),
                    self.entry_inline(entry),
                    Token("paragraph_close", "p", -1, block=True, hidden=True),
                ]
            )
            tokens.extend(self.contents_tokens(entry.children))
            tokens.append(Token("list_item_close", "li", -1, markup="-", block=True))
        tokens.append(Token("bullet_list_close", "ul", -1, markup="-", block=True))
        return tokens

    def entry_inline(self, entry: TableOfContentsEntry) -> Token:
        """Build one entry's inline content, linked to its heading's anchor."""
        if not self.is_linked:
            return copy.deepcopy(entry.inline)
        return anchor_link_inline(entry.inline, entry.slug)
