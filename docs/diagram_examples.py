"""Render the sample diagrams shown on the `Diagrams` documentation page.

Every function here draws the diagram one section of `source/diagrams.md` builds,
so the code on that page and the image beside it stay in step. Each diagram is
written twice, once per theme, into `source/_static/diagrams/`.

Every coordinate comes from the library's golden-ratio scale. The wide canvas is
1220 units across: a 34-unit margin, three 288-unit nodes, and the 144-unit gaps
those leave. Node widths, gaps, and margins are all Fibonacci steps, so any two
of them stand in golden proportion.

    uv run docs/diagram_examples.py
    uv run docs/diagram_examples.py --output docs/source/_static/diagrams
"""

from collections.abc import Callable
from pathlib import Path

import click

from mdreport import (
    Diagram,
    DiagramTheme,
    LucideIcon,
    NodeRole,
    PortSide,
    TextAnchor,
    annotation_callout,
    arrow_key,
    boundary_frame,
    box_label,
    centered_node,
    color_key,
    decision_node,
    group_panel,
    icon_node,
    information_node,
    junction,
    labeled_connector,
    legend_header,
    list_node,
    node_port,
    repeated_stack,
    svg_element,
    swimlane,
    title_node,
)

BRAND_PALETTES = {
    DiagramTheme.LIGHT: {"root": "#0e9f6e", "root_fill": "#ecfdf5", "leaf": "#7c3aed", "leaf_fill": "#f3e8ff"},
    DiagramTheme.DARK: {"root": "#34d399", "root_fill": "#0c2b22", "leaf": "#c4b5fd", "leaf_fill": "#231a39"},
}


def one_node(theme: DiagramTheme) -> Diagram:
    """The smallest diagram: a node in the golden section of its canvas."""
    diagram = Diagram("Source", width=466, height=89, theme=theme)
    title_node(diagram, 89, 17, 288, "Source", role=NodeRole.ROOT)
    return diagram


def two_nodes(theme: DiagramTheme) -> Diagram:
    """Two nodes joined by an arrow."""
    diagram = Diagram("Ingest", width=987, height=144, theme=theme)
    title_node(diagram, 89, 44.5, 288, "Source", role=NodeRole.ROOT)
    title_node(diagram, 610, 44.5, 288, "Store", role=NodeRole.LEAF)
    diagram.line(398, 72, 589, 72, arrow=True)
    return diagram


def three_roles(theme: DiagramTheme) -> Diagram:
    """One node of each role, each carrying as much copy as its shape allows."""
    diagram = Diagram("Ingest pipeline", width=1220, height=212, theme=theme)
    title_node(diagram, 34, 78.5, 288, "Source", role=NodeRole.ROOT)
    centered_node(diagram, 466, 61.5, 288, "Transform", "Normalize the input", role=NodeRole.PARENT)
    information_node(
        diagram,
        898,
        34,
        288,
        "Output artifact",
        "Checked record",
        ["Ready when checks pass"],
        role=NodeRole.LEAF,
    )
    diagram.line(343, 106, 445, 106, arrow=True)
    diagram.line(775, 106, 877, 106, arrow=True)
    return diagram


