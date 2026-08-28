# mdreport

Build Markdown reports in Python with a chainable API. `mdreport` supports headings, text, nested lists, callouts,
figures, captions, code blocks, YAML frontmatter, tables of contents, Jinja templates, and Polars DataFrames.

```python
from mdreport import CalloutKind, MarkdownReport

report = (
    MarkdownReport()
    .frontmatter(title="Q3 review", author="Data team")
    .directive("class", "report")
    .title("Q3 review")
    .table_of_contents(start_level=2, depth=2)
    .heading("Summary")
    .text("Revenue grew {{growth}}%.", params={"growth": 4})
    .callout("Numbers are provisional.", kind=CalloutKind.WARNING)
    .figure(
        "charts/revenue.png",
        alt_text="Revenue by region",
        caption="Quarterly revenue by region.",
    )
    .bullet_list(["EMEA", ["Enterprise", "Consumer"], "APAC"])
    .numbered_list(["Collect", "Review", "Publish"])
    .table(metrics, title="Revenue by region", decimal_places=1)
    .csv(metrics, title="Copyable data")
    .code_block("select * from revenue", language="sql", title="Source query")
    .line_break()
    .horizontal_rule()
)
report.save("q3-review.md")
print(report)
```

## Installation

```bash
pip install mdreport
```

`mdreport` requires Python 3.12 or later.

## `MarkdownReport` reference

### Create and combine reports

#### `MarkdownReport(anchor_style=HeadingAnchorStyle.IMPLICIT)`

