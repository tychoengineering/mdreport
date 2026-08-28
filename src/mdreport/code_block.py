from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from markdown_it.token import Token

from .markdown_tokens import bold_paragraph_tokens, fence_token
from .template_rendering import render_template

if TYPE_CHECKING:
    from .report import MarkdownReport

__all__ = ["CodeBlock"]


@dataclass(frozen=True)
class CodeBlock:
    """A fenced code block tagged with an optional language."""

    code: str
    language: str = ""
    title: str | None = None
    params: Mapping[str, Any] | None = None

    def __report__(self, report: MarkdownReport) -> list[Token]:
        """Return the fence token, preceded by a bold title when one is set."""
        tokens: list[Token] = []
        if self.title:
            tokens.extend(
                bold_paragraph_tokens(report.parser, render_template(self.title, self.params))
            )
        tokens.append(fence_token(render_template(self.code, self.params), self.language))
        return tokens
