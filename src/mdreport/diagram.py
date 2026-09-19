"""Build deterministic, editable SVG diagrams to embed in a Markdown report.

The module provides the drawing surface (``Diagram``), a themed palette, and a
library of component functions — nodes, panels, connectors, and legend keys —
that share one visual language. Callers write ordinary Python to place
components at explicit coordinates; nothing here lays out, measures text, or
detects overlaps, so the same input always produces byte-identical SVG.

Every size in that visual language comes from one golden-ratio system.
``FIBONACCI_SPACE`` supplies the lengths — consecutive Fibonacci numbers differ
by φ, so any two adjacent steps are in golden proportion and every coordinate
stays a whole number. ``TYPE_SCALE`` supplies the text sizes, three even steps
of φ to the octave, so 13 → 21 → 34 doubles as the Fibonacci run. Component
heights land on the same ladder, and ``golden_split``, ``golden_height``, and
``golden_point`` extend it to whatever the caller places by hand.

Geometry is validated, every string is escaped by the XML serializer, and no
JavaScript or remote asset enters the output. Lucide icon geometry is fetched
once from a pinned release and cached on disk, so later runs are offline.

    diagram = Diagram("Ingest flow", width=890, height=golden_height(890), theme=DiagramTheme.LIGHT)
    title_node(diagram, 55, 182, 288, "Source", role=NodeRole.ROOT)
    centered_node(diagram, 547, 165, 288, "Transform", "Normalize the input", role=NodeRole.PARENT)
    diagram.line(364, 210, 526, 210, arrow=True)
    report.append(diagram.figure("Ingest flow", caption="How records reach the store"))
"""

from __future__ import annotations

import base64
import enum
import math
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from urllib.request import urlopen
from xml.etree import ElementTree

from .figure import Figure

__all__ = [
    "BORDER_WIDTH",
    "CANVAS_GRADIENT",
    "CENTERED_NODE_HEIGHT",
    "DARK_PALETTE",
    "DEFAULT_FONT_FAMILY",
    "DEFAULT_ICON_CACHE_DIR",
    "FIBONACCI_SPACE",
    "GOLDEN_RATIO",
    "ICON_NODE_HEIGHT",
    "INFORMATION_NODE_HEIGHT",
    "LANE_HEADER",
    "LIGHT_PALETTE",
    "PANEL_CAPTION_BAND",
    "PANEL_HEADING_BAND",
    "TITLE_NODE_HEIGHT",
    "TYPE_SCALE",
    "Diagram",
    "DiagramTheme",
    "LucideIcon",
    "NodeRole",
    "PortSide",
    "TextAnchor",
    "annotation_callout",
    "arrow_key",
    "boundary_frame",
    "box_label",
    "centered_node",
    "centered_text_stack",
    "color_key",
    "decision_node",
    "golden_height",
    "golden_point",
    "golden_split",
    "group_panel",
    "icon_node",
    "information_node",
    "junction",
    "labeled_connector",
    "legend_header",
    "list_node",
    "lucide_icon_element",
    "node_paint",
    "node_port",
    "repeated_stack",
    "svg_element",
    "swimlane",
    "theme_palette",
    "title_node",
]

DEFAULT_FONT_FAMILY = "'SF Pro Text', 'SF Pro Icons', -apple-system, BlinkMacSystemFont, system-ui, 'Helvetica Neue', Helvetica, Arial, sans-serif"

GOLDEN_RATIO = (1 + math.sqrt(5)) / 2

# Every length a component draws comes from this ladder. Consecutive Fibonacci
# numbers converge on φ, so two adjacent steps are a golden pair and the numbers
# stay whole — the same reason a typographic grid prefers 8/13/21 to 10/16/26.
FIBONACCI_SPACE = (3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610)

# Three even steps of φ per doubling-and-a-half: each size is the one below it
# times φ ** (1 / 3), so every third step is a full golden jump (13 → 21 → 34)
# and the scale stays coarse enough that two neighbours read as different sizes.
TYPE_SCALE = (13, 15, 18, 21, 25, 29, 34)
TEXT_CAPTION, TEXT_SMALL, TEXT_BODY, TEXT_TITLE, TEXT_LEAD, TEXT_HEADING, TEXT_DISPLAY = TYPE_SCALE

# Leading for every stacked label. φ puts each line's advance back on the
# Fibonacci ladder at the sizes that carry most of the text: 13 stacks on 21,
# 21 on 34, 34 on 55.
LINE_HEIGHT = GOLDEN_RATIO

# Inset, gutter, and corner values, named where the intent is not obvious from
# the number: text sits one INSET from its box edge, and a box is rounded by
# RADIUS, one step below the inset so the corner never swallows the padding.
INSET = 21
CARD_INSET = 34
GAP = 8
RADIUS = 13
PANEL_RADIUS = 21

# Component heights, one ladder rung each, so a row of mixed nodes can be
# centered on a shared line by subtracting halves that stay whole.
TITLE_NODE_HEIGHT = 55
CENTERED_NODE_HEIGHT = 89
ICON_NODE_HEIGHT = 89
INFORMATION_NODE_HEIGHT = 144
INFORMATION_NODE_LINE = round(TEXT_BODY * GOLDEN_RATIO)
STACK_HEIGHT = 89
LIST_NODE_HEADER = 55
LIST_NODE_ROW = 21

# The border every surface draws with until a diagram or a component says otherwise.
BORDER_WIDTH = 2

# The id a background pair is registered under, leaving every other name free.
CANVAS_GRADIENT = "canvas"

# Furniture a container reserves before its children start.
PANEL_HEADING_BAND = 55
PANEL_CAPTION_BAND = 34
LANE_HEADER = 144

