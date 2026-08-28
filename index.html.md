# mdreport

Build Markdown reports programmatically using a chainable fluent interface. Add headings, text, lists, code blocks,
templates, and Polars DataFrames.

## Install

```bash
pip install mdreport
```

`mdreport` requires Python 3.12 or later.

## Create a report

```python
from mdreport import MarkdownReport

report = (
    MarkdownReport()
    .title("Q3 review")
    .heading("Revenue")
    .text("Revenue grew {{revenue_growth}}%.", params={"revenue_growth": 4})
    .bullet_list(["EMEA grew 6%", "APAC grew 2%"])
)

report.save("q3-review.md")
```

Each method adds content and returns the report. You can chain methods or call them one at a time.

## Read the documentation

* [Usage examples](usage.html.md)
  * [Add common content](usage.html.md#add-common-content)
  * [Add a callout](usage.html.md#add-a-callout)
  * [Add figures](usage.html.md#add-figures)
  * [Add a DataFrame](usage.html.md#add-a-dataframe)
  * [Add template values](usage.html.md#add-template-values)
  * [Add frontmatter](usage.html.md#add-frontmatter)
  * [Add a table of contents](usage.html.md#add-a-table-of-contents)
  * [Link to headings](usage.html.md#link-to-headings)
  * [Render or save](usage.html.md#render-or-save)
* [API reference](api-reference.html.md)
  * [Report](api-reference.html.md#report)
  * [Blocks](api-reference.html.md#blocks)
  * [Heading anchors](api-reference.html.md#heading-anchors)
  * [Extension protocols](api-reference.html.md#extension-protocols)
  * [Errors](api-reference.html.md#errors)
  * [Token builders](api-reference.html.md#token-builders)
  * [Template helpers](api-reference.html.md#template-helpers)
  * [DataFrame helpers](api-reference.html.md#dataframe-helpers)
  * [Parser](api-reference.html.md#parser)
* [Extensions](extensions.html.md)
  * [Create a block](extensions.html.md#create-a-block)
  * [Add a block](extensions.html.md#add-a-block)
  * [Return tokens](extensions.html.md#return-tokens)
  * [Read the finished document](extensions.html.md#read-the-finished-document)
