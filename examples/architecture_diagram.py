#!/usr/bin/env -S uv run
"""Render a full system architecture diagram with the mdreport diagram API.

The diagram is one composed picture rather than a component sampler: documents
are collected, validated, enriched, and then extracted and published inside a
private network. It exercises most of the library — icon nodes, group panels, a
decision with labeled branches, a field list, a repeated stack, swimlanes with
ports and a junction, an ownership boundary, an annotation callout, and a
legend keyed to the marks actually used.

Every coordinate is explicit, and every one of them is a step on the library's
golden-ratio scale: an 89-unit margin, 288-unit nodes, 144-unit gaps, and bands
of 55, 89, 144, and 233. Nothing here measures text or resolves overlaps, so the
output is byte-identical between runs. The first run fetches three Lucide icons
(a few KB) and caches them under ~/.cache/mdreport; later runs are offline.
Writing the report alongside the SVG embeds the same diagram as a numbered
figure.

Usage:
    uv run examples/architecture_diagram.py                                  # dark, on black
    uv run examples/architecture_diagram.py --theme light
    uv run examples/architecture_diagram.py --output /tmp/architecture.svg
    uv run examples/architecture_diagram.py --background '#ffffff'
    uv run examples/architecture_diagram.py --report data/architecture.md   # also write Markdown
"""

from __future__ import annotations

import re
from pathlib import Path

import click

from mdreport import (
    Diagram,
    DiagramTheme,
    LucideIcon,
    MarkdownReport,
    NodeRole,
    PortSide,
    TextAnchor,
    annotation_callout,
    arrow_key,
    boundary_frame,
    box_label,
    color_key,
    decision_node,
    group_panel,
    icon_node,
    junction,
    labeled_connector,
    legend_header,
    list_node,
    node_port,
    repeated_stack,
    swimlane,
)

WIDTH = 1440
HEIGHT = 1020
TITLE = "Report publishing platform"

# Stage bands. A panel reserves 55 units above its children and 34 below, and
# the stages are separated by the 34-unit gap the connectors cross.
COLLECT_Y = 123
STAGE_Y = 335
STAGE_HEIGHT = 233
NETWORK_Y = 602


def collect_stage(diagram: Diagram) -> None:
    """Three sources feeding one collection step, across the full width."""
    group_panel(
        diagram,
        89,
        COLLECT_Y,
        1262,
        178,
        "1. Collect",
        "Every source lands as an immutable document; nothing is edited in place.",
    )
    sources = (
        (144, "Warehouse tables", "Nightly extract", LucideIcon.DATABASE),
        (576, "Spreadsheets", "Uploaded by analysts", LucideIcon.TABLE_2),
        (1008, "Runbooks", "Narrative context", LucideIcon.NOTEBOOK_TEXT),
    )
    for x, title, description, icon in sources:
        icon_node(diagram, x, 178, 288, title, description, icon=icon, role=NodeRole.ROOT)
    diagram.line(453, 222.5, 555, 222.5, arrow=True)
    diagram.line(885, 222.5, 987, 222.5, arrow=True)


def validate_stage(diagram: Diagram) -> None:
    """A schema decision with an accepted path and a dashed quarantine path."""
    group_panel(diagram, 89, STAGE_Y, 586, STAGE_HEIGHT, "2. Validate")
    decision_node(diagram, 110, 390, 178, 89, "Schema ok?")
    box_label(diagram, 377, 407, 178, 55, "Accept", fill="leaf_fill", stroke="leaf", size=18, weight=500)
    box_label(diagram, 377, 479, 178, 55, "Quarantine", size=18, weight=500)

    # Accept shares the decision's centerline, so the accepted path stays straight
    # and only the quarantine path has to turn.
    accepted = node_port(110, 390, 178, 89, PortSide.RIGHT)
    diagram.line(*accepted, 356, 434.5, arrow=True)
    diagram.text(300, 426, "Yes", size=15, color="muted", weight=500, anchor=TextAnchor.START)

    rejected = node_port(110, 390, 178, 89, PortSide.BOTTOM)
    diagram.path([rejected, (199, 506.5), (356, 506.5)], arrow=True, dashed=True)
    diagram.text(207, 498, "No", size=15, color="muted", weight=500, anchor=TextAnchor.START)


def enrich_stage(diagram: Diagram) -> None:
    """The accepted record shape, and the batch it is written into."""
    group_panel(diagram, 765, STAGE_Y, 586, STAGE_HEIGHT, "3. Enrich")
    list_node(diagram, 786, 407, 233, "Record", ["id: string", "status: enum"])
    repeated_stack(diagram, 1085, 417.5, 178, "Documents", "24 per batch")
    diagram.line(1040, 462, 1064, 462, arrow=True)


