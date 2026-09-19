# mdreport

Build Markdown reports programmatically with a chainable API. Add headings, text, lists, callouts, figures, code blocks,
templates, Polars DataFrames, and SVG diagrams.

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

Each method adds content and returns the report. Chain methods when the sequence is clear, or call them one at a time.

Create a diagram and embed it in a report:

```python
from mdreport import Diagram, DiagramTheme, MarkdownReport, NodeRole, title_node

diagram = Diagram("Ingest", width=466, height=89, theme=DiagramTheme.LIGHT)
title_node(diagram, 89, 17, 288, "Source", role=NodeRole.ROOT)

report = MarkdownReport().title("Ingest")
report.append(diagram.figure(caption="Source node"))
report.save("ingest.md")
```

## Read the documentation

* [Markdown](markdown.html.md)
  * [Add common content](markdown.html.md#add-common-content)
  * [Add a callout](markdown.html.md#add-a-callout)
  * [Add figures](markdown.html.md#add-figures)
  * [Add a DataFrame](markdown.html.md#add-a-dataframe)
  * [Add template values](markdown.html.md#add-template-values)
  * [Add frontmatter](markdown.html.md#add-frontmatter)
  * [Add a table of contents](markdown.html.md#add-a-table-of-contents)
  * [Link to headings](markdown.html.md#link-to-headings)
  * [Render or save](markdown.html.md#render-or-save)
* [Diagrams](diagrams.html.md)
  * [Draw one node](diagrams.html.md#draw-one-node)
  * [Embed the diagram](diagrams.html.md#embed-the-diagram)
  * [Join two nodes](diagrams.html.md#join-two-nodes)
  * [Fit the node to the copy](diagrams.html.md#fit-the-node-to-the-copy)
  * [Add a legend](diagrams.html.md#add-a-legend)
  * [Group the flow](diagrams.html.md#group-the-flow)
  * [Branch on a condition](diagrams.html.md#branch-on-a-condition)
  * [Show a record and annotate it](diagrams.html.md#show-a-record-and-annotate-it)
  * [Divide work into lanes](diagrams.html.md#divide-work-into-lanes)
  * [Name a node with an icon](diagrams.html.md#name-a-node-with-an-icon)
  * [Choose a theme](diagrams.html.md#choose-a-theme)
  * [Palette keys](diagrams.html.md#palette-keys)
  * [Brand the palette](diagrams.html.md#brand-the-palette)
  * [Adjust border widths](diagrams.html.md#adjust-border-widths)
  * [Use gradients](diagrams.html.md#use-gradients)
  * [Frame the canvas](diagrams.html.md#frame-the-canvas)
  * [Draw a shape the library does not have](diagrams.html.md#draw-a-shape-the-library-does-not-have)
  * [Save or serialize](diagrams.html.md#save-or-serialize)
  * [The scale](diagrams.html.md#the-scale)
  * [Component sizes](diagrams.html.md#component-sizes)
* [API reference](api-reference.html.md)
  * [Report](api-reference.html.md#report)
  * [Blocks](api-reference.html.md#blocks)
  * [Diagrams](api-reference.html.md#diagrams)
  * [Golden-ratio scale](api-reference.html.md#golden-ratio-scale)
  * [Diagram components](api-reference.html.md#diagram-components)
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

## LLMs and coding agents

LLMs and coding agents can read the documentation in Markdown format:

- [llms.txt](llms.txt) — a linked index of every page.
- [llms-full.txt](llms-full.txt) — the whole documentation as a single Markdown file.
