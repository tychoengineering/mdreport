mdreport
========

Build Markdown reports programmatically with a chainable API. Add headings, text, lists, callouts, figures, code blocks,
templates, Polars DataFrames, and SVG diagrams.

Install
-------

.. code-block:: bash

   pip install mdreport

``mdreport`` requires Python 3.12 or later.

Create a report
---------------

.. code-block:: python

   from mdreport import MarkdownReport

   report = (
       MarkdownReport()
       .title("Q3 review")
       .heading("Revenue")
       .text("Revenue grew {{revenue_growth}}%.", params={"revenue_growth": 4})
       .bullet_list(["EMEA grew 6%", "APAC grew 2%"])
   )

   report.save("q3-review.md")

Each method adds content and returns the report. Chain methods when the sequence is clear, or call them one at a time.

Create a diagram and embed it in a report:

.. code-block:: python

   from mdreport import Diagram, DiagramTheme, MarkdownReport, NodeRole, title_node

   diagram = Diagram("Ingest", width=466, height=89, theme=DiagramTheme.LIGHT)
   title_node(diagram, 89, 17, 288, "Source", role=NodeRole.ROOT)

   report = MarkdownReport().title("Ingest")
   report.append(diagram.figure(caption="Source node"))
   report.save("ingest.md")

Read the documentation
----------------------

.. toctree::
   :maxdepth: 2

   markdown
   diagrams
   api-reference
   extensions

LLMs and coding agents
----------------------

LLMs and coding agents can read the documentation in Markdown format:

- `llms.txt <llms.txt>`_ — a linked index of every page.
- `llms-full.txt <llms-full.txt>`_ — the whole documentation as a single Markdown file.
