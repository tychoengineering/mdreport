from __future__ import annotations

import io
from typing import Any

import polars as pl
import polars.selectors as cs

__all__ = ["format_dataframe", "format_dataframe_csv", "format_table_cell"]


def format_dataframe(dataframe: pl.DataFrame, decimal_places: int) -> pl.DataFrame:
    """Normalize list and float columns for report exports."""
    formatted_dataframe = dataframe.with_columns(cs.by_dtype(pl.List(pl.String)).list.join(", "))
    return formatted_dataframe.with_columns(
        cs.by_dtype(pl.Float32, pl.Float64).cast(pl.Decimal(scale=decimal_places))
    )


def format_dataframe_csv(dataframe: pl.DataFrame, decimal_places: int = 2) -> str:
    """Serialize a normalized DataFrame as CSV without its record terminator."""
    output = io.StringIO()
    format_dataframe(dataframe, decimal_places).write_csv(output)
    return output.getvalue().rstrip("\n")


def format_table_cell(cell: Any) -> str:
    """Format a complete DataFrame cell without display truncation."""
    if cell is None:
        return "null"
    if isinstance(cell, bool):
        return str(cell).lower()
    cell_text = str(cell).replace("\r\n", "\n").replace("\r", "\n")
    return cell_text.replace("\n", "<br>")
