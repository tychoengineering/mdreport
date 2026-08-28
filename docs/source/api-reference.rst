API reference
=============

Report
------

.. autoclass:: mdreport.MarkdownReport
   :members:
   :undoc-members:
   :special-members: __str__, __add__, __iadd__

Blocks
------

.. autoclass:: mdreport.CodeBlock
   :members:

.. autoclass:: mdreport.Table
   :members:

.. autoclass:: mdreport.TableOfContents
   :members:

.. autoclass:: mdreport.TableOfContentsEntry
   :members:

Heading anchors
---------------

.. autoclass:: mdreport.HeadingAnchorStyle
   :members:

.. autofunction:: mdreport.slugify

Extension protocols
-------------------

.. autoclass:: mdreport.ReportBlock
   :members:
   :special-members: __report__

.. autoclass:: mdreport.DeferredReportBlock
   :members:
   :special-members: __resolve__

.. autodata:: mdreport.report_block.BlockContent

Token builders
--------------

.. autofunction:: mdreport.paragraph_tokens

.. autofunction:: mdreport.bold_paragraph_tokens

.. autofunction:: mdreport.heading_tokens

.. autofunction:: mdreport.list_tokens

.. autofunction:: mdreport.list_item_tokens

.. autofunction:: mdreport.table_tokens

.. autofunction:: mdreport.table_cell_tokens

.. autofunction:: mdreport.fence_token

.. autofunction:: mdreport.raw_token

Template helpers
----------------

.. autofunction:: mdreport.render_template

.. autofunction:: mdreport.render_template_items

DataFrame helpers
-----------------

.. autofunction:: mdreport.format_dataframe

.. autofunction:: mdreport.format_dataframe_csv

Parser
------

.. autoclass:: mdreport.MarkdownParser
   :members:
