mdreport
========

Build Markdown reports programmatically using a chainable fluent interface. Add headings, text, lists, code blocks,
templates, and Polars DataFrames.

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

Each method adds content and returns the report. You can chain methods or call them one at a time.

Read the documentation
----------------------

.. toctree::
   :maxdepth: 2

   usage
   api-reference
   extensions
