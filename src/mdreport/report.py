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
    r"""Build a Markdown document.

    Provides a fluent interface for building markdown documents with various content types
    including headings, text, tables, lists, code blocks, and more. Supports Jinja2
    template rendering for dynamic content generation.

    Features:

        - Method chaining for fluent report building
        - Jinja2 template support for dynamic content
        - Polars DataFrame integration for tables and CSV exports
        - Automatic formatting of numeric data with configurable precision
        - Support for nested lists and various markdown elements
        - Export to file or string rendering

    Methods:

        - frontmatter(data=None, **kwargs): Add YAML frontmatter
        - directive(name, value=None): Add smolslides directive
        - markdown(content, params=None): Add raw markdown content
        - title(text, params=None): Add H1 heading
        - heading(text, level=2, params=None): Add heading (H1-H6)
        - text(content, params=None): Add text paragraphs
        - bullet_list(items, params=None): Add bullet list
        - numbered_list(items, params=None): Add numbered list
        - nested_list(items, params=None): Add nested list with sublists
        - table(df, title=None, params=None, decimal_places=2): Add DataFrame as markdown table
        - csv(df, title=None, params=None, decimal_places=2): Add DataFrame as CSV code block
        - code_block(code, language="", title=None, params=None): Add syntax-highlighted code block
        - line_break(): Add line break
        - horizontal_rule(): Add horizontal rule
        - table_of_contents(): Add table of contents based on headings
        - append(block): Add a custom ReportBlock or DeferredReportBlock
        - render(): Get final markdown as string
        - save(filename): Save report to file

    Example:
        ```python
        report = (MarkdownReport()
            .frontmatter(title="My Report", author="John Doe", date="2024-06-26")
            .frontmatter({"description": "A comprehensive analysis\nwith multiple sections"})
            .directive("class", "title")
            .title("My Report")
            .text("---")  # Slide separator for smolslides
            .directive("class", "segue")
            .heading("Overview")
            .text("---")
            .table_of_contents()
            .heading("Heading level 2")
            .text(["Paragraph 1", "Paragraph 2"])
            .heading("Heading level 3", level=3)
            .table(df, title="Data Summary")
            .bullet_list(["Point 1", "Point 2"])
            .numbered_list(["Step 1", "Step 2"])
            .nested_list(["Main point", ["Sub-point 1", "Sub-point 2"]])
            .code_block("print('Hello, World!')", language="python", title="Example Code")
            .horizontal_rule()
            .text("Report generated on {{date}}", params={"date": "2024-06-26"})
            .save("report.md")
        )
        print(report)
        ```

    Every content method returns the report itself, so calls chain. Content is
    held as a Markdown syntax tree rather than as text, so `render` is what
    serializes it; a report can be rendered repeatedly and keeps building
    afterwards.
    """

    def __init__(self) -> None:
        """Create an empty report with its own parser and no frontmatter."""
        self.parser = create_parser()
        self.document = SyntaxTreeNode()
        self.frontmatter_data: dict[str, Any] = {}

    def append(self, block: ReportBlock | DeferredReportBlock) -> MarkdownReport:
        """Append a block's content to this report.

        This is the extension point behind `table`, `code_block`, and
        `table_of_contents`, and the way to add a block of your own: any object
        with a `__report__` method satisfies `ReportBlock`.

        A block implementing `__resolve__` (a `DeferredReportBlock`) is stored as
        a placeholder and resolved during `render`, once the whole document is
        known; every other block contributes its content immediately.

        Example:
            ```python
            @dataclass(frozen=True)
            class Callout:
                message: str

                def __report__(self, report: MarkdownReport) -> BlockContent:
                    return f"> **Note:** {self.message}"

            report.append(Callout("Numbers are provisional."))
            ```
        """
        if isinstance(block, DeferredReportBlock):
            append_tokens(self.document, [deferred_block_token(block)])
            return self
        append_tokens(self.document, block_tokens(self.parser, block.__report__(self)))
        return self

    def copy(self) -> Self:
        """Return an independent report holding the same content and metadata.

        Content, frontmatter, and parser state are independent, so appending to
        the copy never affects this report. Use it to build several documents
        from a shared preamble.

        Example:
            ```python
            preamble = MarkdownReport().title("Weekly Report").table_of_contents()
            for team in teams:
                preamble.copy().heading(team.name).table(team.metrics).save(f"{team.name}.md")
            ```
        """
        duplicate = type(self)()
        duplicate.document = SyntaxTreeNode(self.document.to_tokens())
        duplicate.parser.environment = copy.deepcopy(self.parser.environment)
        duplicate.frontmatter_data = copy.deepcopy(self.frontmatter_data)
        return duplicate

    def __add__(self, block: ReportBlock | DeferredReportBlock) -> Self:
        """Return a copy of this report with a block appended, leaving it unchanged.

        Example:
            ```python
            summary = base + Callout("All checks passed")  # base is untouched
            ```
        """
        duplicate = self.copy()
        duplicate.append(block)
        return duplicate

    def __iadd__(self, block: ReportBlock | DeferredReportBlock) -> Self:
        """Append a block to this report in place.

        Example:
            ```python
            report += Callout("All checks passed")
            ```
        """
        self.append(block)
        return self

    def frontmatter(self, data: Mapping[str, Any] | None = None, **kwargs: Any) -> MarkdownReport:
        """Merge YAML frontmatter fields into the report metadata.

        Fields accumulate across calls and later values win, so frontmatter can
        be set up front and amended once results are known. The block is emitted
        at the top of the document by `render`, in insertion order, and is
        omitted entirely when no fields were set.

        Args:
            data: Fields to merge, for keys that are not valid identifiers.
            **kwargs: Fields to merge, for keys that are.

        Example:
            ```python
            report.frontmatter(title="Q3 Review", author="Asif")
            report.frontmatter({"table-of-contents": True})  # key needs the mapping form
            ```
        """
        self.frontmatter_data.update({**(data or {}), **kwargs})
        return self

    def markdown(self, content: str, params: Mapping[str, Any] | None = None) -> MarkdownReport:
        """Parse and append raw Markdown content.

        The escape hatch for Markdown the other methods don't build: block quotes,
        footnotes, images, or a whole section held as a string. Content is parsed,
        not inserted verbatim, so it must be valid Markdown; use `raw_token` via
        `append` for text that must survive untouched.

        Args:
            content: Markdown source, treated as a Jinja template when params is given.
            params: Template variables. None leaves the content unrendered, so
                literal braces pass through safely.

        Example:
            ```python
            report.markdown("> Quoted, with an ![image](chart.png)")
            report.markdown("Owner: {{name}}", params={"name": "Asif"})
            ```
        """
        append_tokens(self.document, self.parser.parse(render_template(content, params)))
        return self

    def directive(self, name: str, value: str | None = None) -> MarkdownReport:
        """Append a smolslides HTML-comment directive.

        Directives are HTML comments, so they are invisible to Markdown renderers
        that don't understand them.

        Args:
            name: Directive name, written with the leading underscore smolslides
                expects (`class` becomes `<!-- _class: ... -->`).
            value: Directive argument, or None for a bare flag directive.

        Example:
            ```python
            report.directive("class", "title")  # <!-- _class: title -->
            report.directive("paginate")        # <!-- _paginate -->
            ```
        """
        directive = f"<!-- _{name}: {value} -->" if value is not None else f"<!-- _{name} -->"
        append_tokens(self.document, [html_block_token(directive)])
        return self

    def title(self, text: str, params: Mapping[str, Any] | None = None) -> MarkdownReport:
        """Append an H1 heading.

        Shorthand for `heading(text, level=1)`. Headings added by any method are
        what `table_of_contents` later collects.

        Example:
            ```python
            report.title("Q3 Review")
            ```
        """
        return self.heading(text, level=1, params=params)

    def heading(
        self,
        text: str,
        level: int = 2,
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a heading at a level from one through six.

        Inline Markdown in the text is parsed, so a heading can carry emphasis or
        a link. Every heading becomes an entry in `table_of_contents`, nested by
        its level.

        Args:
            text: Heading text, treated as a Jinja template when params is given.
            level: Heading level, 1 (`#`) through 6 (`######`).
            params: Template variables.

        Raises:
            ValueError: if level is outside the Markdown heading range.

        Example:
            ```python
            report.heading("Findings")
            report.heading("Region: {{region}}", level=3, params={"region": "EMEA"})
            ```
        """
        tokens = heading_tokens(self.parser, render_template(text, params), level)
        append_tokens(self.document, tokens)
        return self

    def text(
        self,
        content: str | list[str],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Parse and append one or more Markdown text blocks.

        A list appends each entry as its own separate block, which is how to get
        distinct paragraphs; a single string containing blank lines parses into
        paragraphs too.

        Args:
            content: One Markdown block, or a list of them.
            params: Template variables, applied to every block.

        Example:
            ```python
            report.text("A single paragraph with **emphasis**.")
            report.text(["First paragraph.", "Second paragraph."])
            report.text("Generated {{date}}", params={"date": "2024-06-26"})
            ```
        """
        blocks = [content] if isinstance(content, str) else content
        for block in blocks:
            self.markdown(str(block), params)
        return self

    def bullet_list(
        self,
        items: list[str],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append an unordered list.

        Items are parsed as inline Markdown, so they can carry emphasis, code, or
        links. An empty list appends an empty list block.

        Args:
            items: List items, each treated as a Jinja template when params is given.
            params: Template variables, applied to every item.

        Example:
            ```python
            report.bullet_list(["Revenue up 4%", "Churn flat", "See [detail](d.md)"])
            ```
        """
        rendered_items = render_template_items(items, params)
        append_tokens(self.document, list_tokens(self.parser, rendered_items, is_ordered=False))
        return self

    def numbered_list(
        self,
        items: list[str],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a consecutively numbered list.

        Numbering is generated from position, starting at 1 — don't write numbers
        into the items themselves.

        Args:
            items: List items, each treated as a Jinja template when params is given.
            params: Template variables, applied to every item.

        Example:
            ```python
            report.numbered_list(["Extract", "Transform", "Load"])
            ```
        """
        rendered_items = render_template_items(items, params)
        append_tokens(self.document, list_tokens(self.parser, rendered_items, is_ordered=True))
        return self

    def nested_list(
        self,
        items: list[NestedListItem],
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a recursively nested unordered list.

        A nested list follows the item it belongs to, so a sublist is written as a
        list immediately after the string it hangs beneath. Nesting is unbounded.

        Args:
            items: Strings, and lists of items that nest under the preceding string.
            params: Template variables, applied at every depth.

        Example:
            ```python
            report.nested_list([
                "Infrastructure",
                ["Database", "Cache", ["Redis", "Memcached"]],
                "Application",
            ])
            ```
        """
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
        """Append every DataFrame column and row as a GFM Markdown table.

        The whole frame is written — there is no row or column limit, so slice
        the frame first if it is large. Column names become the header row and
        floats are rounded for display only.

        Args:
            df: The frame to render.
            title: Bold caption placed above the table.
            params: Template variables, applied to the title.
            decimal_places: Digits after the point for float columns.

        Example:
            ```python
            report.table(metrics.head(20), title="Top 20 by revenue", decimal_places=1)
            ```
        """
        return self.append(Table(df, title=title, params=params, decimal_places=decimal_places))

    def csv(
        self,
        df: pl.DataFrame,
        title: str | None = None,
        params: Mapping[str, Any] | None = None,
        decimal_places: int = 2,
        wrap_code: bool = True,
    ) -> MarkdownReport:
        """Append a DataFrame as CSV, optionally inside a fenced code block.

        Useful where a reader is meant to copy the numbers out rather than read
        them in a table.

        Args:
            df: The frame to serialize.
            title: Bold caption placed above the block.
            params: Template variables, applied to the title.
            decimal_places: Digits after the point for float columns.
            wrap_code: True fences the CSV as a ```csv block. False emits it as
                raw document text, which is only valid where the surrounding
                Markdown tolerates it.

        Example:
            ```python
            report.csv(metrics, title="Raw data")
            ```
        """
        if title:
            append_tokens(
                self.document,
                bold_paragraph_tokens(self.parser, render_template(title, params)),
            )

        csv_content = format_dataframe_csv(df, decimal_places=decimal_places)
        content_token = fence_token(csv_content, "csv") if wrap_code else raw_token(csv_content)
        append_tokens(self.document, [content_token])
        return self

    def code_block(
        self,
        code: str,
        language: str = "",
        title: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> MarkdownReport:
        """Append a syntax-highlighted fenced code block.

        Code is fenced, not parsed, so Markdown inside it stays literal.

        Args:
            code: Source text, reproduced as given.
            language: Info string driving highlighting; "" for a plain fence.
            title: Bold caption placed above the block.
            params: Template variables, applied to the code as well as the title.
                Leave it None — the default — when the code contains Jinja-like
                braces of its own, which templating would otherwise substitute.

        Example:
            ```python
            report.code_block("select 1", language="sql", title="Query")
            ```
        """
        return self.append(CodeBlock(code, language=language, title=title, params=params))

    def line_break(self) -> MarkdownReport:
        """Append one additional blank line between document blocks.

        Blocks are already separated by a blank line when rendered; this adds one
        more for extra visual spacing.

        Example:
            ```python
            report.text("Above").line_break().text("Below")
            ```
        """
        append_tokens(self.document, [line_break_token()])
        return self

    def horizontal_rule(self) -> MarkdownReport:
        """Append a thematic break, rendered as `---`.

        Example:
            ```python
            report.horizontal_rule()
            ```
        """
        append_tokens(self.document, [horizontal_rule_token()])
        return self

    def table_of_contents(self) -> MarkdownReport:
        """Append a nested table of contents covering every heading in the report.

        Resolved at `render` time, not now, so it can be placed near the top and
        still list headings appended afterwards. Entries nest by heading level and
        are plain text, not links.

        Example:
            ```python
            report.title("Q3 Review").table_of_contents().heading("Revenue")
            # the contents list includes "Revenue", added after the call
            ```
        """
        return self.append(TableOfContents())

    def render(self) -> str:
        """Serialize the complete report as a Markdown string.

        Resolves deferred blocks and prepends the frontmatter, leaving the report
        itself unchanged — rendering is repeatable, and content can still be
        appended afterwards.

        Returns:
            The rendered document, including a trailing newline.

        Example:
            ```python
            markdown = report.render()
            ```
        """
        document = SyntaxTreeNode(self.document.to_tokens())
        resolved_tokens: list[Token] = []
        for token in document.to_tokens():
            if token.type == DEFERRED_BLOCK_TOKEN_TYPE:
                block = cast(DeferredReportBlock, token.meta["block"])
                resolved_tokens.extend(block_tokens(self.parser, block.__resolve__(document, self)))
            else:
                resolved_tokens.append(token)

        if self.frontmatter_data:
            resolved_tokens.insert(0, frontmatter_token(dict_to_yaml(self.frontmatter_data)))

        return self.parser.render(SyntaxTreeNode(resolved_tokens).to_tokens())

    def save(self, filename: str | Path) -> MarkdownReport:
        """Render the report and write it to a file as UTF-8.

        Overwrites an existing file. The parent directory must already exist.

        Args:
            filename: Destination path.

        Raises:
            OSError: if the path is not writable or its directory is missing.

        Example:
            ```python
            report.save("reports/q3.md")
            ```
        """
        Path(filename).write_text(self.render(), encoding="utf-8")
        return self

    def __str__(self) -> str:
        """Return the rendered Markdown, so `print(report)` shows the document.

        Equivalent to `render`.
        """
        return self.render()
