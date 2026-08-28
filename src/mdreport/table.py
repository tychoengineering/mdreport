from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import polars as pl
from markdown_it.token import Token

from .dataframe_formatting import format_dataframe
from .markdown_tokens import bold_paragraph_tokens, table_tokens
from .template_rendering import render_template

if TYPE_CHECKING:
    from .report import MarkdownReport

__all__ = ["Table"]


# eq=False because a DataFrame field would make the generated __eq__ return a
# DataFrame of element-wise comparisons rather than a bool.
@dataclass(frozen=True, eq=False)
class Table:
    """Every column and row of a DataFrame as a GFM table."""

    dataframe: pl.DataFrame
    title: str | None = None
    params: Mapping[str, Any] | None = None
    decimal_places: int = 2

    def __report__(self, report: MarkdownReport) -> list[Token]:
        """Return the table tokens, preceded by a bold title when one is set."""
        tokens: list[Token] = []
        if self.title:
            tokens.extend(
                bold_paragraph_tokens(report.parser, render_template(self.title, self.params))
            )
        tokens.extend(
            table_tokens(report.parser, format_dataframe(self.dataframe, self.decimal_places))
        )
        return tokens
