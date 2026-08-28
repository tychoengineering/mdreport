# API reference

## Report

### *class* MarkdownReport

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

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
  * **data** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Fields to merge, for keys that are not valid identifiers.
  * **\*\*kwargs** ([*Any*](https://docs.python.org/3/library/typing.html#typing.Any)) – Fields to merge, for keys that are.

#### markdown(content, params=None)

Parse and append raw Markdown content.

The escape hatch for Markdown the other methods don’t build: block quotes,
footnotes, images, or a whole section held as a string. Content is parsed,
not inserted verbatim, so it must be valid Markdown; use `raw_token` via
`append` for text that must survive untouched.

* **Parameters:**
  * **content** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Markdown source, treated as a Jinja template when params is given.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables. None leaves the content unrendered, so
    literal braces pass through safely.

#### directive(name, value=None)

Append a smolslides HTML-comment directive.

Directives are HTML comments, so they are invisible to Markdown renderers
that don’t understand them.

* **Parameters:**
  * **name** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Directive name, written with the leading underscore smolslides
    expects (`class` becomes `<!-- _class: ... -->`).
  * **value** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Directive argument, or None for a bare flag directive.

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
  * **text** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Heading text, treated as a Jinja template when params is given.
  * **level** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Heading level, 1 (`#`) through 6 (`######`).
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if level is outside the Markdown heading range.

#### text(content, params=None)

Parse and append one or more Markdown text blocks.

A list appends each entry as its own separate block, which is how to get
distinct paragraphs; a single string containing blank lines parses into
paragraphs too.

* **Parameters:**
  * **content** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* [*list*](https://docs.python.org/3/library/stdtypes.html#list) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *]*) – One Markdown block, or a list of them.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to every block.

#### callout(message, kind=CalloutKind.NOTE, title=None, params=None)

Append a titled block quote drawing attention to content.

* **Parameters:**
  * **message** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Markdown content displayed inside the callout.
  * **kind** ([*CalloutKind*](#mdreport.CalloutKind)) – Semantic category supplying the default title.
  * **title** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Custom title replacing the category name.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables applied to the message and custom title.

#### bullet_list(items, params=None)

Append an unordered list, nesting sublists to any depth.

Items are parsed as inline Markdown, so they can carry emphasis, code, or
links. A sublist is written as a list immediately after the item it hangs
beneath. An empty list appends an empty list block.

* **Parameters:**
  * **items** ([*list*](https://docs.python.org/3/library/stdtypes.html#list) *[**NestedListItem* *]*) – Strings, and lists of items that nest under the preceding string.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied at every depth.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if a sublist has no preceding item to nest beneath.

#### numbered_list(items, params=None)

Append a consecutively numbered list, nesting sublists to any depth.

Numbering is generated from position, starting at 1 at every level — don’t
write numbers into the items themselves. A sublist is written as a list
immediately after the item it hangs beneath.

* **Parameters:**
  * **items** ([*list*](https://docs.python.org/3/library/stdtypes.html#list) *[**NestedListItem* *]*) – Strings, and lists of items that nest under the preceding string.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied at every depth.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if a sublist has no preceding item to nest beneath.

#### table(df, title=None, params=None, decimal_places=2)

Append every DataFrame column and row as a GFM Markdown table.

The whole frame is written — there is no row or column limit, so slice
the frame first if it is large. Column names become the header row and
floats are rounded for display only.

* **Parameters:**
  * **df** (*DataFrame*) – The frame to render.
  * **title** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Bold caption placed above the table.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to the title.
  * **decimal_places** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Digits after the point for float columns.

#### csv(df, title=None, params=None, decimal_places=2, wrap_code=True)

Append a DataFrame as CSV, optionally inside a fenced code block.

Useful where a reader is meant to copy the numbers out rather than read
them in a table.

* **Parameters:**
  * **df** (*DataFrame*) – The frame to serialize.
  * **title** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Bold caption placed above the block.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to the title.
  * **decimal_places** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Digits after the point for float columns.
  * **wrap_code** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – True fences the CSV in a `csv` code block. False emits it as
    raw document text, which is only valid where the surrounding
    Markdown tolerates it.

#### code_block(code, language='', title=None, params=None)

Append a syntax-highlighted fenced code block.

Code is fenced, not parsed, so Markdown inside it stays literal.

* **Parameters:**
  * **code** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Source text, reproduced as given.
  * **language** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Info string driving highlighting; “” for a plain fence.
  * **title** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Bold caption placed above the block.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables, applied to the code as well as the title.
    Leave it None — the default — when the code contains Jinja-like
    braces of its own, which templating would otherwise substitute.

#### figure(source, alt_text, caption=None, params=None, is_embedded=False)

Append an image with an optional numbered caption.

Figures are numbered in document order during `render`.

* **Parameters:**
  * **source** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* [*Path*](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Image path or URL written into the Markdown image destination.
  * **alt_text** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Literal alternative text describing the image.
  * **caption** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Optional inline-Markdown caption.
  * **params** ([*Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* [*Any*](https://docs.python.org/3/library/typing.html#typing.Any) *]*  *|* *None*) – Template variables applied to source, alternative text, and caption.
  * **is_embedded** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – True reads a local raster image into a base64 data URL or
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
  * **start_level** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Shallowest heading level listed. Raise it to skip the
    document title, or a section heading a slide deck repeats.
  * **depth** ([*int*](https://docs.python.org/3/library/functions.html#int)) – How many heading levels to list, counting from `start_level`.
    Lower it to keep the contents short in a deeply nested report.
  * **is_linked** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – False renders entries as plain text, for a renderer whose
    heading anchors cannot be relied on.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if start_level is outside the Markdown heading range, or
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
  [str](https://docs.python.org/3/library/stdtypes.html#str)

#### save(filename)

Render the report and write it to a file as UTF-8.

Overwrites an existing file. The parent directory must already exist.

* **Parameters:**
  **filename** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* [*Path*](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Destination path.
* **Raises:**
  [**OSError**](https://docs.python.org/3/library/exceptions.html#OSError) – if the path is not writable or its directory is missing.

#### \_\_str_\_()

Return the rendered Markdown, so `print(report)` shows the document.

Equivalent to `render`.

## Blocks

### *class* Callout

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

A titled block quote drawing attention to report content.

* **Variables:**
  * **message** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Markdown content displayed inside the callout.
  * **kind** ([*mdreport.callout.CalloutKind*](#mdreport.CalloutKind)) – Semantic category supplying the default title.
  * **title** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Optional title overriding the category name.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables applied to the message and custom title.

#### message *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

#### kind *: [CalloutKind](#mdreport.CalloutKind)* *= 'note'*

#### title *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

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

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

A fenced code block tagged with an optional language.

The block behind `MarkdownReport.code_block`. Construct it directly to hold a
snippet as a value and append it with `report.append(...)` or `report + ...`.

* **Variables:**
  * **code** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Source text, fenced rather than parsed, so Markdown in it stays literal.
  * **language** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Info string driving highlighting; “” for a plain fence.
  * **title** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Bold caption placed above the block.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables, applied to the code as well as the title.
    Leave it None when the code contains Jinja-like braces of its own.

#### code *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

#### language *: [str](https://docs.python.org/3/library/stdtypes.html#str)* *= ''*

#### title *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### \_\_report_\_(report)

Return the fence token, preceded by a bold title when one is set.

#### \_\_init_\_(code, language='', title=None, params=None)

### *class* Figure

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

An image with alternative text and an optional numbered caption.

Figures are numbered in document order during rendering.

* **Variables:**
  * **source** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* [*pathlib.Path*](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Image path or URL written into the Markdown image destination.
  * **alt_text** ([*str*](https://docs.python.org/3/library/stdtypes.html#str)) – Literal alternative text describing the image.
  * **caption** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Optional inline-Markdown caption, prefixed with its figure number.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables applied to source, alternative text, and caption.
  * **is_embedded** ([*bool*](https://docs.python.org/3/library/functions.html#bool)) – True reads a local raster image into a base64 data URL or
    inserts a local SVG as inline markup. False leaves source as a link.

#### source *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [Path](https://docs.python.org/3/library/pathlib.html#pathlib.Path)*

#### alt_text *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

#### caption *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### is_embedded *: [bool](https://docs.python.org/3/library/functions.html#bool)* *= False*

#### \_\_resolve_\_(document, report)

Return the image and its number-aware caption.

#### \_\_init_\_(source, alt_text, caption=None, params=None, is_embedded=False)

### *class* Table

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Every column and row of a DataFrame as a GFM table.

The block behind `MarkdownReport.table`. Construct it directly to hold a
table as a value — to pass it around, reuse it across reports, or append it
with `report + table`.

* **Variables:**
  * **dataframe** (*polars.dataframe.frame.DataFrame*) – The frame to render, in full; slice it first if it is large.
  * **title** ([*str*](https://docs.python.org/3/library/stdtypes.html#str) *|* *None*) – Bold caption placed above the table.
  * **params** ([*collections.abc.Mapping*](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping) *[*[*str*](https://docs.python.org/3/library/stdtypes.html#str) *,* *Any* *]*  *|* *None*) – Template variables, applied to the title.
  * **decimal_places** ([*int*](https://docs.python.org/3/library/functions.html#int)) – Digits after the point for float columns.

#### dataframe *: DataFrame*

#### title *: [str](https://docs.python.org/3/library/stdtypes.html#str) | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### params *: [Mapping](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)[[str](https://docs.python.org/3/library/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)] | [None](https://docs.python.org/3/library/constants.html#None)* *= None*

#### decimal_places *: [int](https://docs.python.org/3/library/functions.html#int)* *= 2*

#### \_\_report_\_(report)

Return the table tokens, preceded by a bold title when one is set.

#### \_\_init_\_(dataframe, title=None, params=None, decimal_places=2)

### *class* TableOfContents

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

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
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if start_level is outside the Markdown heading range, or
      depth is less than one.

#### start_level *: [int](https://docs.python.org/3/library/functions.html#int)* *= 1*

#### depth *: [int](https://docs.python.org/3/library/functions.html#int)* *= 6*

#### is_linked *: [bool](https://docs.python.org/3/library/functions.html#bool)* *= True*

#### \_\_post_init_\_()

Reject a scope that no heading could fall in.

#### *property* end_level *: [int](https://docs.python.org/3/library/functions.html#int)*

Deepest heading level listed, clamped to the Markdown heading range.

#### \_\_resolve_\_(document, report)

Return list tokens mirroring the document’s heading hierarchy.

#### entries(document)

Collect the headings in scope into a hierarchy, in document order.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if a heading node contains no inline token.

#### contents_tokens(entries)

Build nested unordered-list tokens for table-of-contents entries.

#### entry_inline(entry)

Build one entry’s inline content, linked to its heading’s anchor.

#### \_\_init_\_(start_level=1, depth=6, is_linked=True)

### *class* TableOfContentsEntry

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

A heading, the anchor linking to it, and the headings nested beneath it.

#### level *: [int](https://docs.python.org/3/library/functions.html#int)*

#### inline *: Token*

#### slug *: [str](https://docs.python.org/3/library/stdtypes.html#str)*

#### children *: [list](https://docs.python.org/3/library/stdtypes.html#list)[[TableOfContentsEntry](#mdreport.TableOfContentsEntry)]*

#### \_\_init_\_(level, inline, slug, children=<factory>)

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

Bases: [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError)

A figure source cannot be embedded as an image in the report.

## Token builders

### paragraph_tokens(parser, content, , is_hidden=False)

Build a paragraph token pair containing parsed inline Markdown.

### bold_paragraph_tokens(parser, content)

Build a paragraph whose complete inline content is strong text.

### heading_tokens(parser, content, level)

Build a heading at a level from one through six.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if level is outside the Markdown heading range.

### list_tokens(parser, items, , is_ordered)

Build an ordered or unordered list, nesting sublists to any depth.

A list element nests beneath the item that precedes it. Every level carries
the marker chosen by is_ordered, so an ordered list nests ordered sublists.

* **Raises:**
  [**ValueError**](https://docs.python.org/3/library/exceptions.html#ValueError) – if a sublist has no preceding item to nest beneath.

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

Bases: [`object`](https://docs.python.org/3/library/functions.html#object)

Parse and serialize Markdown for one report.

The environment accumulates the link reference definitions collected while
parsing, so a reference defined in one block resolves in a later one.

#### parser *: MarkdownIt*

#### environment *: [dict](https://docs.python.org/3/library/stdtypes.html#dict)[[str](https://docs.python.org/3/library/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]*

#### parse(content)

Parse Markdown text into a block-level token stream.

#### parse_inline(content)

Parse inline Markdown into its container token.

#### render(tokens)

Serialize a token stream as Markdown, leaving the environment intact.

#### \_\_init_\_(parser, environment=<factory>)
