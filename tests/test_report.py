from __future__ import annotations

import csv
import io
from pathlib import Path

import polars as pl
import pytest
import yaml

from mdreport import MarkdownReport
from mdreport.report import dict_to_yaml


def test_report_renders_complete_document_with_deferred_contents() -> None:
    report = (
        MarkdownReport()
        .frontmatter(
            {"metadata": {"authors": ["Ada", "Grace"]}},
            title="Quarterly: Review",
            summary="line one\nline two",
        )
        .title("{{ period }} Report", {"period": "Q3"})
        .table_of_contents()
        .heading("Overview")
        .heading("Details", level=3)
        .text("Prepared for {{ audience }}.", {"audience": "engineering"})
    )

    rendered_report = report.render()

    assert (
        rendered_report
        == """---
metadata:
  authors:
  - Ada
  - Grace
title: 'Quarterly: Review'
summary: 'line one

  line two'
---

# Q3 Report

- [Q3 Report](#q3-report)
  - [Overview](#overview)
    - [Details](#details)

## Overview

### Details

Prepared for engineering.

"""
    )


def test_frontmatter_round_trips_yaml_values() -> None:
    metadata = {
        "boolean-like": "true",
        "numeric-like": "123",
        "empty": "",
        "nothing": None,
        "enabled": True,
        "quoted": 'a "quote" and \\ slash',
        "nested": [{"label": "value: #tag", "lines": ["first\nsecond"]}],
    }

    serialized_metadata = dict_to_yaml(metadata)

    assert yaml.safe_load(serialized_metadata) == metadata


def test_report_preserves_block_order_and_markdown_spacing() -> None:
    report = (
        MarkdownReport()
        .directive("class", "summary")
        .directive("skip")
        .markdown("_{{ label }}_", {"label": "Overview"})
        .text(["First {{ noun }}.", "Second {{ noun }}."], {"noun": "paragraph"})
        .bullet_list(["{{ color }}", "blue"], {"color": "red"})
        .numbered_list(["build", "ship"])
        .nested_list(["parent", ["child", ["grandchild"]], "sibling"])
        .code_block(
            "print('{{ greeting }}')",
            language="python",
            title="{{ kind }}",
            params={"greeting": "hello", "kind": "Example"},
        )
        .line_break()
        .horizontal_rule()
    )

    rendered_report = report.render()

    assert (
        rendered_report
        == """<!-- _class: summary -->

<!-- _skip -->

_Overview_

First paragraph.

Second paragraph.

- red
- blue

1. build
2. ship

- parent
  - child
    - grandchild
- sibling

**Example**

```python
print('hello')
```


---

"""
    )


def test_empty_table_of_contents_leaves_no_placeholder() -> None:
    report = MarkdownReport().table_of_contents().text("No headings yet.")

    rendered_report = report.render()

    assert rendered_report == "No headings yet.\n\n"


def test_table_of_contents_uses_parsed_heading_structure() -> None:
    report = (
        MarkdownReport()
        .table_of_contents()
        .markdown(
            """## First

```markdown
# Not a heading
```

#### Deep
"""
        )
        .heading("Second")
    )

    rendered_report = report.render()

    assert rendered_report.startswith(
        """- [First](#first)
  - [Deep](#deep)
- [Second](#second)

"""
    )
    assert "Not a heading" not in rendered_report.split("```markdown")[0]


@pytest.mark.parametrize("level", [0, 7])
def test_heading_rejects_levels_outside_markdown_range(level: int) -> None:
    report = MarkdownReport()

    with pytest.raises(ValueError, match="Heading level must be between 1 and 6"):
        report.heading("Invalid", level=level)


def test_table_formats_list_and_float_columns_for_markdown() -> None:
    dataframe = pl.DataFrame(
        {
            "name": ["alpha", "beta"],
            "score": [1.234, -0.005],
            "tags": [["red", "blue"], []],
        }
    )
    report = MarkdownReport().table(dataframe, title="Data", decimal_places=1)

    rendered_report = report.render()

    assert (
        rendered_report
        == """**Data**

| name  | score | tags      |
| ----- | ----- | --------- |
| alpha | 1.2   | red, blue |
| beta  | 0.0   |           |

"""
    )


def test_table_includes_all_columns_rows_and_complete_values() -> None:
    long_text = "complete-value-" * 8
    dataframe = pl.DataFrame(
        {
            "row": range(1_001),
            "description": [long_text] * 1_001,
            **{f"column_{index}": [index] * 1_001 for index in range(12)},
        }
    )

    rendered_report = MarkdownReport().table(dataframe).render()
    table_lines = [
        line for line in rendered_report.splitlines() if line.startswith("|")
    ]

    assert len(table_lines) == dataframe.height + 2
    assert "column_11" in table_lines[0]
    assert long_text in rendered_report
    assert "| 1000 " in table_lines[-1]
    assert "…" not in rendered_report


def test_table_preserves_cell_boundaries_for_pipes_and_newlines() -> None:
    dataframe = pl.DataFrame({"value": ["left|right", "line one\nline two"]})

    rendered_report = MarkdownReport().table(dataframe).render()

    assert "left\\|right" in rendered_report
    assert "line one<br>line two" in rendered_report


def test_csv_emits_parseable_rows_with_formatted_dataframe_values() -> None:
    dataframe = pl.DataFrame(
        {
            "name": ["alpha", "beta"],
            "score": [1.234, -0.005],
            "tags": [["red", "blue"], []],
        }
    )
    report = MarkdownReport().csv(dataframe, decimal_places=1, wrap_code=False)

    rendered_report = report.render()
    rows = list(csv.DictReader(io.StringIO(rendered_report)))

    assert rows == [
        {"name": "alpha", "score": "1.2", "tags": "red, blue"},
        {"name": "beta", "score": "0.0", "tags": ""},
    ]


def test_csv_wraps_export_in_titled_markdown_fence() -> None:
    dataframe = pl.DataFrame({"name": ["alpha"], "score": [1.234]})
    report = MarkdownReport().csv(
        dataframe,
        title="{{ kind }} data",
        params={"kind": "Raw"},
    )

    rendered_report = report.render()

    assert (
        rendered_report
        == """**Raw data**

```csv
name,score
alpha,1.23
```

"""
    )


def test_save_writes_the_rendered_report_and_supports_chaining(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "summary.md"
    report_path.parent.mkdir()
    report = MarkdownReport().title("Summary").text("Complete.")

    returned_report = report.save(str(report_path))

    assert returned_report is report
    assert report_path.read_text(encoding="utf-8") == report.render()