LIGHT_PALETTE = {
    "background": "#f5f2ec",
    "panel": "#fcfbf8",
    "panel_alt": "#f7faf7",
    "ink": "#202429",
    "muted": "#69706f",
    "line": "#737874",
    "soft_line": "#ded9cf",
    "root": "#1769e0",
    "root_fill": "#edf4ff",
    "parent": "#e88700",
    "parent_fill": "#fff5e5",
    "leaf": "#087d52",
    "leaf_fill": "#eaf7f0",
    "neutral_fill": "#f8f7f3",
}

DARK_PALETTE = {
    "background": "#000000",
    "panel": "#171717",
    "panel_alt": "#202020",
    "neutral_fill": "#2b2b2b",
    "ink": "#ffffff",
    "muted": "#aaaaaa",
    "line": "#777777",
    "soft_line": "#383838",
    "root": "#ffffff",
    "parent": "#ffffff",
    "leaf": "#ffffff",
    "root_fill": "#2b2b2b",
    "parent_fill": "#2b2b2b",
    "leaf_fill": "#2b2b2b",
}


class DiagramTheme(enum.StrEnum):
    """Visual presets that keep identical component geometry and hierarchy.

    LIGHT draws bordered, tinted surfaces on a transparent canvas. DARK draws
    borderless gray surfaces and white text on a black canvas.
    """

    LIGHT = "light"
    DARK = "dark"


class TextAnchor(enum.StrEnum):
    """Valid SVG horizontal text anchors."""

    START = "start"
    MIDDLE = "middle"
    END = "end"


class NodeRole(enum.StrEnum):
    """Semantic role of a node, resolved to a palette stroke and fill pair.

    A role names the position in the flow, not a color, so the same diagram
    reads correctly under every theme. ``ROOT`` is where data enters, ``PARENT``
    is work done on it, and ``LEAF`` is what comes out.
    """

    ROOT = "root"
    PARENT = "parent"
    LEAF = "leaf"


class PortSide(enum.StrEnum):
    """Named attachment edges for a rectangular node."""

    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"


def theme_palette(theme: DiagramTheme) -> Mapping[str, str]:
    """Returns the palette a theme draws with."""
    return DARK_PALETTE if theme == DiagramTheme.DARK else LIGHT_PALETTE


def golden_split(length: float) -> tuple[int, int]:
    """Divide a length at its golden section; returns the (major, minor) parts.

    The parts sum to the rounded length and their ratio is φ, so a panel split
    this way reads as two related sizes rather than two arbitrary ones.

    Raises:
        ValueError: if length is not positive.
    """
    positive_number(length, "length")
    minor = round(length / (1 + GOLDEN_RATIO))
    return round(length) - minor, minor


def golden_height(width: float) -> int:
    """Returns the height that makes a canvas of this width a golden rectangle.

    Raises:
        ValueError: if width is not positive.
    """
    positive_number(width, "width")
    return round(width / GOLDEN_RATIO)


def golden_point(start: float, length: float, *, from_end: bool = False) -> int:
    """Returns the golden section of a span, the off-center line to place a focus on.

    Measured from start by default, which puts the point past the middle; pass
    from_end to mirror it and sit the focus high, the way a title band does.

    Raises:
        ValueError: if start is not finite or length is not positive.
    """
    finite_number(start, "start")
    major, minor = golden_split(length)
    return round(start) + (minor if from_end else major)


def finite_number(number: float, name: str) -> float:
    """Reject booleans and non-finite coordinates before serializing invalid SVG.

    Raises:
        ValueError: if number is a bool, NaN, or infinite.
    """
    if isinstance(number, bool) or not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    return number


def positive_number(number: float, name: str, *, can_be_zero: bool = False) -> float:
    """Validate a finite positive geometry value.

    Raises:
        ValueError: if number is not finite, or not above the allowed minimum.
    """
    finite_number(number, name)
    minimum_is_valid = number >= 0 if can_be_zero else number > 0
    if not minimum_is_valid:
        qualifier = "non-negative" if can_be_zero else "positive"
        raise ValueError(f"{name} must be {qualifier}.")
    return number


def format_number(number: float) -> str:
    """Render a coordinate without a trailing ``.0`` so output stays stable."""
    if isinstance(number, int):
        return str(number)
    rounded = round(number, 4)
    return str(int(rounded)) if rounded == int(rounded) else str(rounded)


def svg_element(
    tag: str,
    *children: ElementTree.Element,
    text: str | None = None,
    **attributes: str | float | None,
) -> ElementTree.Element:
    """Build an SVG element; underscores in attribute names become hyphens.

    Attributes whose value is None are omitted. Text and attribute values are
    escaped by the serializer, so caller content is never interpreted as markup.
    """
    element = ElementTree.Element(tag)
    for name, value in attributes.items():
        if value is None:
            continue
        element.set(name.replace("_", "-"), value if isinstance(value, str) else format_number(value))
    if text is not None:
        element.text = text
    element.extend(children)
    return element


# Indenting inside these would add rendered whitespace to their content.
INLINE_TAGS = frozenset({"text", "tspan", "desc", "title"})


def serialize_element(element: ElementTree.Element, depth: int = 0) -> str:
    """Serialize one element as indented XML, keeping text content on one line."""
    padding = "  " * depth
    if element.tag in INLINE_TAGS or not len(element):
        return padding + ElementTree.tostring(element, encoding="unicode")
    opening = ElementTree.tostring(svg_element(element.tag, **dict(element.attrib)), encoding="unicode")
    head = opening.removesuffix(" />").removesuffix("/>").rstrip()
    lines = [f"{padding}{head}>"]
    lines.extend(serialize_element(child, depth + 1) for child in element)
    lines.append(f"{padding}</{element.tag}>")
    return "\n".join(lines)