def with_legend(theme: DiagramTheme) -> Diagram:
    """The same row, plus a conditional return path and the legend that reads it."""
    diagram = Diagram("Ingest pipeline", width=1220, height=342, theme=theme)
    title_node(diagram, 34, 78.5, 288, "Source", role=NodeRole.ROOT)
    centered_node(diagram, 466, 61.5, 288, "Transform", "Normalize the input", role=NodeRole.PARENT)
    information_node(
        diagram,
        898,
        34,
        288,
        "Output artifact",
        "Checked record",
        ["Ready when checks pass"],
        role=NodeRole.LEAF,
    )
    diagram.line(343, 106, 445, 106, arrow=True)
    diagram.line(775, 106, 877, 106, arrow=True)

    diagram.path([(1042, 178), (1042, 212), (610, 212), (610, 158)], dashed=True, arrow=True)
    diagram.text(826, 199, "If invalid: retry", size=15, color="muted", weight=500)

    key_y = legend_header(diagram, 34, 246, 1152)
    is_colored = diagram.theme != DiagramTheme.DARK
    if is_colored:
        color_key(diagram, 34, key_y, "Collected input", NodeRole.ROOT)
        color_key(diagram, 267, key_y, "Processing", NodeRole.PARENT)
        color_key(diagram, 500, key_y, "Published output", NodeRole.LEAF)
    arrow_key(diagram, 733 if is_colored else 34, key_y, "Normal flow")
    arrow_key(diagram, 967 if is_colored else 267, key_y, "Conditional flow", dashed=True)
    return diagram


def grouped(theme: DiagramTheme) -> Diagram:
    """A panel around the row, with a heading and a caption."""
    diagram = Diagram("Ingest pipeline", width=1220, height=430, theme=theme)
    diagram.text(610, 55, "Ingest pipeline", size=29, weight=550)

    caption = "Peers with the same role use the same node pattern."
    group_panel(diagram, 34, 89, 1152, 233, "Main flow", caption)
    title_node(diagram, 89, 188.5, 288, "Source", role=NodeRole.ROOT)
    centered_node(diagram, 466, 171.5, 288, "Transform", "Normalize the input", role=NodeRole.PARENT)
    information_node(
        diagram,
        843,
        144,
        288,
        "Output artifact",
        "Checked record",
        ["Ready when checks pass"],
        role=NodeRole.LEAF,
    )
    diagram.line(398, 216, 445, 216, arrow=True)
    diagram.line(775, 216, 822, 216, arrow=True)

    key_y = legend_header(diagram, 34, 356, 1152, title=None)
    is_colored = diagram.theme != DiagramTheme.DARK
    if is_colored:
        color_key(diagram, 34, key_y, "Collected input", NodeRole.ROOT)
        color_key(diagram, 267, key_y, "Processing", NodeRole.PARENT)
        color_key(diagram, 500, key_y, "Published output", NodeRole.LEAF)
    arrow_key(diagram, 733 if is_colored else 34, key_y, "Normal flow")
    return diagram


def branching(theme: DiagramTheme) -> Diagram:
    """A condition with an accepted path and a dashed quarantine path."""
    diagram = Diagram("Validation", width=1220, height=267, theme=theme)
    title_node(diagram, 34, 116.5, 233, "Record", role=NodeRole.ROOT)
    decision_node(diagram, 377, 99.5, 233, 89, "Schema ok?")
    diagram.line(*node_port(34, 116.5, 233, 55, PortSide.RIGHT), 356, 144, arrow=True)

    box_label(diagram, 733, 89, 178, 55, "Accept", fill="leaf_fill", stroke="leaf", size=18)
    box_label(diagram, 733, 178, 178, 55, "Quarantine", size=18)

    accepted = node_port(377, 99.5, 233, 89, PortSide.RIGHT)
    diagram.path([accepted, (667, 144), (667, 116.5), (712, 116.5)], arrow=True)
    diagram.text(679, 108, "Yes", size=15, color="muted", weight=500, anchor=TextAnchor.START)

    rejected = node_port(377, 99.5, 233, 89, PortSide.BOTTOM)
    diagram.path([rejected, (493.5, 233), (667, 233), (667, 205.5), (712, 205.5)], arrow=True, dashed=True)
    diagram.text(510, 225, "No", size=15, color="muted", weight=500, anchor=TextAnchor.START)

    labeled_connector(diagram, (932, 116.5), (987, 116.5), "records")
    box_label(diagram, 1008, 89, 178, 55, "Store", fill="leaf_fill", stroke="leaf", size=18)
    return diagram


