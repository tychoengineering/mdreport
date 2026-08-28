# Usage examples

Create a `MarkdownReport`, add content, and then render or save it.

## Add common content

```python
from mdreport import MarkdownReport

report = (
    MarkdownReport()
    .title("Pipeline health")
    .heading("Summary")
    .text("All nightly jobs finished before 06:00.")
    .bullet_list(["12 jobs passed", "0 jobs failed"])
    .numbered_list(["Collect data", "Check data", "Publish report"])
    .code_block("select count(*) from jobs", language="sql")
)
```

Both list methods nest to any depth. Write a sublist as a list immediately after the item it hangs
beneath.

```python
report.bullet_list([
    "Infrastructure",
    ["Database", "Cache", ["Redis", "Memcached"]],
    "Application",
])
```

Use `markdown` for content such as a quote or an image.

```python
report.markdown("> Numbers are provisional.")
```

## Add a callout

Use `callout` for a portable, titled block quote. Its message supports Markdown and template
parameters.

```python
from mdreport import CalloutKind

report.callout(
    "Numbers for **{{ period }}** are provisional.",
    kind=CalloutKind.WARNING,
    params={"period": "Q3"},
)
```

The kinds are `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, and `CAUTION`. Pass `title` to replace the
kind's title.

## Add figures

Use `figure` for a numbered image with alternative text and an optional caption.

```python
report = (
    MarkdownReport()
    .figure(
        "charts/revenue.png",
        alt_text="Revenue by region",
        caption="Quarterly **revenue** by region.",
    )
)
```

Captions receive `Figure 1`, `Figure 2`, and so on in document order during `render`.

By default, the image remains linked to its path or URL. Set `is_embedded=True` to make a local
image part of the Markdown document:

```python
report.figure(
    "charts/revenue.png",
    alt_text="Revenue by region",
    is_embedded=True,
)
```

Raster images become base64 data URLs. SVG files are copied into the document as inline markup,
inside an accessible wrapper carrying the alternative text. Embedding reads local files only; it
does not download a remote URL. Only embed trusted SVG files because their markup is preserved.
Some hosted Markdown viewers disallow data URLs even though the generated document is
self-contained.

## Add a DataFrame

Use `table` for a Markdown table. Use `csv` when readers need to copy the data.

```python
import polars as pl

metrics = pl.DataFrame({
    "region": ["EMEA", "APAC"],
    "revenue": [1234.567, 890.1],
})

report.table(metrics, title="Revenue by region", decimal_places=1)
report.csv(metrics, title="Revenue data")
```

Both methods include every row and column. Slice a large DataFrame before you add it.

## Add template values

Pass a `params` mapping to fill Jinja variables.

```python
report.text(
    "Generated on {{date}} by {{author}}.",
    params={"date": "2026-08-28", "author": "Asif"},
)
```

Templating runs only when you pass `params`. Leave it out when the content contains literal Jinja braces.

## Add frontmatter

Use `frontmatter` to add YAML metadata to the top of the report.

```python
report.frontmatter(title="Q3 review", author="Asif")
report.frontmatter({"table-of-contents": True})
```

Later calls can add fields or replace their values.

## Add a table of contents

Place `table_of_contents` where you want the list. It includes headings that you add later.

```python
report = (
    MarkdownReport()
    .title("Q3 review")
    .table_of_contents()
    .heading("Revenue")
    .heading("Costs")
)
```

Entries link to each heading's anchor, so the list reads as `- [Revenue](#revenue)`. Narrow the
list with `start_level` and `depth` — `table_of_contents(start_level=2, depth=2)` covers level 2
and level 3 headings, skipping the title.

## Link to headings

The anchors the contents link to are the ones a renderer derives from the heading text. GitHub,
GitLab, Pandoc, and MkDocs all generate them, so the links resolve with nothing written into the
document. Two headings with the same text are numbered apart, as `#findings` and `#findings-1`.

For a renderer that generates no anchors, write them into the document:

```python
from mdreport import HeadingAnchorStyle, MarkdownReport, slugify

MarkdownReport(anchor_style=HeadingAnchorStyle.HTML)       # ## <a id="revenue"></a>Revenue
MarkdownReport(anchor_style=HeadingAnchorStyle.ATTRIBUTE)  # ## Revenue {#revenue}

report.markdown(f"Back to [revenue](#{slugify('Revenue')}).")  # link to a heading
```

`ATTRIBUTE` is the syntax Pandoc, kramdown, and python-markdown's `attr_list` understand; anything
else renders it as visible text.

## Render or save

```python
markdown = report.render()
print(report)
report.save("reports/q3.md")
```

`render` returns a string. `save` writes the same Markdown to a UTF-8 file.
