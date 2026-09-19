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

.. autoclass:: mdreport.Callout
   :members:

.. autoclass:: mdreport.CalloutKind
   :members:

.. autoclass:: mdreport.CodeBlock
   :members:

.. autoclass:: mdreport.Figure
   :members:

.. autoclass:: mdreport.Table
   :members:

.. autoclass:: mdreport.TableOfContents
   :members:

.. autoclass:: mdreport.TableOfContentsEntry
   :members:

Diagrams
--------

.. autoclass:: mdreport.Diagram
   :members:

.. autoclass:: mdreport.DiagramTheme
   :members:

.. autoclass:: mdreport.NodeRole
   :members:

.. autoclass:: mdreport.PortSide
   :members:

.. autoclass:: mdreport.TextAnchor
   :members:

.. autoclass:: mdreport.LucideIcon
   :members:

.. autofunction:: mdreport.theme_palette

.. autodata:: mdreport.LIGHT_PALETTE

.. autodata:: mdreport.DARK_PALETTE

.. autodata:: mdreport.DEFAULT_FONT_FAMILY

Golden-ratio scale
------------------

.. autofunction:: mdreport.golden_split

.. autofunction:: mdreport.golden_height

.. autofunction:: mdreport.golden_point

.. autodata:: mdreport.GOLDEN_RATIO

.. autodata:: mdreport.FIBONACCI_SPACE

.. autodata:: mdreport.TYPE_SCALE

.. autodata:: mdreport.TITLE_NODE_HEIGHT

.. autodata:: mdreport.CENTERED_NODE_HEIGHT

.. autodata:: mdreport.ICON_NODE_HEIGHT

.. autodata:: mdreport.INFORMATION_NODE_HEIGHT

.. autodata:: mdreport.PANEL_HEADING_BAND

.. autodata:: mdreport.PANEL_CAPTION_BAND

.. autodata:: mdreport.LANE_HEADER

.. autodata:: mdreport.BORDER_WIDTH

.. autodata:: mdreport.CANVAS_GRADIENT

Diagram components
------------------

.. autofunction:: mdreport.title_node

.. autofunction:: mdreport.centered_node

.. autofunction:: mdreport.information_node

.. autofunction:: mdreport.icon_node

.. autofunction:: mdreport.decision_node

.. autofunction:: mdreport.list_node

.. autofunction:: mdreport.repeated_stack

.. autofunction:: mdreport.box_label

.. autofunction:: mdreport.group_panel

.. autofunction:: mdreport.swimlane

.. autofunction:: mdreport.boundary_frame

.. autofunction:: mdreport.node_port

.. autofunction:: mdreport.node_paint

.. autofunction:: mdreport.junction

.. autofunction:: mdreport.labeled_connector

.. autofunction:: mdreport.annotation_callout

.. autofunction:: mdreport.legend_header

.. autofunction:: mdreport.color_key

.. autofunction:: mdreport.arrow_key

.. autofunction:: mdreport.centered_text_stack

.. autofunction:: mdreport.svg_element

.. autofunction:: mdreport.lucide_icon_element

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

Errors
------

.. autoclass:: mdreport.FigureEmbeddingError

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
