from __future__ import annotations

from dataclasses import dataclass

import polars as pl
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

from mdreport import (
    BlockContent,
    CodeBlock,
    DeferredReportBlock,
    MarkdownReport,
    ReportBlock,
    Table,
    TableOfContents,
)


@dataclass(frozen=True)
class Callout:
    """A block returning Markdown text, the simplest form a plugin can take."""

    message: str

    def __report__(self, report: MarkdownReport) -> BlockContent:
        return f"> **Note:** {self.message}"


@dataclass(frozen=True)
class Mermaid:
    """A block returning tokens rather than text."""

    source: str

    def __report__(self, report: MarkdownReport) -> BlockContent:
        return Token(
            "fence", "code", 0, content=f"{self.source}\n", markup="```", info="mermaid", block=True
        )


@dataclass(frozen=True)
class HeadingCount:
    """A deferred block that reads the completed document."""

    def __resolve__(self, document: SyntaxTreeNode, report: MarkdownReport) -> BlockContent:
        headings = sum(1 for node in document.walk() if node.type == "heading")
        return f"This report has {headings} headings."


def test_builtin_blocks_satisfy_the_block_protocols() -> None:
    assert isinstance(Table(pl.DataFrame({"a": [1]})), ReportBlock)
    assert isinstance(CodeBlock("print(1)"), ReportBlock)
    assert isinstance(TableOfContents(), DeferredReportBlock)
    assert not isinstance(Callout("hi"), DeferredReportBlock)


def test_append_accepts_markdown_text_and_token_blocks() -> None:
    report = (
        MarkdownReport()
        .heading("Findings")
        .append(Callout("latency regressed"))
        .append(Mermaid("flowchart TD\n    a --> b"))
    )

    assert (
        report.render()
        == """## Findings

> **Note:** latency regressed

```mermaid
flowchart TD
    a --> b
```

"""
    )


def test_in_place_addition_appends_and_returns_the_same_report() -> None:
    report = MarkdownReport().title("Summary")
    original = report

    report += Callout("first")
    report += Callout("second")

    assert report is original
    assert report.render() == "# Summary\n\n> **Note:** first\n\n> **Note:** second\n\n"


def test_addition_returns_a_copy_leaving_the_original_unchanged() -> None:
    base = MarkdownReport().frontmatter(title="Base").title("Summary")

    combined = base + Callout("only in the copy")

    assert combined is not base
    assert "only in the copy" in combined.render()
    assert "only in the copy" not in base.render()
    assert combined.render().startswith("---\ntitle: Base\n---")


def test_copies_do_not_share_appended_content() -> None:
    base = MarkdownReport().title("Summary")

    duplicate = base.copy()
    duplicate.append(Callout("copy only"))
    base.append(Callout("base only"))

    assert "copy only" not in base.render()
    assert "base only" not in duplicate.render()


def test_deferred_blocks_resolve_against_the_completed_document() -> None:
    report = (
        MarkdownReport()
        .append(HeadingCount())
        .title("Summary")
        .heading("Details")
    )

    assert report.render() == "This report has 2 headings.\n\n# Summary\n\n## Details\n\n"


def test_deferred_blocks_resolve_independently_at_each_position() -> None:
    report = MarkdownReport().append(TableOfContents()).heading("First")
    report += TableOfContents()

    rendered_report = report.render()

    assert rendered_report == "- First\n\n## First\n\n- First\n\n"


def test_deferred_blocks_survive_a_copy() -> None:
    base = MarkdownReport().append(TableOfContents())

    combined = base + Callout("body")
    combined.heading("Later")

    assert combined.render().startswith("- Later\n")


def test_table_block_matches_the_table_method() -> None:
    dataframe = pl.DataFrame({"name": ["alpha"], "score": [1.234]})

    from_block = MarkdownReport().append(Table(dataframe, title="Data", decimal_places=1)).render()
    from_method = MarkdownReport().table(dataframe, title="Data", decimal_places=1).render()

    assert from_block == from_method