Creates an empty report. The default anchor style relies on the Markdown renderer to create heading anchors. See
[Heading links](#heading-links) for explicit anchor options.

#### `append(block)`

Adds a built-in or custom report block. A regular block is evaluated immediately. A deferred block is evaluated by
`render()` after the document is complete.

```python
from mdreport import CodeBlock

report.append(CodeBlock("print('hello')", language="python"))
```

#### `copy()`

Returns an independent report with the same content, frontmatter, parser state, and anchor style.

#### `report += block` and `report + block`

`+=` appends a block to the current report. `+` returns a copy with the block appended and leaves the original report
unchanged.

### Metadata and text

#### `frontmatter(data=None, **kwargs)`

Merges fields into YAML frontmatter at the top of the rendered document. Calls accumulate fields; later values replace
earlier values. Use a mapping for keys that are not valid Python identifiers.

```python
report.frontmatter(title="Q3 review", author="Data team")
report.frontmatter({"table-of-contents": True})
```

No frontmatter is written when you do not add any fields.

#### `title(text, params=None)`

Adds a level-one heading. It is shorthand for `heading(text, level=1)`.

#### `heading(text, level=2, params=None)`

Adds a heading from level 1 through 6. The text supports inline Markdown and optional Jinja parameters. A level outside
that range raises `ValueError`.

```python
report.heading("Region: {{region}}", level=3, params={"region": "EMEA"})
```

#### `text(content, params=None)`

Adds Markdown text. Pass one string or a list of strings; each list entry becomes a separate block.

```python
report.text("A paragraph with **emphasis**.")
report.text(["First paragraph.", "Second paragraph."])
```

#### `markdown(content, params=None)`

Parses and adds arbitrary Markdown. Use it for content such as block quotes, images, links, or a complete section.

```python
report.markdown("> See the [source](https://example.com).")
```

#### `directive(name, value=None)`

Adds a smolslides HTML-comment directive. Other Markdown renderers ignore the comment.

```python
report.directive("class", "title")  # <!-- _class: title -->
report.directive("paginate")        # <!-- _paginate -->
```

#### `callout(message, kind=CalloutKind.NOTE, title=None, params=None)`

Adds a titled block quote. The message supports Markdown. Choose `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, or `CAUTION`,
or pass a custom `title`.

```python
from mdreport import CalloutKind

report.callout(
    "Numbers for **{{ period }}** are provisional.",
    kind=CalloutKind.WARNING,
    params={"period": "Q3"},
)
```

### Lists and spacing

#### `bullet_list(items, params=None)`

Adds an unordered list. List items support inline Markdown and Jinja parameters.

#### `numbered_list(items, params=None)`

Adds an ordered list and generates numbering from 1 at each level.

Both methods support nesting to any depth. Put a list immediately after the item it belongs to:

```python
report.bullet_list(
    [
        "Infrastructure",
        ["Database", "Cache", ["Redis", "Memcached"]],
        "Application",
    ]
)
```

A nested list without a preceding item raises `ValueError`.

#### `line_break()`

Adds one extra blank line. Report blocks already have one blank line between them.

#### `horizontal_rule()`

Adds a thematic break rendered as `---`.

### DataFrames and code

#### `table(df, title=None, params=None, decimal_places=2)`

Adds every row and column of a Polars `DataFrame` as a GitHub-Flavored Markdown table. Float values are rounded for
display, and list columns are joined with commas. Slice a large DataFrame before adding it if you do not want the whole
frame in the report.

```python
report.table(metrics.head(20), title="Top regions", decimal_places=1)
```

#### `csv(df, title=None, params=None, decimal_places=2, wrap_code=True)`

Adds a Polars `DataFrame` as CSV. The default wraps it in a fenced `csv` code block so readers can copy it safely. Set
`wrap_code=False` to add the CSV as raw text.

#### `code_block(code, language="", title=None, params=None)`

Adds a fenced code block. `language` supplies the syntax-highlighting info string. When you pass `params`, Jinja
templating applies to both the code and title.

```python
report.code_block("select 1", language="sql", title="Health check")
```

Leave `params` as `None` when code contains Jinja-like braces that must remain literal.

### Figures and captions

#### `figure(source, alt_text, caption=None, params=None, is_embedded=False)`

Adds a figure numbered in document order. The alternative text is literal, while the optional caption supports inline
Markdown and Jinja parameters.

```python
report.figure(
    "charts/revenue.png",
    alt_text="Revenue by region",
    caption="Quarterly **revenue** by region.",
)
```

The default leaves the source as a path or URL. With `is_embedded=True`, a local raster image becomes a base64 data URL
and a local SVG is copied into the document as inline markup. Embedding does not fetch remote URLs. Only embed trusted
SVG files because their markup is preserved; some hosted Markdown viewers also disallow image data URLs.

### Table of contents

#### `table_of_contents(start_level=1, depth=6, is_linked=True)`

Adds a nested list of headings at that position. The list is deferred until `render()`, so it includes headings added
after the method call.

- `start_level` is the shallowest heading level to include. Use `2` to omit a level-one title.
- `depth` is the number of levels to include, counting from `start_level`.
- `is_linked=False` writes plain text instead of links.

```python
report = (
    MarkdownReport()
    .title("Q3 review")
    .table_of_contents(start_level=2, depth=2)
    .heading("Revenue")
    .heading("By region", level=3)
)
```

### Render and save

#### `render()`

Returns the complete Markdown document with a trailing newline. It resolves deferred blocks, adds the configured
heading anchors, and prepends frontmatter. It does not change the report.

#### `save(filename)`

Renders the report and writes it as UTF-8. It overwrites an existing file and returns the report. The parent directory
must already exist.

#### `str(report)`

Returns `report.render()`, so `print(report)` prints the Markdown document.

## Templates

Methods with a `params` argument treat their text as a short Jinja template only when you supply the mapping.

```python
report.text(
    "Generated on {{date}} by {{author}}.",
    params={"date": "2026-08-28", "author": "Data team"},
)
```

Template values work in headings, text, Markdown, list items at every nesting level, callouts, figures, code blocks, and
titles for tables and CSV. If `params` is `None`, braces pass through unchanged.

## Heading links

By default, `HeadingAnchorStyle.IMPLICIT` writes ordinary headings and links the table of contents to anchors that
GitHub, GitLab, Pandoc, MkDocs, and similar renderers derive from the heading text. Repeated headings receive numbered
anchors such as `#findings` and `#findings-1`.

Use an explicit style when your renderer does not generate anchors:

```python
from mdreport import HeadingAnchorStyle, MarkdownReport, slugify

html_report = MarkdownReport(anchor_style=HeadingAnchorStyle.HTML)
# Renders: ## <a id="revenue"></a>Revenue

attribute_report = MarkdownReport(anchor_style=HeadingAnchorStyle.ATTRIBUTE)
# Renders: ## Revenue {#revenue}

report.markdown(f"Back to [revenue](#{slugify('Revenue')}).")
```

`HeadingAnchorStyle.ATTRIBUTE` works with Pandoc, kramdown, and Python-Markdown's `attr_list` extension. Renderers that
do not support heading attributes display `{#revenue}` as text.

## Built-in blocks

The fluent methods use reusable block values internally. You can construct these values directly and pass them to
`append`, `+=`, or `+`.

| Block             | Purpose                                       |
| ----------------- | --------------------------------------------- |
| `Callout`         | A titled, semantic block quote.               |
| `CodeBlock`       | A fenced code block with an optional caption. |
| `Figure`          | A numbered image with an optional caption.    |
| `Table`           | A complete Polars DataFrame as a GFM table.   |
| `TableOfContents` | A deferred, nested heading list.              |

`TableOfContentsEntry` is the data record returned by `TableOfContents.entries()`. It contains `level`, the heading's
inline token, its `slug`, and its child entries. `TableOfContents.end_level` returns the deepest included heading level,
clamped to level 6.

## Custom blocks

A regular block is any object with a `__report__` method. It can return Markdown text, one `markdown_it.token.Token`, or
a sequence of tokens. You do not need to inherit from `ReportBlock` or register the class.

```python
from dataclasses import dataclass

from mdreport import BlockContent, MarkdownReport


@dataclass(frozen=True)
class Aside:
    content: str

    def __report__(self, report: MarkdownReport) -> BlockContent:
        return f"> {self.content}"


report = MarkdownReport().append(Aside("Numbers are provisional."))
```

Do not modify the report inside `__report__`. Return the block content instead.

### Return tokens

Return Markdown text when you can write the complete block as a string. Return tokens when you need literal output or
want the token builders to handle Markdown edge cases.

```python
from dataclasses import dataclass

from markdown_it.token import Token

from mdreport import MarkdownReport, bold_paragraph_tokens, fence_token


@dataclass(frozen=True)
class Query:
    sql: str
    title: str

    def __report__(self, report: MarkdownReport) -> list[Token]:
        tokens = bold_paragraph_tokens(report.parser, self.title)
        tokens.append(fence_token(self.sql, "sql"))
        return tokens
```

### Read the completed document

A deferred block has a `__resolve__` method instead of `__report__`. The report stores a placeholder and resolves it
during each render, after all content has been added.

```python
from dataclasses import dataclass

from markdown_it.tree import SyntaxTreeNode

from mdreport import BlockContent, MarkdownReport


@dataclass(frozen=True)
class HeadingCount:
    def __resolve__(
        self,
        document: SyntaxTreeNode,
        report: MarkdownReport,
    ) -> BlockContent:
        count = sum(1 for node in document.walk() if node.type == "heading")
        return f"This report has {count} headings."


report = MarkdownReport().append(HeadingCount()).title("Findings").heading("Revenue")
```

The deferred block sees the completed report, but not the output of other deferred blocks. It resolves again every time
you render, so its content stays current as the report grows. `TableOfContents` uses this mechanism.

`ReportBlock` and `DeferredReportBlock` are runtime-checkable protocols for type annotations and `isinstance` checks.
`BlockContent` is the return type shared by both protocols.

## Advanced public API

Most callers only need `MarkdownReport` and the built-in blocks. The package also exports helpers for custom blocks and
low-level integrations.

### Token builders

Functions that accept a `MarkdownParser` parse their text as inline Markdown.

| Function                                                | Result                                          |
| ------------------------------------------------------- | ----------------------------------------------- |
| `paragraph_tokens(parser, content, *, is_hidden=False)` | A paragraph containing parsed inline Markdown.  |
| `bold_paragraph_tokens(parser, content)`                | A paragraph whose complete content is bold.     |
| `heading_tokens(parser, content, level)`                | A level 1–6 heading.                            |
| `list_tokens(parser, items, *, is_ordered)`             | A nested ordered or unordered list.             |
| `list_item_tokens(parser, content)`                     | One complete unordered-list item.               |
| `table_tokens(parser, dataframe)`                       | A complete GFM table.                           |
| `table_cell_tokens(parser, content, *, is_header)`      | One table header or body cell.                  |
| `fence_token(content, language="")`                     | A fenced code block.                            |
| `raw_token(content)`                                    | Verbatim output that bypasses Markdown parsing. |

`NestedListItem` is the recursive item type accepted by `list_tokens`, `bullet_list`, and `numbered_list`.

### Template and DataFrame helpers

| Function                                            | Purpose                                                             |
| --------------------------------------------------- | ------------------------------------------------------------------- |
| `render_template(text, params=None)`                | Renders a Jinja template only when parameters are supplied.         |
| `render_template_items(items, params=None)`         | Renders templates throughout a nested list.                         |
| `format_dataframe(dataframe, decimal_places)`       | Joins string-list columns and rounds float columns for output.      |
| `format_dataframe_csv(dataframe, decimal_places=2)` | Returns a formatted CSV string without its final record terminator. |
| `slugify(text)`                                     | Returns the GitHub-style anchor slug for heading text.              |

### `MarkdownParser`

Each report owns a `MarkdownParser` at `report.parser`. Its reference-definition environment persists across blocks.
The class exposes three methods:

- `parse(content)` returns block-level tokens.
- `parse_inline(content)` returns one inline container token.
- `render(tokens)` serializes a token sequence as Markdown.

Use the report's parser inside custom blocks so their Markdown shares the report's environment.

## License

`mdreport` is available under the [MIT License](LICENSE).