def shapes(theme: DiagramTheme) -> Diagram:
    """A field list, a batch, a split, and a note about one branch."""
    diagram = Diagram("Record delivery", width=1220, height=267, theme=theme)
    list_node(diagram, 34, 34, 233, "Record", ["id: string", "status: enum", "score: float"])
    diagram.line(288, 99.5, 356, 99.5, arrow=True)
    repeated_stack(diagram, 377, 55, 233, "Documents", "24 per batch")

    diagram.line(644, 99.5, 678, 99.5)
    junction(diagram, 686, 99.5)
    diagram.line(686, 99.5, 788, 99.5, arrow=True)
    box_label(diagram, 809, 72, 233, 55, "Publish", fill="leaf_fill", stroke="leaf", size=18)

    diagram.path([(686, 99.5), (686, 199), (788, 199)], arrow=True)
    box_label(diagram, 809, 171.5, 233, 55, "Cache", size=18)
    annotation_callout(diagram, 1097, 191, ["Expires after", "15 minutes"], (1042, 199))
    return diagram


def lanes(theme: DiagramTheme) -> Diagram:
    """Two lanes of work inside one ownership boundary."""
    diagram = Diagram("Delivery", width=1220, height=356, theme=theme)
    boundary_frame(diagram, 34, 34, 1152, 288, "Private network")
    swimlane(diagram, 55, 89, 1110, 89, "Extract")
    swimlane(diagram, 55, 199, 1110, 89, "Publish")

    extract = ((233, 178, "Parse"), (500, 178, "Normalize"), (767, 178, "Score"))
    for x, width, label in extract:
        box_label(diagram, x, 106, width, 55, label, fill="parent_fill", stroke="parent", size=18)
    labeled_connector(diagram, (432, 133.5), (479, 133.5), "records")
    diagram.line(699, 133.5, 746, 133.5, arrow=True)

    publish = ((233, 233, "Render report"), (555, 178, "Sign"), (822, 178, "Publish"))
    for x, width, label in publish:
        box_label(diagram, x, 216, width, 55, label, fill="leaf_fill", stroke="leaf", size=18)
    diagram.line(487, 243.5, 534, 243.5, arrow=True)
    diagram.line(754, 243.5, 801, 243.5, arrow=True)
    diagram.path([(966, 133.5), (1042, 133.5), (1042, 188), (349, 188), (349, 208)], arrow=True)
    return diagram


def icons(theme: DiagramTheme) -> Diagram:
    """Four sources, each named by an icon as well as by its title."""
    diagram = Diagram("Sources", width=1220, height=301, theme=theme)
    sources = (
        (34, 34, "Warehouse tables", "Nightly extract", LucideIcon.DATABASE, NodeRole.ROOT),
        (682, 34, "Spreadsheets", "Uploaded by analysts", LucideIcon.TABLE_2, NodeRole.ROOT),
        (34, 178, "Runbooks", "Narrative context", LucideIcon.NOTEBOOK_TEXT, NodeRole.PARENT),
        (682, 178, "Checked record", "Checks passed", LucideIcon.FILE_CHECK_2, NodeRole.LEAF),
    )
    for x, y, title, description, icon, role in sources:
        icon_node(diagram, x, y, 504, title, description, icon=icon, role=role)
    return diagram


def branded(theme: DiagramTheme) -> Diagram:
    """The two-node diagram under a palette override chosen for the theme."""
    diagram = Diagram("Ingest", width=987, height=144, theme=theme, palette=BRAND_PALETTES[theme])
    title_node(diagram, 89, 44.5, 288, "Source", role=NodeRole.ROOT)
    title_node(diagram, 610, 44.5, 288, "Store", role=NodeRole.LEAF)
    diagram.line(398, 72, 589, 72, arrow=True)
    return diagram