class Diagram:
    """A themed SVG canvas with escaped content and validated geometry.

    Construct one per diagram, place components onto it with the module's
    component functions, then hand it to a report with ``figure`` or write it
    with ``save``. Palette keys such as ``"ink"`` or ``"root_fill"`` may be used
    anywhere a color is accepted; an unknown value is passed through as a
    literal CSS color.

    Brand a diagram by passing ``palette`` with only the keys that differ; the
    rest fall back to the theme's own, so partial overrides stay valid:

        Diagram("Flow", palette={"root": "#0e9f6e", "root_fill": "#ecfdf5"})

    A pair of colors in ``background`` washes the canvas with a gradient, and
    ``gradient`` defines one for anything drawn on top:

        Diagram("Flow", background=("#fff5e5", "#eaf7f0"))
    """

    def __init__(
        self,
        title: str,
        *,
        width: float = 1120,
        height: float = 692,
        theme: DiagramTheme = DiagramTheme.LIGHT,
        palette: Mapping[str, str] | None = None,
        font_family: str = DEFAULT_FONT_FAMILY,
        background: str | tuple[str, str] | None = None,
        borders: bool | None = None,
        stroke_width: float = BORDER_WIDTH,
    ) -> None:
        """Open a canvas.

        The default size is a golden rectangle; ``golden_height`` gives the
        matching height for any other width. The theme supplies the palette, the
        canvas fill, and whether surfaces are bordered; ``palette``,
        ``background``, and ``borders`` override each of those. A ``background``
        of None under the light theme leaves the canvas transparent, and a pair
        of colors washes it corner to corner as the ``canvas`` gradient.
        ``stroke_width`` is the border thickness every surface starts from, which
        each component can still override.

        Raises:
            ValueError: if title or font_family is blank, the size or stroke
                width is not positive, or a background pair is not two colors.
        """
        if not title.strip():
            raise ValueError("Diagram title must not be empty.")
        positive_number(width, "width")
        positive_number(height, "height")
        positive_number(stroke_width, "stroke_width")
        if not font_family.strip():
            raise ValueError("Diagram font family must not be empty.")
        if not isinstance(background, str | None) and len(background) != 2:
            raise ValueError("A background gradient takes exactly two colors.")

        self.title = title
        self.width = width
        self.height = height
        self.theme = theme
        self.palette = {**theme_palette(theme), **(palette or {})}
        self.font_family = font_family
        self.borders = theme != DiagramTheme.DARK if borders is None else borders
        self.stroke_width = stroke_width
        canvas = background if isinstance(background, str | None) else None
        if canvas is None and background is None and theme == DiagramTheme.DARK:
            canvas = "background"

        self.root = svg_element(
            "svg",
            xmlns="http://www.w3.org/2000/svg",
            width=width,
            height=height,
            viewBox=f"0 0 {format_number(width)} {format_number(height)}",
            role="img",
            aria_label=title,
        )
        arrow = svg_element(
            "marker",
            svg_element("path", d="M0,0 L0,6 L9,3 z", fill=self.color("ink")),
            id="arrow",
            markerWidth=10,
            markerHeight=10,
            refX=8,
            refY=3,
            orient="auto",
            markerUnits="strokeWidth",
        )
        self.defs = svg_element("defs", arrow)
        self.gradients: dict[str, tuple[str, str]] = {}
        self.root.append(self.defs)
        if not isinstance(background, str | None):
            canvas = self.gradient(CANVAS_GRADIENT, *background)
        if canvas is not None:
            self.root.append(svg_element("rect", width=width, height=height, fill=self.color(canvas)))

    def frame(self, color: str = "line", *, width: float | None = None, radius: float = 0) -> ElementTree.Element:
        """Outline the canvas edge; returns the element.

        The outline sits half a stroke inside the viewBox, because a rectangle
        drawn on the edge itself loses its outer half to the clip and renders at
        half the weight asked for. A frame is an explicit request, so it draws
        under a borderless theme too, the way ``boundary_frame`` does. Call it
        last if the frame should sit over content that reaches the edge.

        Raises:
            ValueError: if the width is not positive, the radius is negative, or
                the border is too thick for the canvas to hold.
        """
        width = self.stroke_width if width is None else width
        positive_number(width, "width")
        positive_number(radius, "radius", can_be_zero=True)
        if width >= min(self.width, self.height):
            raise ValueError("A canvas frame must be thinner than the canvas.")
        inset = width / 2
        return self.append(
            svg_element(
                "rect",
                x=inset,
                y=inset,
                width=self.width - width,
                height=self.height - width,
                rx=radius or None,
                fill="none",
                stroke=self.color(color),
                stroke_width=width,
            )
        )

    def color(self, color: str) -> str:
        """Resolve a palette key, or pass a literal CSS color through.

        Raises:
            ValueError: if the resolved color is blank.
        """
        resolved = self.palette.get(color, color)
        if not resolved.strip():
            raise ValueError("Diagram color must not be empty.")
        return resolved

    def gradient(
        self,
        name: str,
        start: str,
        end: str,
        *,
        x1: float = 0,
        y1: float = 0,
        x2: float = 1,
        y2: float = 1,
    ) -> str:
        """Define a two-stop linear gradient; returns the paint to fill or stroke with.

        The returned ``url(#name)`` is accepted anywhere a color is, so one
        gradient can fill a node, stroke its border, or do both. ``start`` and
        ``end`` resolve through the palette, which keeps a gradient built from
        role keys correct under every theme. The axis runs in bounding-box
        fractions, so the gradient spans whatever element uses it: the default
        runs corner to corner, ``x2=1, y2=0`` runs left to right.

        SVG resolves a paint by id, not by document order, so a gradient defined
        after the element that references it still applies. That is the way to
        give the canvas a gradient on an axis of your own: construct with
        ``background="url(#hero)"``, then define ``hero`` here.

        Raises:
            ValueError: if the name is not a valid unique SVG id, an axis point
                is not finite, or a color resolves to blank.
        """
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", name) is None:
            raise ValueError("A gradient name must start with a letter and use letters, digits, '-', or '_'.")
        if name in self.gradients:
            raise ValueError(f"Gradient {name!r} is already defined on this diagram.")
        for axis_name, axis in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)):
            finite_number(axis, axis_name)
        stops = (self.color(start), self.color(end))
        self.gradients[name] = stops
        self.defs.append(
            svg_element(
                "linearGradient",
                svg_element("stop", offset="0%", stop_color=stops[0]),
                svg_element("stop", offset="100%", stop_color=stops[1]),
                id=name,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
            )
        )
        return f"url(#{name})"

    def append(self, element: ElementTree.Element) -> ElementTree.Element:
        """Append a custom element when the drawing methods are insufficient."""
        self.root.append(element)
        return element

    def rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        fill: str = "panel",
        stroke: str = "line",
        radius: float = RADIUS,
        stroke_width: float | None = None,
    ) -> ElementTree.Element:
        """Append a rounded rectangle; the stroke is dropped in borderless themes.

        A stroke width of None takes the diagram's own.
        """
        finite_number(x, "x")
        finite_number(y, "y")
        positive_number(width, "width")
        positive_number(height, "height")
        positive_number(radius, "radius", can_be_zero=True)
        stroke_width = self.stroke_width if stroke_width is None else stroke_width
        positive_number(stroke_width, "stroke_width")
        return self.append(
            svg_element(
                "rect",
                x=x,
                y=y,
                width=width,
                height=height,
                rx=radius,
                fill=self.color(fill),
                stroke=self.color(stroke) if self.borders else "none",
                stroke_width=stroke_width,
            )
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        color: str = "ink",
        width: float = 2,
        arrow: bool = False,
        dashed: bool = False,
    ) -> ElementTree.Element:
        """Append a straight line; solid means the normal path, dashed a conditional one."""
        for name, coordinate in (("x1", x1), ("y1", y1), ("x2", x2), ("y2", y2)):
            finite_number(coordinate, name)
        positive_number(width, "width")
        return self.append(
            svg_element(
                "line",
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                stroke=self.color(color),
                stroke_width=width,
                marker_end="url(#arrow)" if arrow else None,
                stroke_dasharray="8 5" if dashed else None,
            )
        )

    def path(
        self,
        points: Sequence[tuple[float, float]],
        *,
        color: str = "ink",
        width: float = 2,
        arrow: bool = False,
        dashed: bool = False,
    ) -> ElementTree.Element:
        """Append a polyline through at least two validated points.

        Raises:
            ValueError: if fewer than two points are given, or a coordinate is not finite.
        """
        if len(points) < 2:
            raise ValueError("A diagram path requires at least two points.")
        for index, (x, y) in enumerate(points):
            finite_number(x, f"points[{index}].x")
            finite_number(y, f"points[{index}].y")
        positive_number(width, "width")
        command = "M " + " L ".join(f"{format_number(x)} {format_number(y)}" for x, y in points)
        return self.append(
            svg_element(
                "path",
                d=command,
                fill="none",
                stroke=self.color(color),
                stroke_width=width,
                marker_end="url(#arrow)" if arrow else None,
                stroke_dasharray="8 5" if dashed else None,
            )
        )

    def text(
        self,
        x: float,
        y: float,
        lines: str | Sequence[str],
        *,
        size: float = TEXT_TITLE,
        color: str = "ink",
        weight: int = 500,
        anchor: TextAnchor | str = TextAnchor.MIDDLE,
        line_height: float = LINE_HEIGHT,
    ) -> ElementTree.Element:
        """Append single- or multi-line text at a baseline; y is the first baseline.

        Raises:
            ValueError: if anchor is not a TextAnchor, or lines is empty.
        """
        finite_number(x, "x")
        finite_number(y, "y")
        positive_number(size, "size")
        positive_number(weight, "weight")
        positive_number(line_height, "line_height")
        resolved_anchor = self.anchor(anchor)
        rows = [lines] if isinstance(lines, str) else list(lines)
        if not rows:
            raise ValueError("Diagram text requires at least one line.")
        element = svg_element(
            "text",
            x=x,
            y=y,
            text_anchor=resolved_anchor.value,
            font_family=self.font_family,
            font_size=size,
            font_weight=weight,
            fill=self.color(color),
        )
        for index, row in enumerate(rows):
            element.append(svg_element("tspan", text=row, x=x, dy=0 if index == 0 else size * line_height))
        return self.append(element)

    def rich_line(
        self,
        x: float,
        y: float,
        fragments: Sequence[tuple[str, str]],
        *,
        size: float = TEXT_BODY,
        weight: int = 600,
        anchor: TextAnchor | str = TextAnchor.MIDDLE,
    ) -> ElementTree.Element:
        """Append one line of text whose (fragment, color) pairs are colored separately.

        Raises:
            ValueError: if fragments is empty or anchor is not a TextAnchor.
        """
        finite_number(x, "x")
        finite_number(y, "y")
        positive_number(size, "size")
        positive_number(weight, "weight")
        resolved_anchor = self.anchor(anchor)
        if not fragments:
            raise ValueError("Rich diagram text requires at least one fragment.")
        element = svg_element(
            "text",
            x=x,
            y=y,
            text_anchor=resolved_anchor.value,
            font_family=self.font_family,
            font_size=size,
            font_weight=weight,
        )
        for fragment, color in fragments:
            element.append(svg_element("tspan", text=fragment, fill=self.color(color)))
        return self.append(element)

    def circle(self, x: float, y: float, radius: float, color: str = "ink") -> ElementTree.Element:
        """Append a filled circle."""
        finite_number(x, "x")
        finite_number(y, "y")
        positive_number(radius, "radius")
        return self.append(svg_element("circle", cx=x, cy=y, r=radius, fill=self.color(color)))

    def anchor(self, anchor: TextAnchor | str) -> TextAnchor:
        """Resolve a text anchor.

        Raises:
            ValueError: if anchor does not name a TextAnchor member.
        """
        try:
            return TextAnchor(anchor)
        except ValueError as error:
            raise ValueError(f"Invalid diagram text anchor: {anchor!r}.") from error

    def to_string(self) -> str:
        """Serialize deterministic, indented SVG with a trailing newline."""
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{serialize_element(self.root)}\n'

    def data_url(self) -> str:
        """Returns the diagram as a base64 ``data:image/svg+xml`` URL."""
        encoded = base64.b64encode(self.to_string().encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"

    def save(self, path: Path) -> None:
        """Create the destination directory and write the SVG as UTF-8."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_string(), encoding="utf-8")

    def figure(self, alt_text: str | None = None, *, caption: str | None = None) -> Figure:
        """Returns a report figure embedding this diagram, defaulting its alternative text to the title."""
        return Figure(
            source=self.data_url(),
            alt_text=self.title if alt_text is None else alt_text,
            caption=caption,
            is_embedded=True,
        )


def box_label(
    diagram: Diagram,
    x: float,
    y: float,
    width: float,
    height: float,
    lines: str | Sequence[str],
    *,
    fill: str = "neutral_fill",
    stroke: str = "line",
    stroke_width: float | None = None,
    color: str = "ink",
    size: float = TEXT_TITLE,
    weight: int = 600,
) -> None:
    """Draw centered text inside a rounded rectangle.

    Lines are set on the φ leading every stacked label uses, so a box has to be
    tall enough to hold ``size + (rows - 1) * size * φ`` and still clear its own
    corner. These are line-box metrics, not measured ink extents, so glyph
    bounds still need visual verification in the target font.

    Raises:
        ValueError: if lines is empty, or the stack leaves under 13 units of
            padding above and below.
    """
    diagram.rect(x, y, width, height, fill=fill, stroke=stroke, radius=RADIUS, stroke_width=stroke_width)
    rows = [lines] if isinstance(lines, str) else list(lines)
    if not rows:
        raise ValueError("A box label requires at least one line.")
    total_height = (len(rows) - 1) * size * LINE_HEIGHT
    if (height - total_height - size) / 2 < RADIUS:
        raise ValueError("A box label needs at least 13 units of padding above and below its lines.")
    baseline = y + height / 2 - total_height / 2 + size * 0.35
    diagram.text(x + width / 2, baseline, rows, size=size, color=color, weight=weight)


def centered_text_stack(
    diagram: Diagram,
    x: float,
    y: float,
    height: float,
    rows: Sequence[tuple[str, float, int, str]],
    *,
    anchor: TextAnchor,
    gap: float | None = None,
) -> None:
    """Center a complete text stack in a box using equal top and bottom line-box space.

    Each row carries text, size, weight, and color. A gap of None gives each row
    its own size over φ, which puts the advance to the next row at one φ step of
    that row's size, the same leading LINE_HEIGHT gives a wrapped label. Pass a
    number to set one gap for every row instead. The 0.35-em baseline offset
    matches box_label. These are line-box metrics, not measured ink extents, so
    glyph bounds still need visual verification in the target font.

    Raises:
        ValueError: if rows is empty, the gap is negative, or the stack leaves
            under 13 units of padding.
    """
    if not rows:
        raise ValueError("A text stack needs at least one row.")
    if gap is not None:
        positive_number(gap, "gap", can_be_zero=True)
    gaps = [size / GOLDEN_RATIO if gap is None else gap for _, size, _, _ in rows[:-1]]
    content_height = sum(size for _, size, _, _ in rows) + sum(gaps)
    padding = (height - content_height) / 2
    if padding < RADIUS:
        raise ValueError("A text stack needs at least 13 units of padding on both sides.")
    top = y + padding
    for index, (label, size, weight, color) in enumerate(rows):
        baseline = top + size / 2 + size * 0.35
        diagram.text(x, baseline, label, size=size, weight=weight, color=color, anchor=anchor)
        top += size + (gaps[index] if index < len(gaps) else 0)


def role_colors(role: NodeRole | str) -> tuple[str, str]:
    """Returns the (stroke, fill) palette keys for a node role."""
    name = str(role)
    return name, f"{name}_fill"


def node_paint(role: NodeRole | str, fill: str | None, stroke: str | None) -> tuple[str, str]:
    """Returns the (stroke, fill) a node draws with, after either override replaces its role key.

    An override is any color the diagram accepts, including the ``url(#name)``
    a gradient returns, so a node can carry a gradient and keep its role.
    """
    role_stroke, role_fill = role_colors(role)
    return role_stroke if stroke is None else stroke, role_fill if fill is None else fill


def title_node(
    diagram: Diagram,
    x: float,
    y: float,
    width: float,
    title: str,
    *,
    role: NodeRole | str,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float | None = None,
) -> None:
    """A compact 55-unit node for a short name with no supporting copy."""
    node_stroke, node_fill = node_paint(role, fill, stroke)
    box_label(
        diagram,
        x,
        y,
        width,
        TITLE_NODE_HEIGHT,
        title,
        fill=node_fill,
        stroke=node_stroke,
        stroke_width=stroke_width,
        color="ink",
        size=TEXT_TITLE,
        weight=550,
    )


def centered_node(
    diagram: Diagram,
    x: float,
    y: float,
    width: float,
    title: str,
    description: str,
    *,
    role: NodeRole | str,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float | None = None,
) -> None:
    """An 89-unit node with a title and one short, subordinate description."""
    node_stroke, node_fill = node_paint(role, fill, stroke)
    diagram.rect(
        x,
        y,
        width,
        CENTERED_NODE_HEIGHT,
        fill=node_fill,
        stroke=node_stroke,
        radius=RADIUS,
        stroke_width=stroke_width,
    )
    centered_text_stack(
        diagram,
        x + width / 2,
        y,
        CENTERED_NODE_HEIGHT,
        [(title, TEXT_TITLE, 550, "ink"), (description, TEXT_BODY, 400, "muted")],
        anchor=TextAnchor.MIDDLE,
    )


def information_node(
    diagram: Diagram,
    x: float,
    y: float,
    width: float,
    eyebrow: str,
    title: str,
    description: Sequence[str],
    *,
    role: NodeRole | str,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float | None = None,
) -> float:
    """Left-align a category, title, and explicit description lines; returns the height.

    The tall card of the set: 144 units for one description line, 26 more for
    each line after it, with its copy inset 34 units from the left edge.

    Raises:
        ValueError: if description has no lines.
    """
    if not description:
        raise ValueError("An information node needs a description.")
    node_stroke, node_fill = node_paint(role, fill, stroke)
    height = INFORMATION_NODE_HEIGHT + (len(description) - 1) * INFORMATION_NODE_LINE
    diagram.rect(x, y, width, height, fill=node_fill, stroke=node_stroke, radius=RADIUS, stroke_width=stroke_width)
    centered_text_stack(
        diagram,
        x + CARD_INSET,
        y,
        height,
        [
            (eyebrow, TEXT_CAPTION, 550, node_stroke),
            (title, TEXT_TITLE, 550, "ink"),
            *((line, TEXT_BODY, 400, "muted") for line in description),
        ],
        anchor=TextAnchor.START,
    )
    return height


class LucideIcon(enum.StrEnum):
    """Convenient names; the loader also accepts any pinned-release icon name."""

    BOT = "bot"
    DATABASE = "database"
    FILE_CHECK_2 = "file-check-2"
    MESSAGES_SQUARE = "messages-square"
    NOTEBOOK_TEXT = "notebook-text"
    SHARE_2 = "share-2"
    SHIELD_CHECK = "shield-check"
    TABLE_2 = "table-2"


LUCIDE_VERSION = "0.468.0"
DEFAULT_ICON_CACHE_DIR = Path.home() / ".cache" / "mdreport" / "icons" / "lucide"
HEX_COLOR = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
LUCIDE_SHAPES = {
    "path": {"d"},
    "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx", "ry"},
    "rect": {"x", "y", "width", "height", "rx", "ry"},
    "line": {"x1", "y1", "x2", "y2"},
    "polyline": {"points"},
    "polygon": {"points"},
}


def lucide_icon_element(
    name: str,
    *,
    primary: str = "#ffffff",
    accent: str | None = None,
    accent_parts: Sequence[int] = (),
    gradient: tuple[str, str] | None = None,
    element_id: str | None = None,
    size: float = TEXT_DISPLAY,
    x: float = 0,
    y: float = 0,
    cache_dir: Path = DEFAULT_ICON_CACHE_DIR,
) -> ElementTree.Element:
    """Fetch a pinned Lucide icon and return safe, editable SVG geometry.

    Cache hits work offline. A cache miss fetches the icon and the upstream
    LICENSE from jsDelivr's pinned lucide-static package with a 15-second
    timeout; no caller-provided URL is ever requested. Duo color uses zero-based
    geometry indices; a gradient colors every stroke and needs an element_id
    unique within the containing document. Colors are #RGB or #RRGGBB.

    Raises:
        ValueError: if the name, colors, indices, or fetched geometry are invalid.
        OSError: if the icon is not cached and cannot be fetched.
    """
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(name)) is None:
        raise ValueError("Use a Lucide kebab-case icon name.")
    positive_number(size, "size")
    finite_number(x, "x")
    finite_number(y, "y")
    colors = [primary]
    if accent is not None:
        colors.append(accent)
        if not accent_parts:
            raise ValueError("Duo color requires explicit accent_parts indices.")
    elif accent_parts:
        raise ValueError("accent_parts requires an accent color.")
    if gradient is not None:
        if len(gradient) != 2 or accent is not None:
            raise ValueError("Use two gradient colors, without a duo-color accent.")
        if element_id is None or re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", element_id) is None:
            raise ValueError("A gradient needs a unique element_id, such as 'record-gradient'.")
        colors.extend(gradient)
    if any(HEX_COLOR.fullmatch(color) is None for color in colors):
        raise ValueError("Icon colors must be #RGB or #RRGGBB.")

    assets = lucide_assets(str(name), cache_dir)
    geometry = lucide_geometry(assets[f"icons/{name}.svg"])
    if any(type(index) is not int or index < 0 or index >= len(geometry) for index in accent_parts):
        raise ValueError("accent_parts must reference existing geometry indices.")

    # Cache only after structural validation; preserve the upstream license too.
    for filename, content in assets.items():
        cached = cache_dir / LUCIDE_VERSION / filename
        if not cached.exists():
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text(content, encoding="utf-8")

    mark = svg_element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        x=x,
        y=y,
        width=size,
        height=size,
        viewBox="0 0 24 24",
        fill="none",
        stroke=primary,
        stroke_width=2,
        stroke_linecap="round",
        stroke_linejoin="round",
        aria_hidden="true",
        focusable="false",
    )
    mark.append(svg_element("desc", text=f"Lucide {LUCIDE_VERSION}: {name}. " + assets["LICENSE"]))
    if gradient is not None:
        mark.append(
            svg_element(
                "defs",
                svg_element(
                    "linearGradient",
                    svg_element("stop", offset="0%", stop_color=gradient[0]),
                    svg_element("stop", offset="100%", stop_color=gradient[1]),
                    id=element_id,
                    x1=0,
                    y1=0,
                    x2=24,
                    y2=24,
                    gradientUnits="userSpaceOnUse",
                ),
            )
        )
    for index, (tag, attributes) in enumerate(geometry):
        stroke = (
            f"url(#{element_id})"
            if gradient is not None
            else accent
            if accent is not None and index in accent_parts
            else primary
        )
        mark.append(svg_element(tag, **{**attributes, "stroke": stroke}))
    return mark


def lucide_assets(name: str, cache_dir: Path) -> dict[str, str]:
    """Returns the icon source and the upstream LICENSE, reading the cache first.

    Raises:
        ValueError: if a fetched asset exceeds the 100 KB limit.
        OSError: if an uncached asset cannot be fetched.
    """
    assets: dict[str, str] = {}
    for filename in (f"icons/{name}.svg", "LICENSE"):
        cached = cache_dir / LUCIDE_VERSION / filename
        if cached.exists():
            assets[filename] = cached.read_text(encoding="utf-8")
            continue
        url = f"https://cdn.jsdelivr.net/npm/lucide-static@{LUCIDE_VERSION}/{filename}"
        with urlopen(url, timeout=15) as response:
            payload = response.read(100_001)
        if len(payload) > 100_000:
            raise ValueError("A Lucide asset exceeds the 100 KB limit.")
        assets[filename] = payload.decode("utf-8")
    return assets


def lucide_geometry(source: str) -> list[tuple[str, dict[str, str]]]:
    """Parse a Lucide SVG into plain shape tags and attributes.

    Only the flat, attribute-only shapes Lucide emits are accepted, so nothing
    scriptable, nested, or externally referenced can reach the output.

    Raises:
        ValueError: if the document declares entities, is not a 24-unit Lucide
            SVG, is empty, or contains unsupported geometry.
    """
    if "<!DOCTYPE" in source.upper() or "<!ENTITY" in source.upper():
        raise ValueError("A Lucide SVG must not contain document entities.")
    root = ElementTree.fromstring(source)
    namespace = "{http://www.w3.org/2000/svg}"
    if root.tag != f"{namespace}svg" or root.get("viewBox") != "0 0 24 24":
        raise ValueError("Expected a Lucide SVG with a 24-unit viewBox.")
    if not len(root):
        raise ValueError("The Lucide icon contains no geometry.")
    geometry: list[tuple[str, dict[str, str]]] = []
    for child in root:
        tag = child.tag.removeprefix(namespace)
        if tag not in LUCIDE_SHAPES or len(child) or not set(child.attrib) <= LUCIDE_SHAPES[tag]:
            raise ValueError(f"Unsupported Lucide geometry: {tag}.")
        geometry.append((tag, dict(child.attrib)))
    return geometry


def icon_node(
    diagram: Diagram,
    x: float,
    y: float,
    width: float,
    title: str,
    description: str,
    *,
    icon: LucideIcon | str,
    role: NodeRole | str,
    fill: str | None = None,
    stroke: str | None = None,
    stroke_width: float | None = None,
    icon_accent: str | None = None,
    accent_parts: Sequence[int] = (),
    icon_gradient: tuple[str, str] | None = None,
    icon_id: str | None = None,
    icon_cache_dir: Path = DEFAULT_ICON_CACHE_DIR,
) -> None:
    """An 89-unit node with left-aligned copy and a decorative right-side icon.

    Reserves 34 units for the icon, a 21-unit text/icon gap, and 21-unit outer
    padding. Copy must fit the remaining width (width - 97); nothing wraps.

    The icon is drawn in the node's stroke color. A Lucide stroke has to be a
    flat hex color, so a border carrying a gradient leaves the icon on the
    role's own color; ``icon_gradient`` is how an icon takes one.

    Raises:
        ValueError: if width is under 144 units, or the icon cannot be resolved.
    """
    if width < 144:
        raise ValueError("An icon node must be at least 144 units wide.")
    node_stroke, node_fill = node_paint(role, fill, stroke)
    icon_stroke = node_stroke if HEX_COLOR.fullmatch(diagram.color(node_stroke)) else role_colors(role)[0]
    diagram.rect(
        x,
        y,
        width,
        ICON_NODE_HEIGHT,
        fill=node_fill,
        stroke=node_stroke,
        radius=RADIUS,
        stroke_width=stroke_width,
    )
    centered_text_stack(
        diagram,
        x + INSET,
        y,
        ICON_NODE_HEIGHT,
        [(title, TEXT_TITLE, 550, "ink"), (description, TEXT_BODY, 400, "muted")],
        anchor=TextAnchor.START,
    )
    diagram.append(
        lucide_icon_element(
            str(icon),
            primary=diagram.color(icon_stroke),
            accent=icon_accent,
            accent_parts=accent_parts,
            gradient=icon_gradient,
            element_id=icon_id,
            x=x + width - INSET - TEXT_DISPLAY,
            y=y + (ICON_NODE_HEIGHT - TEXT_DISPLAY) / 2,
            cache_dir=icon_cache_dir,
        )
    )


def group_panel(
    diagram: Diagram,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    caption: str | None = None,
) -> None:
    """Frame a group with a top-left heading and a muted bottom-left caption.

    Reserve PANEL_HEADING_BAND (55) units above the children and
    PANEL_CAPTION_BAND (34) below them for the furniture.
    """
    diagram.rect(x, y, width, height, fill="panel", stroke="soft_line", radius=PANEL_RADIUS)
    diagram.text(x + INSET, y + 34, title, size=TEXT_TITLE, weight=500, anchor=TextAnchor.START)
    if caption:
        diagram.text(
            x + INSET,
            y + height - RADIUS,
            caption,
            size=TEXT_SMALL,
            weight=400,
            color="muted",
            anchor=TextAnchor.START,
        )


def legend_header(diagram: Diagram, x: float, y: float, width: float, *, title: str | None = "Legend") -> float:
    """Draw the mandatory separator and optional heading; returns the key centerline.

    Place the rule at least 21 units below the preceding content and align its
    ends with the legend's content column. The rule stays even without a heading.
    """
    diagram.line(x, y, x + width, y, color="soft_line", width=1.5)
    if title:
        diagram.text(x, y + INSET, title, size=TEXT_SMALL, color="muted", weight=500, anchor=TextAnchor.START)
        return y + 55
    return y + 34


def color_key(diagram: Diagram, x: float, y: float, label: str, role: NodeRole | str) -> None:
    """Place a color swatch and its left-aligned label on a shared centerline."""
    diagram.circle(x + GAP, y, GAP, role_colors(role)[0])
    diagram.text(x + 29, y + 6, label, size=TEXT_BODY, weight=400, anchor=TextAnchor.START)


def arrow_key(diagram: Diagram, x: float, y: float, label: str, *, dashed: bool = False) -> None:
    """Show the actual connector treatment beside its meaning."""
    diagram.line(x, y, x + 55, y, arrow=True, dashed=dashed)
    diagram.text(x + 68, y + 6, label, size=TEXT_BODY, weight=400, anchor=TextAnchor.START)


def node_port(x: float, y: float, width: float, height: float, side: PortSide) -> tuple[float, float]:
    """Derive a connector attachment point from node bounds."""
    return {
        PortSide.LEFT: (x, y + height / 2),
        PortSide.RIGHT: (x + width, y + height / 2),
        PortSide.TOP: (x + width / 2, y),
        PortSide.BOTTOM: (x + width / 2, y + height),
    }[side]


def junction(diagram: Diagram, x: float, y: float) -> None:
    """A filled dot denotes a connected split or merge, never a plain crossing."""
    diagram.circle(x, y, 5, "ink")


def decision_node(diagram: Diagram, x: float, y: float, width: float, height: float, label: str) -> None:
    """Center a short condition in a diamond; branch labels belong to the connectors."""
    points = [
        (x + width / 2, y),
        (x + width, y + height / 2),
        (x + width / 2, y + height),
        (x, y + height / 2),
    ]
    diagram.append(
        svg_element(
            "polygon",
            points=" ".join(f"{format_number(px)},{format_number(py)}" for px, py in points),
            fill=diagram.color("neutral_fill"),
            stroke=diagram.color("line") if diagram.borders else "none",
            stroke_width=2,
        )
    )
    diagram.text(x + width / 2, y + height / 2 + 6, label, size=TEXT_BODY, weight=550)


def labeled_connector(
    diagram: Diagram,
    start: tuple[float, float],
    end: tuple[float, float],
    label: str,
    *,
    dashed: bool = False,
) -> None:
    """Label a horizontal arrow with a consistent clearance above its centerline.

    Raises:
        ValueError: if the connector is not horizontal.
    """
    if start[1] != end[1]:
        raise ValueError("A labeled connector must be horizontal.")
    diagram.line(*start, *end, arrow=True, dashed=dashed)
    diagram.text((start[0] + end[0]) / 2, start[1] - INSET, label, size=TEXT_SMALL, weight=500, color="muted")


def swimlane(diagram: Diagram, x: float, y: float, width: float, height: float, title: str) -> None:
    """A lane uses a fixed LANE_HEADER (144) column to identify an actor or execution owner."""
    diagram.rect(x, y, width, height, fill="panel_alt", stroke="soft_line", radius=GAP)
    diagram.text(x + INSET, y + height / 2 + 6, title, size=TEXT_BODY, weight=500, anchor=TextAnchor.START)
    diagram.line(x + LANE_HEADER, y + RADIUS, x + LANE_HEADER, y + height - RADIUS, color="soft_line", width=1.5)


def repeated_stack(diagram: Diagram, x: float, y: float, width: float, title: str, count: str) -> None:
    """Two offset silhouettes imply repetition; only the front layer carries text.

    The front layer is 89 units tall at the given position, and the stack behind
    it reaches 13 units further right and down.
    """
    for offset, fill in ((RADIUS, "line"), (GAP, "soft_line"), (0, "neutral_fill")):
        diagram.rect(x + offset, y + offset, width, STACK_HEIGHT, fill=fill, stroke="line", radius=RADIUS)
    centered_text_stack(
        diagram,
        x + width / 2,
        y,
        STACK_HEIGHT,
        [(title, TEXT_TITLE, 550, "ink"), (count, TEXT_SMALL, 400, "muted")],
        anchor=TextAnchor.MIDDLE,
    )


def annotation_callout(
    diagram: Diagram,
    x: float,
    y: float,
    lines: Sequence[str],
    target: tuple[float, float],
) -> None:
    """Muted explanatory copy uses a leader line with no directional arrowhead."""
    diagram.path([target, (x - INSET, target[1]), (x - INSET, y - 5), (x - GAP, y - 5)], color="muted", width=1.5)
    diagram.text(
        x,
        y,
        lines,
        size=TEXT_BODY,
        weight=400,
        color="muted",
        anchor=TextAnchor.START,
    )


def list_node(diagram: Diagram, x: float, y: float, width: float, title: str, rows: Sequence[str]) -> float:
    """A compact field list with a header divider and equal-height rows; returns the height.

    The header band is 55 units, each row is 21, and the list closes with a
    13-unit foot, so the height is 68 plus 21 per row.
    """
    height = LIST_NODE_HEADER + RADIUS + LIST_NODE_ROW * len(rows)
    diagram.rect(x, y, width, height, fill="neutral_fill", stroke="line", radius=RADIUS)
    diagram.text(x + INSET, y + 34, title, size=TEXT_TITLE, weight=550, anchor=TextAnchor.START)
    diagram.line(x + INSET, y + 47, x + width - INSET, y + 47, color="soft_line", width=1.5)
    for index, row in enumerate(rows):
        baseline = y + LIST_NODE_HEADER + 16 + index * LIST_NODE_ROW
        diagram.text(x + INSET, baseline, row, size=TEXT_SMALL, weight=400, color="muted", anchor=TextAnchor.START)
    return height


def boundary_frame(diagram: Diagram, x: float, y: float, width: float, height: float, title: str) -> None:
    """A labeled ownership boundary keeps an explicit outline even in borderless themes."""
    diagram.append(
        svg_element(
            "rect",
            x=x,
            y=y,
            width=width,
            height=height,
            rx=GAP,
            fill="none",
            stroke=diagram.color("line"),
            stroke_width=1.5,
        )
    )
    diagram.text(x + INSET, y + 26, title, size=TEXT_SMALL, weight=500, color="muted", anchor=TextAnchor.START)
