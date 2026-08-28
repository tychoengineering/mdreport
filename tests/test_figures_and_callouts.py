from __future__ import annotations

import base64
from pathlib import Path

import pytest

from mdreport import (
    Callout,
    CalloutKind,
    DeferredReportBlock,
    Figure,
    FigureEmbeddingError,
    MarkdownReport,
    ReportBlock,
)


def test_callout_renders_a_portable_titled_block_quote() -> None:
    report = MarkdownReport().callout(
        "Numbers for **{{ period }}** are provisional.\n\n- Check source\n- Check owner",
        kind=CalloutKind.WARNING,
        params={"period": "Q3"},
    )

    assert (
        report.render()
        == "> **Warning**\n>\n> Numbers for **Q3** are provisional.\n>\n> - Check source\n> - Check owner\n\n"
    )


def test_callout_accepts_a_templated_custom_title() -> None:
    report = MarkdownReport().callout(
        "All checks passed.",
        kind=CalloutKind.TIP,
        title="{{ system }} status",
        params={"system": "Pipeline"},
    )

    assert report.render() == "> **Pipeline status**\n>\n> All checks passed.\n\n"


def test_figure_captions_are_numbered_in_document_order() -> None:
    report = (
        MarkdownReport()
        .figure(
            "charts/cost.png",
            alt_text="Cost by region",
            caption="Quarterly cost.",
        )
        .figure(
            "charts/revenue.png",
            alt_text="Revenue by region",
            caption="Quarterly **revenue**.",
        )
    )

    assert (
        report.render()
        == """![Cost by region](charts/cost.png)

*Figure 1: Quarterly cost.*

![Revenue by region](charts/revenue.png)

*Figure 2: Quarterly **revenue**.*

"""
    )


def test_figure_templates_source_alt_text_and_caption() -> None:
    report = MarkdownReport().figure(
        "charts/{{ name }} chart.png",
        alt_text="{{ name }} by region",
        caption="Results for {{ period }}.",
        params={"name": "Revenue", "period": "Q3"},
    )

    assert report.render() == "![Revenue by region](<charts/Revenue chart.png>)\n\n*Figure 1: Results for Q3.*\n\n"


def test_figure_without_a_caption_renders_only_its_image() -> None:
    report = MarkdownReport().figure(
        "chart.png",
        alt_text="A closing ] bracket",
    )

    assert report.render() == "![A closing \\] bracket](chart.png)\n\n"


def test_raster_figure_can_be_embedded_as_a_base64_data_url(tmp_path: Path) -> None:
    image_bytes = b"not a complete png, but stable bytes for serialization"
    image_path = tmp_path / "pixel.png"
    image_path.write_bytes(image_bytes)

    rendered_report = (
        MarkdownReport()
        .figure(
            image_path,
            alt_text="Pixel",
            is_embedded=True,
        )
        .render()
    )

    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    assert rendered_report == f"![Pixel](data:image/png;base64,{encoded_image})\n\n"


def test_svg_figure_can_be_inserted_as_inline_markup(tmp_path: Path) -> None:
    svg_path = tmp_path / "chart.svg"
    svg_path.write_text(
        '<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>\n',
        encoding="utf-8",
    )

    rendered_report = (
        MarkdownReport()
        .figure(
            svg_path,
            alt_text='Revenue "chart" & trend',
            caption="Revenue trend.",
            is_embedded=True,
        )
        .render()
    )

    assert (
        rendered_report
        == """<div role="img" aria-label="Revenue &quot;chart&quot; &amp; trend">
<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>
</div>

*Figure 1: Revenue trend.*

"""
    )


def test_an_existing_data_url_remains_embedded() -> None:
    data_url = "data:image/png;base64,cGl4ZWw="

    assert MarkdownReport().figure(data_url, alt_text="Pixel", is_embedded=True).render() == f"![Pixel]({data_url})\n\n"


@pytest.mark.parametrize("source", ["https://example.com/chart.png", "missing.png"])
def test_embedding_requires_an_existing_local_image(source: str) -> None:
    report = MarkdownReport().figure(source, alt_text="Chart", is_embedded=True)

    with pytest.raises(FigureEmbeddingError, match="existing local file"):
        report.render()


def test_one_figure_instance_cannot_occupy_two_document_positions() -> None:
    figure = Figure("chart.png", alt_text="Chart")
    report = MarkdownReport().append(figure).append(figure)

    with pytest.raises(ValueError, match="same Figure instance"):
        report.render()


def test_figures_survive_report_copying_and_repeated_rendering() -> None:
    base = MarkdownReport().figure(
        "one.png",
        alt_text="One",
        caption="First.",
    )
    duplicate = base.copy().figure(
        "two.png",
        alt_text="Two",
        caption="Second.",
    )

    assert "Figure 2" not in base.render()
    assert "*Figure 2: Second.*" in duplicate.render()
    assert duplicate.render() == duplicate.render()


def test_new_blocks_satisfy_the_extension_protocols() -> None:
    assert isinstance(Callout("Note"), ReportBlock)
    assert isinstance(Figure("chart.png", alt_text="Chart"), DeferredReportBlock)