BOLD_GRADIENTS = {
    DiagramTheme.LIGHT: {
        "canvas": ("#fdf6ec", "#eef7f1"),
        "fill": ("#fff5e5", "#eaf7f0"),
        "edge": ("#e88700", "#087d52"),
    },
    DiagramTheme.DARK: {
        "canvas": ("#1a1205", "#04160e"),
        "fill": ("#2f2410", "#0f2b1f"),
        "edge": ("#f5a524", "#3ddc97"),
    },
}


def bold_nodes(theme: DiagramTheme) -> Diagram:
    """Heavier borders and an orange-to-green gradient, over a gradient canvas."""
    stops = BOLD_GRADIENTS[theme]
    diagram = Diagram(
        "Ingest",
        width=1220,
        height=144,
        theme=theme,
        stroke_width=3,
        borders=True,
        background=stops["canvas"],
    )
    warm = diagram.gradient("warm-fill", *stops["fill"])
    bold = diagram.gradient("bold-edge", *stops["edge"], x2=1, y2=0)
    title_node(diagram, 34, 44.5, 288, "Source", role=NodeRole.ROOT)
    centered_node(
        diagram,
        466,
        27.5,
        288,
        "Transform",
        "Normalize the input",
        role=NodeRole.PARENT,
        fill=warm,
        stroke=bold,
        stroke_width=5,
    )
    title_node(diagram, 898, 44.5, 288, "Store", role=NodeRole.LEAF)
    diagram.line(343, 72, 445, 72, arrow=True)
    diagram.line(775, 72, 877, 72, arrow=True)
    return diagram


def framed(theme: DiagramTheme) -> Diagram:
    """A gradient outline on the canvas edge, inset so its full weight shows."""
    stops = BOLD_GRADIENTS[theme]
    diagram = Diagram("Ingest", width=466, height=144, theme=theme, background=stops["canvas"])
    edge = diagram.gradient("edge", *stops["edge"], x2=1, y2=0)
    title_node(diagram, 89, 44.5, 288, "Source", role=NodeRole.ROOT)
    diagram.frame(edge, width=6, radius=21)
    return diagram


def custom_element(theme: DiagramTheme) -> Diagram:
    """A shape the component library does not draw, appended directly."""
    diagram = Diagram("Queue depth", width=987, height=144, theme=theme)
    title_node(diagram, 89, 44.5, 233, "Producer", role=NodeRole.ROOT)
    diagram.append(
        svg_element(
            "ellipse",
            cx=493.5,
            cy=72,
            rx=89,
            ry=55,
            fill=diagram.color("parent_fill"),
            stroke=diagram.color("parent"),
            stroke_width=2,
        )
    )
    diagram.text(493.5, 79, "Queue", size=21, weight=550)
    title_node(diagram, 665, 44.5, 233, "Consumer", role=NodeRole.LEAF)
    diagram.line(343, 72, 391, 72, arrow=True)
    diagram.line(596, 72, 644, 72, arrow=True)
    return diagram


EXAMPLES: dict[str, Callable[[DiagramTheme], Diagram]] = {
    "one-node": one_node,
    "two-nodes": two_nodes,
    "three-roles": three_roles,
    "with-legend": with_legend,
    "grouped": grouped,
    "branching": branching,
    "shapes": shapes,
    "lanes": lanes,
    "icons": icons,
    "branded": branded,
    "bold-nodes": bold_nodes,
    "framed": framed,
    "custom-element": custom_element,
}


@click.command(help="Render the documentation's sample diagrams in both themes.")
@click.option(
    "--output",
    type=click.Path(path_type=Path, file_okay=False),
    default=Path("docs/source/_static/diagrams"),
    show_default=True,
    help="Destination directory; existing files are replaced.",
)
def main(output: Path) -> None:
    for name, build in EXAMPLES.items():
        for theme in DiagramTheme:
            build(theme).save(output / f"{name}-{theme.value}.svg")
        click.echo(f"Rendered {name}")


if __name__ == "__main__":
    main()
