from __future__ import annotations

import pytest

from mdreport import HeadingAnchorStyle, MarkdownReport, TableOfContents, slugify


def test_contents_links_every_heading_to_its_anchor() -> None:
    report = MarkdownReport().table_of_contents().title("Q3 Review").heading("Revenue").heading("By region", level=3)

    rendered_report = report.render()

    assert rendered_report.startswith(
        """- [Q3 Review](#q3-review)
  - [Revenue](#revenue)
    - [By region](#by-region)
"""
    )


def test_repeated_heading_text_links_to_numbered_anchors() -> None:
    report = MarkdownReport().table_of_contents().heading("Findings").heading("Findings")

    rendered_report = report.render()

    assert rendered_report.startswith("- [Findings](#findings)\n- [Findings](#findings-1)\n")


def test_written_anchors_match_the_links_the_contents_generates() -> None:
    """The anchor a heading carries and the link pointing at it are computed
    separately — from the resolved token stream and from the parsed document —
    so repeated headings are where the two would drift apart."""
    report = (
        MarkdownReport(anchor_style=HeadingAnchorStyle.HTML).table_of_contents().heading("Findings").heading("Findings")
    )

    rendered_report = report.render()

    for slug in ("findings", "findings-1"):
        assert f'<a id="{slug}"></a>' in rendered_report
        assert f"(#{slug})" in rendered_report


def test_anchor_slug_drops_inline_markup_and_punctuation() -> None:
    report = MarkdownReport().table_of_contents().heading("Costs & `overhead`: 2024!")

    assert "(#costs--overhead-2024)" in report.render()


def test_anchor_slug_keeps_unicode_letters_and_digits() -> None:
    assert slugify("Résumé für Ω 2024") == "résumé-für-ω-2024"


def test_headings_without_sluggable_text_fall_back_to_numbered_sections() -> None:
    report = MarkdownReport().table_of_contents().heading("!?").heading("...")

    rendered_report = report.render()

    assert "(#section)" in rendered_report
    assert "(#section-1)" in rendered_report


def test_contents_entry_unwraps_a_link_inside_the_heading() -> None:
    report = MarkdownReport().table_of_contents().heading("See [the docs](https://example.com)")

    assert "- [See the docs](#see-the-docs)" in report.render()


def test_contents_scope_skips_levels_without_shifting_the_anchors() -> None:
    report = (
        MarkdownReport()
        .title("Report")
        .table_of_contents(start_level=2, depth=1)
        .heading("Report")
        .heading("Detail", level=3)
    )

    rendered_report = report.render()

    assert "- [Report](#report-1)\n" in rendered_report
    assert "[Detail]" not in rendered_report


def test_contents_out_of_scope_everywhere_leaves_no_placeholder() -> None:
    report = MarkdownReport().table_of_contents(start_level=6).heading("Revenue")

    assert report.render() == "## Revenue\n\n"


@pytest.mark.parametrize(("start_level", "depth"), [(0, 6), (7, 6), (1, 0), (1, -1)])
def test_contents_rejects_a_scope_no_heading_can_fall_in(start_level: int, depth: int) -> None:
    with pytest.raises(ValueError, match="Table of contents"):
        TableOfContents(start_level=start_level, depth=depth)


def test_unlinked_contents_renders_entries_as_plain_text() -> None:
    report = MarkdownReport().table_of_contents(is_linked=False).heading("Revenue")

    assert report.render().startswith("- Revenue\n")


def test_html_anchor_style_writes_an_anchor_element_into_each_heading() -> None:
    report = MarkdownReport(anchor_style=HeadingAnchorStyle.HTML).heading("Cost of Goods")

    assert report.render() == '## <a id="cost-of-goods"></a>Cost of Goods\n\n'


def test_attribute_anchor_style_writes_the_slug_after_each_heading() -> None:
    report = MarkdownReport(anchor_style=HeadingAnchorStyle.ATTRIBUTE).heading("Cost of Goods")

    assert report.render() == "## Cost of Goods {#cost-of-goods}\n\n"


def test_anchors_skip_headings_inside_a_code_block() -> None:
    report = MarkdownReport(anchor_style=HeadingAnchorStyle.HTML).code_block("# Not a heading", language="markdown")

    assert "<a id=" not in report.render()


def test_a_copy_keeps_the_anchor_style() -> None:
    base = MarkdownReport(anchor_style=HeadingAnchorStyle.ATTRIBUTE).heading("Revenue")

    assert base.copy().render() == base.render()


def test_rendering_twice_produces_the_same_anchors() -> None:
    report = (
        MarkdownReport(anchor_style=HeadingAnchorStyle.HTML).table_of_contents().heading("Findings").heading("Findings")
    )

    assert report.render() == report.render()
