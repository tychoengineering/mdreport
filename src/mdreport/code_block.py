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
    """A fenced code block tagged with an optional language.

    The block behind ``MarkdownReport.code_block``. Construct it directly to hold a
    snippet as a value and append it with ``report.append(...)`` or ``report + ...``.

    Attributes:
        code: Source text, fenced rather than parsed, so Markdown in it stays literal.
        language: Info string driving highlighting; "" for a plain fence.
        title: Bold caption placed above the block.
        params: Template variables, applied to the code as well as the title.
            Leave it None when the code contains Jinja-like braces of its own.

    Example:

        .. code-block:: python

           report.append(CodeBlock("select 1", language="sql", title="Query"))
    """

    code: str
    language: str = ""
    title: str | None = None
    params: Mapping[str, Any] | None = None

    def __report__(self, report: MarkdownReport) -> list[Token]:
        """Return the fence token, preceded by a bold title when one is set."""
        tokens: list[Token] = []
        if self.title:
            tokens.extend(bold_paragraph_tokens(report.parser, render_template(self.title, self.params)))
        tokens.append(fence_token(render_template(self.code, self.params), self.language))
        return tokens
