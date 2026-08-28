"""Build Markdown reports from a fluent API, extensible with custom blocks.

Most callers need only `MarkdownReport` and the built-in blocks (`CodeBlock`,
`Table`, `TableOfContents`). The rest of this surface exists for writing custom
blocks: implement `ReportBlock` (or `DeferredReportBlock`) and build the
`BlockContent` you return with the token builders and `render_template`.
"""

__version__ = "0.0.1a1"

from .code_block import CodeBlock
from .dataframe_formatting import format_dataframe, format_dataframe_csv
from .markdown_parser import MarkdownParser
from .markdown_tokens import (
    NestedListItem,
    bold_paragraph_tokens,
    fence_token,
    heading_tokens,
    list_item_tokens,
    list_tokens,
    nested_list_tokens,
    paragraph_tokens,
    raw_token,
    table_cell_tokens,
    table_tokens,
)
from .report import MarkdownReport
from .report_block import BlockContent, DeferredReportBlock, ReportBlock
from .table import Table
from .table_of_contents import TableOfContents
from .template_rendering import (
    render_nested_template_items,
    render_template,
    render_template_items,
)

__all__ = [
    "BlockContent",
    "CodeBlock",
    "DeferredReportBlock",
    "MarkdownParser",
    "MarkdownReport",
    "NestedListItem",
    "ReportBlock",
    "Table",
    "TableOfContents",
    "bold_paragraph_tokens",
    "fence_token",
    "format_dataframe",
    "format_dataframe_csv",
    "heading_tokens",
    "list_item_tokens",
    "list_tokens",
    "nested_list_tokens",
    "paragraph_tokens",
    "raw_token",
    "render_nested_template_items",
    "render_template",
    "render_template_items",
    "table_cell_tokens",
    "table_tokens",
]
