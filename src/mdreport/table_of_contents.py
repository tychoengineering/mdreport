from __future__ import annotations

import copy
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

if TYPE_CHECKING:
    from .report import MarkdownReport

__all__ = ["TableOfContents", "TableOfContentsEntry"]


@dataclass
class TableOfContentsEntry:
    """A heading and the headings nested beneath it in document order."""

    level: int
    inline: Token
    children: list[TableOfContentsEntry] = field(default_factory=list)


@dataclass(frozen=True)
class TableOfContents:
    """A nested list of every heading in the finished report.

    The block behind ``MarkdownReport.table_of_contents``, and the reference
    ``DeferredReportBlock``: it is appended as a placeholder and resolved during
    ``render``, so it lists headings added after it as well as before. Entries nest
    by heading level and are plain text, not links.

    Example:

        .. code-block:: python

           report.append(TableOfContents())
    """

    def __resolve__(self, document: SyntaxTreeNode, report: MarkdownReport) -> list[Token]:
        """Return list tokens mirroring the document's heading hierarchy."""
        return self.contents_tokens(self.entries(document))

    def entries(self, document: SyntaxTreeNode) -> list[TableOfContentsEntry]:
        """Collect headings into a hierarchy based on document order and level.

        Raises:
            ValueError: if a heading node contains no inline token.
        """
        root_entries: list[TableOfContentsEntry] = []
        ancestors: list[TableOfContentsEntry] = []

        for node in document.walk():
            if node.type != "heading":
                continue
            inline_node = next((child for child in node.children if child.type == "inline"), None)
            if inline_node is None:
                continue
            if inline_node.token is None:
                raise ValueError("Heading inline node must contain a token")

            entry = TableOfContentsEntry(
                level=int(node.tag.removeprefix("h")),
                inline=copy.deepcopy(inline_node.token),
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
                    copy.deepcopy(entry.inline),
                    Token("paragraph_close", "p", -1, block=True, hidden=True),
                ]
            )
            tokens.extend(self.contents_tokens(entry.children))
            tokens.append(Token("list_item_close", "li", -1, markup="-", block=True))
        tokens.append(Token("bullet_list_close", "ul", -1, markup="-", block=True))
        return tokens
