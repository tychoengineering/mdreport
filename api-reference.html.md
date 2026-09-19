# API reference

## Report

### *class* MarkdownReport

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Build a Markdown document.

Provides a fluent interface for building markdown documents with various content types
including headings, text, tables, lists, code blocks, and more. Supports Jinja2
template rendering for dynamic content generation.

- Method chaining for fluent report building
- Jinja2 template support for dynamic content
- Polars DataFrame integration for tables and CSV exports
- Automatic formatting of numeric data with configurable precision
- Numbered figures and captions
- Portable semantic callouts
- Support for nested lists and various markdown elements
- Export to file or string rendering

Every content method returns the report itself, so calls chain. Content is
held as a Markdown syntax tree rather than as text, so `render` is what
serializes it; a report can be rendered repeatedly and keeps building
afterwards.

#### \_\_init_\_(anchor_style=HeadingAnchorStyle.IMPLICIT)

Create an empty report with its own parser and no frontmatter.

* **Parameters:**
  **anchor_style** ([*HeadingAnchorStyle*](#mdreport.HeadingAnchorStyle)) – How each heading’s anchor is written into the rendered
  document. The default writes nothing and relies on the anchor the
  renderer derives from the heading text, which is what
  `table_of_contents` links to; pass `HeadingAnchorStyle.HTML`
  or `HeadingAnchorStyle.ATTRIBUTE` for a renderer that derives
  none.

#### append(block)

Append a block’s content to this report.

This is the extension point behind `table`, `code_block`, and
`table_of_contents`, and the way to add a block of your own: any object
with a `__report__` method satisfies `ReportBlock`.

A block implementing `__resolve__` (a `DeferredReportBlock`) is stored as
a placeholder and resolved during `render`, once the whole document is
known; every other block contributes its content immediately.

#### copy()

Return an independent report holding the same content and metadata.

Content, frontmatter, and parser state are independent, so appending to
the copy never affects this report. Use it to build several documents
from a shared preamble.

#### \_\_add_\_(block)

Return a copy of this report with a block appended, leaving it unchanged.

#### \_\_iadd_\_(block)

Append a block to this report in place.

#### frontmatter(data=None, \*\*kwargs)

Merge YAML frontmatter fields into the report metadata.

Fields accumulate across calls and later values win, so frontmatter can
be set up front and amended once results are known. The block is emitted
at the top of the document by `render`, in insertion order, and is
omitted entirely when no fields were set.

* **Parameters:**
  * **data** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Fields to merge, for keys that are not valid identifiers.
  * **\*\*kwargs** ([*Any*](https://docs.python.org/3/library/typing.html#typing.Any)) – Fields to merge, for keys that are.

#### markdown(content, params=None)

Parse and append raw Markdown content.

The escape hatch for Markdown the other methods don’t build: block quotes,
footnotes, images, or a whole section held as a string. Content is parsed,
not inserted verbatim, so it must be valid Markdown; use `raw_token` via
`append` for text that must survive untouched.

* **Parameters:**
  * **content** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Markdown source, treated as a Jinja template when params is given.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables. None leaves the content unrendered, so
    literal braces pass through safely.

#### directive(name, value=None)

Append a smolslides HTML-comment directive.

Directives are HTML comments, so they are invisible to Markdown renderers
that don’t understand them.

* **Parameters:**
  * **name** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Directive name, written with the leading underscore smolslides
    expects (`class` becomes `<!-- _class: ... -->`).
  * **value** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Directive argument, or None for a bare flag directive.

#### title(text, params=None)

Append an H1 heading.

Shorthand for `heading(text, level=1)`. Headings added by any method are
what `table_of_contents` later collects.

#### heading(text, level=2, params=None)

Append a heading at a level from one through six.

Inline Markdown in the text is parsed, so a heading can carry emphasis or
a link. Every heading becomes an entry in `table_of_contents`, nested by
its level and linked to the heading’s anchor — headings repeating the same
text are numbered apart, as `findings` and `findings-1`.

* **Parameters:**
  * **text** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Heading text, treated as a Jinja template when params is given.
  * **level** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Heading level, 1 (`#`) through 6 (`######`).
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if level is outside the Markdown heading range.

#### text(content, params=None)

Parse and append one or more Markdown text blocks.

A list appends each entry as its own separate block, which is how to get
distinct paragraphs; a single string containing blank lines parses into
paragraphs too.

* **Parameters:**
  * **content** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *]*) – One Markdown block, or a list of them.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to every block.

#### callout(message, kind=CalloutKind.NOTE, title=None, params=None)

Append a titled block quote drawing attention to content.

* **Parameters:**
  * **message** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Markdown content displayed inside the callout.
  * **kind** ([*CalloutKind*](#mdreport.CalloutKind)) – Semantic category supplying the default title.
  * **title** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Custom title replacing the category name.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables applied to the message and custom title.

#### bullet_list(items, params=None)

Append an unordered list, nesting sublists to any depth.

Items are parsed as inline Markdown, so they can carry emphasis, code, or
links. A sublist is written as a list immediately after the item it hangs
beneath. An empty list appends an empty list block.

* **Parameters:**
  * **items** ([*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *[**NestedListItem* *]*) – Strings, and lists of items that nest under the preceding string.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied at every depth.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if a sublist has no preceding item to nest beneath.

#### numbered_list(items, params=None)

Append a consecutively numbered list, nesting sublists to any depth.

Numbering is generated from position, starting at 1 at every level — don’t
write numbers into the items themselves. A sublist is written as a list
immediately after the item it hangs beneath.

* **Parameters:**
  * **items** ([*list*](https://docs.python.org/3/builtins/stdtypes.html#list) *[**NestedListItem* *]*) – Strings, and lists of items that nest under the preceding string.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied at every depth.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if a sublist has no preceding item to nest beneath.

#### table(df, title=None, params=None, decimal_places=2)

Append every DataFrame column and row as a GFM Markdown table.

The whole frame is written — there is no row or column limit, so slice
the frame first if it is large. Column names become the header row and
floats are rounded for display only.

* **Parameters:**
  * **df** (*DataFrame*) – The frame to render.
  * **title** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Bold caption placed above the table.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to the title.
  * **decimal_places** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Digits after the point for float columns.

#### csv(df, title=None, params=None, decimal_places=2, wrap_code=True)

Append a DataFrame as CSV, optionally inside a fenced code block.

Useful where a reader is meant to copy the numbers out rather than read
them in a table.

* **Parameters:**
  * **df** (*DataFrame*) – The frame to serialize.
  * **title** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Bold caption placed above the block.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to the title.
  * **decimal_places** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Digits after the point for float columns.
  * **wrap_code** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool)) – True fences the CSV in a `csv` code block. False emits it as
    raw document text, which is only valid where the surrounding
    Markdown tolerates it.

#### code_block(code, language='', title=None, params=None)

Append a syntax-highlighted fenced code block.

Code is fenced, not parsed, so Markdown inside it stays literal.

* **Parameters:**
  * **code** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Source text, reproduced as given.
  * **language** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Info string driving highlighting; “” for a plain fence.
  * **title** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Bold caption placed above the block.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to the code as well as the title.
    Leave it None — the default — when the code contains Jinja-like
    braces of its own, which templating would otherwise substitute.

#### figure(source, alt_text, caption=None, params=None, is_embedded=False)

Append an image with an optional numbered caption.

Figures are numbered in document order during `render`.

* **Parameters:**
  * **source** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*Path*](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Image path or URL written into the Markdown image destination.
  * **alt_text** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Literal alternative text describing the image.
  * **caption** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Optional inline-Markdown caption.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables applied to source, alternative text, and caption.
  * **is_embedded** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool)) – True reads a local raster image into a base64 data URL or
    inserts a local SVG as inline markup. False links to source.
* **Raises:**
  [**FigureEmbeddingError**](#mdreport.FigureEmbeddingError) – during rendering, if an embedded source is not
      a supported local image.

#### line_break()

Append one additional blank line between document blocks.

Blocks are already separated by a blank line when rendered; this adds one
more for extra visual spacing.

#### horizontal_rule()

Append a thematic break, rendered as `---`.

#### table_of_contents(start_level=1, depth=6, is_linked=True)

Append a nested table of contents covering the report’s headings.

Resolved at `render` time, not now, so it can be placed near the top and
still list headings appended afterwards. Entries nest by heading level and
link to each heading’s anchor.

* **Parameters:**
  * **start_level** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Shallowest heading level listed. Raise it to skip the
    document title, or a section heading a slide deck repeats.
  * **depth** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – How many heading levels to list, counting from `start_level`.
    Lower it to keep the contents short in a deeply nested report.
  * **is_linked** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool)) – False renders entries as plain text, for a renderer whose
    heading anchors cannot be relied on.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if start_level is outside the Markdown heading range, or
      depth is less than one.

#### render()

Serialize the complete report as a Markdown string.

Resolves deferred blocks, writes heading anchors in the report’s
`anchor_style`, and prepends the frontmatter, leaving the report itself
unchanged — rendering is repeatable, and content can still be appended
afterwards.

* **Returns:**
  The rendered document, including a trailing newline.
* **Return type:**
  [str](https://docs.python.org/3/builtins/stdtypes.html#str)

#### save(filename)

Render the report and write it to a file as UTF-8.

Overwrites an existing file. The parent directory must already exist.

* **Parameters:**
  **filename** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*Path*](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Destination path.
* **Raises:**
  [**OSError**](https://docs.python.org/3/builtins/exceptions.html#OSError) – if the path is not writable or its directory is missing.

#### \_\_str_\_()

Return the rendered Markdown, so `print(report)` shows the document.

Equivalent to `render`.

## Blocks

### *class* Callout

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A titled block quote drawing attention to report content.

* **Variables:**
  * **message** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Markdown content displayed inside the callout.
  * **kind** ([*mdreport.callout.CalloutKind*](#mdreport.CalloutKind)) – Semantic category supplying the default title.
  * **title** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Optional title overriding the category name.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables applied to the message and custom title.

#### message *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

#### kind *: [CalloutKind](#mdreport.CalloutKind)* *= 'note'*

#### title *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### \_\_report_\_(report)

Return a portable block quote containing a bold title and body.

#### \_\_init_\_(message, kind=CalloutKind.NOTE, title=None, params=None)

### *class* CalloutKind

Bases: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)

Portable semantic categories for a report callout.

#### NOTE *= 'note'*

#### TIP *= 'tip'*

#### IMPORTANT *= 'important'*

#### WARNING *= 'warning'*

#### CAUTION *= 'caution'*

#### \_\_new_\_(value)

### *class* CodeBlock

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A fenced code block tagged with an optional language.

The block behind `MarkdownReport.code_block`. Construct it directly to hold a
snippet as a value and append it with `report.append(...)` or `report + ...`.

* **Variables:**
  * **code** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Source text, fenced rather than parsed, so Markdown in it stays literal.
  * **language** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Info string driving highlighting; “” for a plain fence.
  * **title** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Bold caption placed above the block.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables, applied to the code as well as the title.
    Leave it None when the code contains Jinja-like braces of its own.

#### code *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

#### language *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)* *= ''*

#### title *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### \_\_report_\_(report)

Return the fence token, preceded by a bold title when one is set.

#### \_\_init_\_(code, language='', title=None, params=None)

### *class* Figure

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

An image with alternative text and an optional numbered caption.

Figures are numbered in document order during rendering.

* **Variables:**
  * **source** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* [*pathlib.Path*](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Image path or URL written into the Markdown image destination.
  * **alt_text** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Literal alternative text describing the image.
  * **caption** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Optional inline-Markdown caption, prefixed with its figure number.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables applied to source, alternative text, and caption.
  * **is_embedded** ([*bool*](https://docs.python.org/3/builtins/functions.html#bool)) – True reads a local raster image into a base64 data URL or
    inserts a local SVG as inline markup. False leaves source as a link.

#### source *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path)*

#### alt_text *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

#### caption *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### is_embedded *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= False*

#### \_\_resolve_\_(document, report)

Return the image and its number-aware caption.

#### \_\_init_\_(source, alt_text, caption=None, params=None, is_embedded=False)

### *class* Table

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Every column and row of a DataFrame as a GFM table.

The block behind `MarkdownReport.table`. Construct it directly to hold a
table as a value — to pass it around, reuse it across reports, or append it
with `report + table`.

* **Variables:**
  * **dataframe** (*polars.dataframe.frame.DataFrame*) – The frame to render, in full; slice it first if it is large.
  * **title** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *|* *None*) – Bold caption placed above the table.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/builtins/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables, applied to the title.
  * **decimal_places** ([*int*](https://docs.python.org/3/builtins/functions.html#int)) – Digits after the point for float columns.

#### dataframe *: DataFrame*

#### title *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/builtins/constants.html#None)* *= None*

#### decimal_places *: [int](https://docs.python.org/3/builtins/functions.html#int)* *= 2*

#### \_\_report_\_(report)

Return the table tokens, preceded by a bold title when one is set.

#### \_\_init_\_(dataframe, title=None, params=None, decimal_places=2)

### *class* TableOfContents

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A nested list of the report’s headings, linked to their anchors.

The block behind `MarkdownReport.table_of_contents`, and the reference
`DeferredReportBlock`: it is appended as a placeholder and resolved during
`render`, so it lists headings added after it as well as before. Entries
nest by heading level.

Entries link to the anchor a renderer derives from the heading text, which
resolves as-is on GitHub, GitLab, Pandoc, and MkDocs. Where the renderer
generates no anchors, build the report with a `MarkdownReport`
`anchor_style` that writes them into the document.

* **Parameters:**
  * **start_level** – Shallowest heading level listed; headings above it are
    skipped along with the nesting they would have introduced.
  * **depth** – How many heading levels to list, counting from `start_level`.
  * **is_linked** – False renders entries as plain text, for a document whose
    anchors cannot be relied on.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if start_level is outside the Markdown heading range, or
      depth is less than one.

#### start_level *: [int](https://docs.python.org/3/builtins/functions.html#int)* *= 1*

#### depth *: [int](https://docs.python.org/3/builtins/functions.html#int)* *= 6*

#### is_linked *: [bool](https://docs.python.org/3/builtins/functions.html#bool)* *= True*

#### \_\_post_init_\_()

Reject a scope that no heading could fall in.

#### *property* end_level *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Deepest heading level listed, clamped to the Markdown heading range.

#### \_\_resolve_\_(document, report)

Return list tokens mirroring the document’s heading hierarchy.

#### entries(document)

Collect the headings in scope into a hierarchy, in document order.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if a heading node contains no inline token.

#### contents_tokens(entries)

Build nested unordered-list tokens for table-of-contents entries.

#### entry_inline(entry)

Build one entry’s inline content, linked to its heading’s anchor.

#### \_\_init_\_(start_level=1, depth=6, is_linked=True)

### *class* TableOfContentsEntry

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A heading, the anchor linking to it, and the headings nested beneath it.

#### level *: [int](https://docs.python.org/3/builtins/functions.html#int)*

#### inline *: Token*

#### slug *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)*

#### children *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[TableOfContentsEntry](#mdreport.TableOfContentsEntry)]*

#### \_\_init_\_(level, inline, slug, children=<factory>)

## Diagrams

### *class* Diagram

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A themed SVG canvas with escaped content and validated geometry.

Construct one per diagram, place components onto it with the module’s
component functions, then hand it to a report with `figure` or write it
with `save`. Palette keys such as `"ink"` or `"root_fill"` may be used
anywhere a color is accepted; an unknown value is passed through as a
literal CSS color.

Brand a diagram by passing `palette` with only the keys that differ; the
rest fall back to the theme’s own, so partial overrides stay valid:

> Diagram(“Flow”, palette={“root”: “#0e9f6e”, “root_fill”: “#ecfdf5”})

A pair of colors in `background` washes the canvas with a gradient, and
`gradient` defines one for anything drawn on top:

> Diagram(“Flow”, background=(“#fff5e5”, “#eaf7f0”))

#### \_\_init_\_(title, , width=1120, height=692, theme=DiagramTheme.LIGHT, palette=None, font_family="'SF Pro Text', 'SF Pro Icons', -apple-system, BlinkMacSystemFont, system-ui, 'Helvetica Neue', Helvetica, Arial, sans-serif", background=None, borders=None, stroke_width=2)

Open a canvas.

The default size is a golden rectangle; `golden_height` gives the
matching height for any other width. The theme supplies the palette, the
canvas fill, and whether surfaces are bordered; `palette`,
`background`, and `borders` override each of those. A `background`
of None under the light theme leaves the canvas transparent, and a pair
of colors washes it corner to corner as the `canvas` gradient.
`stroke_width` is the border thickness every surface starts from, which
each component can still override.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if title or font_family is blank, the size or stroke
      width is not positive, or a background pair is not two colors.

#### frame(color='line', , width=None, radius=0)

Outline the canvas edge; returns the element.

The outline sits half a stroke inside the viewBox, because a rectangle
drawn on the edge itself loses its outer half to the clip and renders at
half the weight asked for. A frame is an explicit request, so it draws
under a borderless theme too, the way `boundary_frame` does. Call it
last if the frame should sit over content that reaches the edge.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if the width is not positive, the radius is negative, or
      the border is too thick for the canvas to hold.

#### color(color)

Resolve a palette key, or pass a literal CSS color through.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if the resolved color is blank.

#### gradient(name, start, end, , x1=0, y1=0, x2=1, y2=1)

Define a two-stop linear gradient; returns the paint to fill or stroke with.

The returned `url(#name)` is accepted anywhere a color is, so one
gradient can fill a node, stroke its border, or do both. `start` and
`end` resolve through the palette, which keeps a gradient built from
role keys correct under every theme. The axis runs in bounding-box
fractions, so the gradient spans whatever element uses it: the default
runs corner to corner, `x2=1, y2=0` runs left to right.

SVG resolves a paint by id, not by document order, so a gradient defined
after the element that references it still applies. That is the way to
give the canvas a gradient on an axis of your own: construct with
`background="url(#hero)"`, then define `hero` here.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if the name is not a valid unique SVG id, an axis point
      is not finite, or a color resolves to blank.

#### append(element)

Append a custom element when the drawing methods are insufficient.

#### rect(x, y, width, height, , fill='panel', stroke='line', radius=13, stroke_width=None)

Append a rounded rectangle; the stroke is dropped in borderless themes.

A stroke width of None takes the diagram’s own.

#### line(x1, y1, x2, y2, , color='ink', width=2, arrow=False, dashed=False)

Append a straight line; solid means the normal path, dashed a conditional one.

#### path(points, , color='ink', width=2, arrow=False, dashed=False)

Append a polyline through at least two validated points.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if fewer than two points are given, or a coordinate is not finite.

#### text(x, y, lines, , size=21, color='ink', weight=500, anchor=TextAnchor.MIDDLE, line_height=1.618033988749895)

Append single- or multi-line text at a baseline; y is the first baseline.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if anchor is not a TextAnchor, or lines is empty.

#### rich_line(x, y, fragments, , size=18, weight=600, anchor=TextAnchor.MIDDLE)

Append one line of text whose (fragment, color) pairs are colored separately.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if fragments is empty or anchor is not a TextAnchor.

#### circle(x, y, radius, color='ink')

Append a filled circle.

#### anchor(anchor)

Resolve a text anchor.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if anchor does not name a TextAnchor member.

#### to_string()

Serialize deterministic, indented SVG with a trailing newline.

#### data_url()

Returns the diagram as a base64 `data:image/svg+xml` URL.

#### save(path)

Create the destination directory and write the SVG as UTF-8.

#### figure(alt_text=None, , caption=None)

Returns a report figure embedding this diagram, defaulting its alternative text to the title.

### *class* DiagramTheme

Bases: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)

Visual presets that keep identical component geometry and hierarchy.

LIGHT draws bordered, tinted surfaces on a transparent canvas. DARK draws
borderless gray surfaces and white text on a black canvas.

#### LIGHT *= 'light'*

#### DARK *= 'dark'*

#### \_\_new_\_(value)

### *class* NodeRole

Bases: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)

Semantic role of a node, resolved to a palette stroke and fill pair.

A role names the position in the flow, not a color, so the same diagram
reads correctly under every theme. `ROOT` is where data enters, `PARENT`
is work done on it, and `LEAF` is what comes out.

#### ROOT *= 'root'*

#### PARENT *= 'parent'*

#### LEAF *= 'leaf'*

#### \_\_new_\_(value)

### *class* PortSide

Bases: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)

Named attachment edges for a rectangular node.

#### LEFT *= 'left'*

#### RIGHT *= 'right'*

#### TOP *= 'top'*

#### BOTTOM *= 'bottom'*

#### \_\_new_\_(value)

### *class* TextAnchor

Bases: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)

Valid SVG horizontal text anchors.

#### START *= 'start'*

#### MIDDLE *= 'middle'*

#### END *= 'end'*

#### \_\_new_\_(value)

### *class* LucideIcon

Bases: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)

Convenient names; the loader also accepts any pinned-release icon name.

#### BOT *= 'bot'*

#### DATABASE *= 'database'*

#### FILE_CHECK_2 *= 'file-check-2'*

#### MESSAGES_SQUARE *= 'messages-square'*

#### NOTEBOOK_TEXT *= 'notebook-text'*

#### SHARE_2 *= 'share-2'*

#### SHIELD_CHECK *= 'shield-check'*

#### TABLE_2 *= 'table-2'*

#### \_\_new_\_(value)

### theme_palette(theme)

Returns the palette a theme draws with.

### LIGHT_PALETTE *= {'background': '#f5f2ec', 'ink': '#202429', 'leaf': '#087d52', 'leaf_fill': '#eaf7f0', 'line': '#737874', 'muted': '#69706f', 'neutral_fill': '#f8f7f3', 'panel': '#fcfbf8', 'panel_alt': '#f7faf7', 'parent': '#e88700', 'parent_fill': '#fff5e5', 'root': '#1769e0', 'root_fill': '#edf4ff', 'soft_line': '#ded9cf'}*

Colors `DiagramTheme.LIGHT` resolves roles and surfaces against.

Bordered, tinted surfaces and dark ink, tuned to read on a page that is itself light.

### DARK_PALETTE *= {'background': '#000000', 'ink': '#ffffff', 'leaf': '#ffffff', 'leaf_fill': '#2b2b2b', 'line': '#777777', 'muted': '#aaaaaa', 'neutral_fill': '#2b2b2b', 'panel': '#171717', 'panel_alt': '#202020', 'parent': '#ffffff', 'parent_fill': '#2b2b2b', 'root': '#ffffff', 'root_fill': '#2b2b2b', 'soft_line': '#383838'}*

Colors `DiagramTheme.DARK` resolves roles and surfaces against.

Borderless gray surfaces and white ink on black, so roles separate by shape and
position rather than by hue.

### DEFAULT_FONT_FAMILY *= "'SF Pro Text', 'SF Pro Icons', -apple-system, BlinkMacSystemFont, system-ui, 'Helvetica Neue', Helvetica, Arial, sans-serif"*

str(object=’’) -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object._\_str_\_() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to ‘strict’.

## Golden-ratio scale

### golden_split(length)

Divide a length at its golden section; returns the (major, minor) parts.

The parts sum to the rounded length and their ratio is φ, so a panel split
this way reads as two related sizes rather than two arbitrary ones.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if length is not positive.

### golden_height(width)

Returns the height that makes a canvas of this width a golden rectangle.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if width is not positive.

### golden_point(start, length, , from_end=False)

Returns the golden section of a span, the off-center line to place a focus on.

Measured from start by default, which puts the point past the middle; pass
from_end to mirror it and sit the focus high, the way a title band does.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if start is not finite or length is not positive.

### GOLDEN_RATIO *= 1.618033988749895*

Convert a string or number to a floating-point number, if possible.

### FIBONACCI_SPACE *= (3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610)*

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable’s items.

If the argument is a tuple, the return value is the same object.

### TYPE_SCALE *= (13, 15, 18, 21, 25, 29, 34)*

Built-in immutable sequence.

If no argument is given, the constructor returns an empty tuple.
If iterable is specified the tuple is initialized from iterable’s items.

If the argument is a tuple, the return value is the same object.

### TITLE_NODE_HEIGHT *= 55*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### CENTERED_NODE_HEIGHT *= 89*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### ICON_NODE_HEIGHT *= 89*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### INFORMATION_NODE_HEIGHT *= 144*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### PANEL_HEADING_BAND *= 55*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### PANEL_CAPTION_BAND *= 34*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### LANE_HEADER *= 144*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### BORDER_WIDTH *= 2*

int([x]) -> integer
int(x, base=10) -> integer

Convert a number or string to an integer, or return 0 if no arguments
are given.  If x is a number, return x._\_int_\_().  For floating-point
numbers, this truncates towards zero.

If x is not a number or if base is given, then x must be a string,
bytes, or bytearray instance representing an integer literal in the
given base.  The literal can be preceded by ‘+’ or ‘-’ and be surrounded
by whitespace.  The base defaults to 10.  Valid bases are 0 and 2-36.
Base 0 means to interpret the base from the string as an integer literal.
>>> int(‘0b100’, base=0)
4

### CANVAS_GRADIENT *= 'canvas'*

str(object=’’) -> str
str(bytes_or_buffer[, encoding[, errors]]) -> str

Create a new string object from the given object. If encoding or
errors is specified, then the object must expose a data buffer
that will be decoded using the given encoding and error handler.
Otherwise, returns the result of object._\_str_\_() (if defined)
or repr(object).
encoding defaults to sys.getdefaultencoding().
errors defaults to ‘strict’.

## Diagram components

### title_node(diagram, x, y, width, title, , role, fill=None, stroke=None, stroke_width=None)

A compact 55-unit node for a short name with no supporting copy.

### centered_node(diagram, x, y, width, title, description, , role, fill=None, stroke=None, stroke_width=None)

An 89-unit node with a title and one short, subordinate description.

### information_node(diagram, x, y, width, eyebrow, title, description, , role, fill=None, stroke=None, stroke_width=None)

Left-align a category, title, and explicit description lines; returns the height.

The tall card of the set: 144 units for one description line, 26 more for
each line after it, with its copy inset 34 units from the left edge.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if description has no lines.

### icon_node(diagram, x, y, width, title, description, , icon, role, fill=None, stroke=None, stroke_width=None, icon_accent=None, accent_parts=(), icon_gradient=None, icon_id=None, icon_cache_dir=PosixPath('/Users/asif/.cache/mdreport/icons/lucide'))

An 89-unit node with left-aligned copy and a decorative right-side icon.

Reserves 34 units for the icon, a 21-unit text/icon gap, and 21-unit outer
padding. Copy must fit the remaining width (width - 97); nothing wraps.

The icon is drawn in the node’s stroke color. A Lucide stroke has to be a
flat hex color, so a border carrying a gradient leaves the icon on the
role’s own color; `icon_gradient` is how an icon takes one.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if width is under 144 units, or the icon cannot be resolved.

### decision_node(diagram, x, y, width, height, label)

Center a short condition in a diamond; branch labels belong to the connectors.

### list_node(diagram, x, y, width, title, rows)

A compact field list with a header divider and equal-height rows; returns the height.

The header band is 55 units, each row is 21, and the list closes with a
13-unit foot, so the height is 68 plus 21 per row.

### repeated_stack(diagram, x, y, width, title, count)

Two offset silhouettes imply repetition; only the front layer carries text.

The front layer is 89 units tall at the given position, and the stack behind
it reaches 13 units further right and down.

### box_label(diagram, x, y, width, height, lines, , fill='neutral_fill', stroke='line', stroke_width=None, color='ink', size=21, weight=600)

Draw centered text inside a rounded rectangle.

Lines are set on the φ leading every stacked label uses, so a box has to be
tall enough to hold `size + (rows - 1) * size * φ` and still clear its own
corner. These are line-box metrics, not measured ink extents, so glyph
bounds still need visual verification in the target font.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if lines is empty, or the stack leaves under 13 units of
      padding above and below.

### group_panel(diagram, x, y, width, height, title, caption=None)

Frame a group with a top-left heading and a muted bottom-left caption.

Reserve PANEL_HEADING_BAND (55) units above the children and
PANEL_CAPTION_BAND (34) below them for the furniture.

### swimlane(diagram, x, y, width, height, title)

A lane uses a fixed LANE_HEADER (144) column to identify an actor or execution owner.

### boundary_frame(diagram, x, y, width, height, title)

A labeled ownership boundary keeps an explicit outline even in borderless themes.

### node_port(x, y, width, height, side)

Derive a connector attachment point from node bounds.

### node_paint(role, fill, stroke)

Returns the (stroke, fill) a node draws with, after either override replaces its role key.

An override is any color the diagram accepts, including the `url(#name)`
a gradient returns, so a node can carry a gradient and keep its role.

### junction(diagram, x, y)

A filled dot denotes a connected split or merge, never a plain crossing.

### labeled_connector(diagram, start, end, label, , dashed=False)

Label a horizontal arrow with a consistent clearance above its centerline.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if the connector is not horizontal.

### annotation_callout(diagram, x, y, lines, target)

Muted explanatory copy uses a leader line with no directional arrowhead.

### legend_header(diagram, x, y, width, , title='Legend')

Draw the mandatory separator and optional heading; returns the key centerline.

Place the rule at least 21 units below the preceding content and align its
ends with the legend’s content column. The rule stays even without a heading.

### color_key(diagram, x, y, label, role)

Place a color swatch and its left-aligned label on a shared centerline.

### arrow_key(diagram, x, y, label, , dashed=False)

Show the actual connector treatment beside its meaning.

### centered_text_stack(diagram, x, y, height, rows, , anchor, gap=None)

Center a complete text stack in a box using equal top and bottom line-box space.

Each row carries text, size, weight, and color. A gap of None gives each row
its own size over φ, which puts the advance to the next row at one φ step of
that row’s size, the same leading LINE_HEIGHT gives a wrapped label. Pass a
number to set one gap for every row instead. The 0.35-em baseline offset
matches box_label. These are line-box metrics, not measured ink extents, so
glyph bounds still need visual verification in the target font.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if rows is empty, the gap is negative, or the stack leaves
      under 13 units of padding.

### svg_element(tag, \*children, text=None, \*\*attributes)

Build an SVG element; underscores in attribute names become hyphens.

Attributes whose value is None are omitted. Text and attribute values are
escaped by the serializer, so caller content is never interpreted as markup.

### lucide_icon_element(name, , primary='#ffffff', accent=None, accent_parts=(), gradient=None, element_id=None, size=34, x=0, y=0, cache_dir=PosixPath('/Users/asif/.cache/mdreport/icons/lucide'))

Fetch a pinned Lucide icon and return safe, editable SVG geometry.

Cache hits work offline. A cache miss fetches the icon and the upstream
LICENSE from jsDelivr’s pinned lucide-static package with a 15-second
timeout; no caller-provided URL is ever requested. Duo color uses zero-based
geometry indices; a gradient colors every stroke and needs an element_id
unique within the containing document. Colors are #RGB or #RRGGBB.

* **Raises:**
  * [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if the name, colors, indices, or fetched geometry are invalid.
  * [**OSError**](https://docs.python.org/3/builtins/exceptions.html#OSError) – if the icon is not cached and cannot be fetched.

## Heading anchors

### *class* HeadingAnchorStyle

Bases: [`StrEnum`](https://docs.python.org/3/library/enum.html#enum.StrEnum)

How a heading’s anchor is written into the rendered Markdown.

`IMPLICIT` writes nothing and relies on the anchor the renderer derives
from the heading text — what GitHub, GitLab, Pandoc, MkDocs, and Docusaurus
all do, and what `slugify` reproduces. `HTML` prefixes the heading with
an `<a id="...">` element, for renderers that generate no anchors of their
own. `ATTRIBUTE` appends the `{#slug}` attribute Pandoc, kramdown, and
python-markdown’s `attr_list` understand; anything else renders it as
visible text.

#### IMPLICIT *= 'implicit'*

#### HTML *= 'html'*

#### ATTRIBUTE *= 'attribute'*

#### \_\_new_\_(value)

### slugify(text)

Return the anchor slug a heading of this text is linked by.

Follows the GitHub algorithm — case folded, punctuation dropped, spaces
turned into hyphens — so a link to the slug resolves on every renderer that
derives heading anchors the same way, with nothing written into the
document. Text that slugifies to nothing yields `section`.

## Extension protocols

### *class* ReportBlock

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

A self-contained unit of report content.

#### \_\_report_\_(report)

Return this block’s content, as Markdown text or as tokens.

The report is passed for its `parser`, which the token builders in
`markdown_tokens` (`paragraph_tokens`, `table_tokens`, `list_tokens`)
take. Implementations must not append to it.

#### \_\_init_\_(\*args, \*\*kwargs)

### *class* DeferredReportBlock

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Report content whose value depends on the completed document.

A deferred block is appended as a placeholder and resolved once, at render
time, against the document as it finally stands. Use it for content that
reads the rest of the report — tables of contents, summaries, and figure
numbering.

#### \_\_resolve_\_(document, report)

Return this block’s content for the completed document.

The document excludes deferred placeholders’ own content, so a
deferred block never observes another deferred block’s output.

#### \_\_init_\_(\*args, \*\*kwargs)

### BlockContent *= BlockContent*

Type alias.

Type aliases are created through the type statement:

```default
type Alias = int
```

In this example, Alias and int will be treated equivalently by static
type checkers.

At runtime, Alias is an instance of TypeAliasType. The \_\_name_\_
attribute holds the name of the type alias. The value of the type alias
is stored in the \_\_value_\_ attribute. It is evaluated lazily, so the
value is computed only if the attribute is accessed.

Type aliases can also be generic:

```default
type ListOrSet[T] = list[T] | set[T]
```

In this case, the type parameters of the alias are stored in the
\_\_type_params_\_ attribute.

See PEP 695 for more information.

## Errors

### *class* FigureEmbeddingError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A figure source cannot be embedded as an image in the report.

## Token builders

### paragraph_tokens(parser, content, , is_hidden=False)

Build a paragraph token pair containing parsed inline Markdown.

### bold_paragraph_tokens(parser, content)

Build a paragraph whose complete inline content is strong text.

### heading_tokens(parser, content, level)

Build a heading at a level from one through six.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if level is outside the Markdown heading range.

### list_tokens(parser, items, , is_ordered)

Build an ordered or unordered list, nesting sublists to any depth.

A list element nests beneath the item that precedes it. Every level carries
the marker chosen by is_ordered, so an ordered list nests ordered sublists.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if a sublist has no preceding item to nest beneath.

### list_item_tokens(parser, content)

Build one complete unordered-list item.

### table_tokens(parser, dataframe)

Build a GFM table from every DataFrame column and row.

### table_cell_tokens(parser, content, , is_header)

Build one table header or body cell with inline Markdown.

### fence_token(content, language='')

Build a fenced code block, terminating the content with a newline.

### raw_token(content)

Build content that renders verbatim, bypassing Markdown formatting.

## Template helpers

### render_template(text, params=None)

Render a short Jinja template when parameters are supplied.

### render_template_items(items, params=None)

Render templates across list items, descending into nested sublists.

## DataFrame helpers

### format_dataframe(dataframe, decimal_places)

Normalize list and float columns for report exports.

### format_dataframe_csv(dataframe, decimal_places=2)

Serialize a normalized DataFrame as CSV without its record terminator.

## Parser

### *class* MarkdownParser

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Parse and serialize Markdown for one report.

The environment accumulates the link reference definitions collected while
parsing, so a reference defined in one block resolves in a later one.

#### parser *: MarkdownIt*

#### environment *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]*

#### parse(content)

Parse Markdown text into a block-level token stream.

#### parse_inline(content)

Parse inline Markdown into its container token.

#### render(tokens)

Serialize a token stream as Markdown, leaving the environment intact.

#### \_\_init_\_(parser, environment=<factory>)
