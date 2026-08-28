# Extensions

Create a block when the report methods do not support the content you need.

## Create a block

A block has a `__report__` method. The method returns Markdown text or Markdown tokens.

```python
from dataclasses import dataclass
from mdreport import BlockContent, MarkdownReport

@dataclass(frozen=True)
class Callout:
    message: str

    def __report__(self, report: MarkdownReport) -> BlockContent:
        return f"> **Note:** {self.message}"

report = MarkdownReport().title("Findings")
report.append(Callout("Numbers are provisional."))
```

You do not need a base class or a registration step. Do not change the report inside `__report__`.

## Add a block

```python
report.append(block)
report += block
new_report = report + block
```

`append` and `+=` change the report. The `+` operator returns a changed copy.

## Return tokens

A report holds its content as a Markdown syntax tree, not as text. The string you return from
`__report__` is parsed into tokens before it joins that tree, so both routes end in the same place.
Return tokens to skip the parse and build the tree yourself.

The token builders assemble the pieces. This block pairs a bold caption with a fenced query:

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

report.append(Query("select count(*) from orders", "Order volume"))
```

````markdown
**Order volume**

```sql
select count(*) from orders
```
````

Three reasons to build tokens instead of a string:

- **The builders get the format's edge cases right.** `fence_token` widens the fence when the code
  contains backticks. `table_tokens` escapes the pipes and turns the newlines in a DataFrame cell
  into `<br>`. Written as a string, both corrupt the document instead.
- **`raw_token` bypasses Markdown.** Its content reaches the file untouched. No string can do this,
  because a string is always parsed.
- **A `text` token stays literal.** The builders that take `report.parser` parse their argument as
  inline Markdown, so a caption of `Top _accounts_` comes out as emphasis. Put the value in a
  `Token("text", "", 0, content=value)` when it has to survive as data, and the renderer escapes it
  on the way out.

A Markdown string is the better choice when you write the whole block yourself, as `Callout` does
above. Reach for tokens when your data decides the content.

The [API reference](api-reference.rst) lists all token builders.

## Read the finished document

`__report__` runs the moment you append the block, so it cannot see the rest of the report. Give
your block a `__resolve__` method instead when it summarizes, counts, or links to other content.

`append` stores a placeholder. The report calls `__resolve__` during `render` and puts the returned
content where the placeholder sits.

```python
from dataclasses import dataclass
from markdown_it.tree import SyntaxTreeNode
from mdreport import BlockContent, MarkdownReport

@dataclass(frozen=True)
class HeadingCount:
    def __resolve__(self, document: SyntaxTreeNode, report: MarkdownReport) -> BlockContent:
        headings = sum(1 for node in document.walk() if node.type == "heading")
        return f"This report has {headings} headings."

report = MarkdownReport().append(HeadingCount())
report.title("Findings").heading("Revenue")
print(report.render())
```

The count is 2, even though the block went in before either heading:

```markdown
This report has 2 headings.

# Findings

## Revenue
```

`document` is the report parsed into a [markdown-it-py](https://markdown-it-py.readthedocs.io)
syntax tree. Walk it to find the nodes you care about. `report` gives you the parser, the same as
in `__report__`.

Two rules follow from resolving at render time:

- A deferred block never sees another deferred block's output, so the order you append them in does
  not change what each one reads.
- `render` resolves the block again every time you call it, so a report that grows between renders
  produces an up-to-date block each time.

`TableOfContents` works this way. It is why you place the contents at the top and still list the
headings you add later.
