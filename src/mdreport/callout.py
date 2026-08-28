from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from markdown_it.token import Token

from .markdown_tokens import bold_paragraph_tokens
from .template_rendering import render_template

if TYPE_CHECKING:
    from .report import MarkdownReport

__all__ = ["Callout", "CalloutKind"]


class CalloutKind(enum.StrEnum):
    """Portable semantic categories for a report callout."""

    NOTE = "note"
    TIP = "tip"
    IMPORTANT = "important"
    WARNING = "warning"
    CAUTION = "caution"


@dataclass(frozen=True)
class Callout:
    """A titled block quote drawing attention to report content.

    Attributes:
        message: Markdown content displayed inside the callout.
        kind: Semantic category supplying the default title.
        title: Optional title overriding the category name.
        params: Template variables applied to the message and custom title.
    """

    message: str
    kind: CalloutKind = CalloutKind.NOTE
    title: str | None = None
    params: Mapping[str, Any] | None = None

    def __report__(self, report: MarkdownReport) -> list[Token]:
        """Return a portable block quote containing a bold title and body."""
        title = self.kind.value.title() if self.title is None else render_template(self.title, self.params)
        return [
            Token("blockquote_open", "blockquote", 1, markup=">", block=True),
            *bold_paragraph_tokens(report.parser, title),
            *report.parser.parse(render_template(self.message, self.params)),
            Token("blockquote_close", "blockquote", -1, markup=">", block=True),
        ]