def delivery_network(diagram: Diagram) -> None:
    """Two lanes inside an ownership boundary: extraction, then publication."""
    boundary_frame(diagram, 89, NETWORK_Y, 1262, 288, "Private network")
    swimlane(diagram, 110, 657, 1220, 89, "Extract")
    swimlane(diagram, 110, 767, 1220, 89, "Publish")

    extract = (
        (288, 144, "Parse"),
        (521, 178, "Normalize"),
        (788, 144, "Score"),
    )
    for x, width, label in extract:
        box_label(diagram, x, 674, width, 55, label, fill="parent_fill", stroke="parent", size=18, weight=500)
    labeled_connector(diagram, (453, 701.5), (500, 701.5), "records")
    diagram.line(720, 701.5, 767, 701.5, arrow=True)

    # One junction splits the scored record: cached for reuse, and published.
    scored = node_port(788, 674, 144, 55, PortSide.RIGHT)
    diagram.line(scored[0] + 21, scored[1], 987, 701.5)
    junction(diagram, 995, 701.5)
    diagram.line(995, 701.5, 1054, 701.5, arrow=True)
    box_label(diagram, 1075, 674, 144, 55, "Cache", size=18, weight=500)
    annotation_callout(diagram, 1274, 694, ["Expires after", "15 minutes"], (1219, 701.5))

    publish = (
        (288, 233, "Render report"),
        (610, 144, "Sign"),
        (843, 178, "Publish"),
    )
    for x, width, label in publish:
        box_label(diagram, x, 784, width, 55, label, fill="leaf_fill", stroke="leaf", size=18, weight=500)
    diagram.line(542, 811.5, 589, 811.5, arrow=True)
    diagram.line(775, 811.5, 822, 811.5, arrow=True)
    diagram.path([(995, 701.5), (995, 756), (404, 756), (404, 776)], arrow=True)


def legend(diagram: Diagram) -> None:
    """Keys use the diagram's own marks; color keys are redundant when monochrome."""
    key_y = legend_header(diagram, 89, 924, 1262)
    is_colored = diagram.theme != DiagramTheme.DARK
    if is_colored:
        color_key(diagram, 89, key_y, "Collected input", NodeRole.ROOT)
        color_key(diagram, 322, key_y, "Processing", NodeRole.PARENT)
        color_key(diagram, 555, key_y, "Published output", NodeRole.LEAF)
    arrow_key(diagram, 788 if is_colored else 89, key_y, "Normal flow")
    arrow_key(diagram, 1022 if is_colored else 322, key_y, "Conditional flow", dashed=True)
    junction(diagram, 1256 if is_colored else 610, key_y)
    diagram.text(
        1277 if is_colored else 631,
        key_y + 6,
        "Connected junction",
        size=18,
        weight=400,
        anchor=TextAnchor.START,
    )


def render_architecture(background: str | None = None, *, theme: DiagramTheme = DiagramTheme.DARK) -> Diagram:
    """Compose the four stages, the delivery network, and the legend."""
    diagram = Diagram(TITLE, width=WIDTH, height=HEIGHT, theme=theme, background=background)
    diagram.text(WIDTH / 2, 55, TITLE, size=29, weight=550)
    diagram.text(
        WIDTH / 2,
        89,
        "From raw sources to a signed report, with everything after validation inside the boundary",
        size=18,
        color="muted",
        weight=400,
    )
    collect_stage(diagram)
    validate_stage(diagram)
    enrich_stage(diagram)
    delivery_network(diagram)
    legend(diagram)

    # Stage-to-stage connectors, drawn across the 34-unit gap between panels.
    diagram.line(382, 301, 382, 327, arrow=True)
    diagram.line(1058, 301, 1058, 327, arrow=True)
    diagram.line(382, 568, 382, 594, arrow=True)
    diagram.line(1058, 568, 1058, 594, arrow=True)
    return diagram


@click.command(help="Render the report publishing platform architecture as editable SVG.")
@click.option(
    "--output",
    type=click.Path(path_type=Path, dir_okay=False),
    default=Path("data/architecture.svg"),
    show_default=True,
    help="Destination SVG file; an existing file is replaced.",
)
@click.option(
    "--theme",
    type=click.Choice([theme.value for theme in DiagramTheme]),
    default=DiagramTheme.DARK.value,
    show_default=True,
    help="Visual preset; component geometry and typography are unchanged.",
)
@click.option(
    "--background",
    default="auto",
    show_default=True,
    help="Canvas: auto (theme default), transparent, or a solid #RGB / #RRGGBB color. Quote hex colors.",
)
@click.option(
    "--report",
    type=click.Path(path_type=Path, dir_okay=False),
    default=None,
    help="Also write a Markdown report embedding the diagram as a numbered figure.",
)
def main(output: Path, theme: str, background: str, report: Path | None) -> None:
    if (
        background not in {"auto", "transparent"}
        and re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", background) is None
    ):
        raise click.BadParameter("Use auto, transparent, or a hex color such as '#ffffff'.", param_hint="--background")
    selected_theme = DiagramTheme(theme)
    canvas = None if background in {"auto", "transparent"} else background
    diagram = render_architecture(canvas, theme=selected_theme)
    diagram.save(output)
    click.echo(f"Rendered {output}")

    if report is not None:
        markdown = MarkdownReport()
        markdown.title(TITLE).text(
            "Documents are immutable once collected. Validation decides what enters the private "
            "network, and only signed reports leave it."
        )
        markdown.append(diagram.figure(caption="Report publishing platform, end to end"))
        markdown.save(report)
        click.echo(f"Wrote {report}")


if __name__ == "__main__":
    main()
