from __future__ import annotations

import copy
import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, ClassVar, cast

import mdformat.plugins
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererProtocol
from markdown_it.token import Token
from mdformat.renderer import MDRenderer, RenderContext, RenderTreeNode
from mdformat.renderer.typing import Postprocess, Render

__all__ = ["MarkdownParser", "ReportSyntaxExtension", "create_parser"]


def create_markdown_renderer(parser: MarkdownIt) -> RendererProtocol:
    """Create mdformat's Markdown renderer for markdown-it-py."""
    return cast(RendererProtocol, MDRenderer(parser))


def render_report_root(node: RenderTreeNode, context: RenderContext) -> str:
    """Render top-level blocks while preserving explicit line breaks."""
    output = io.StringIO()
    has_block = False
    pending_line_breaks = 0

    for child in node.children:
        if child.type == "report_line_break":
            pending_line_breaks += 1
            continue

        rendered_child = child.render(context)
        if not rendered_child:
            continue

        if has_block:
            output.write("\n" * (2 + pending_line_breaks))
        elif pending_line_breaks:
            output.write("\n" * pending_line_breaks)
        output.write(rendered_child)
        has_block = True
        pending_line_breaks = 0

    if has_block:
        output.write("\n" * (1 + pending_line_breaks))
    elif pending_line_breaks:
        output.write("\n" * pending_line_breaks)
    return output.getvalue()


def render_report_raw(node: RenderTreeNode, context: RenderContext) -> str:
    """Render content whose non-Markdown format must be preserved verbatim."""
    return node.content


def render_report_frontmatter(node: RenderTreeNode, context: RenderContext) -> str:
    """Render a YAML metadata node with frontmatter delimiters."""
    output = io.StringIO()
    output.write("---\n")
    output.write(node.content)
    output.write("\n---")
    return output.getvalue()


def render_report_line_break(node: RenderTreeNode, context: RenderContext) -> str:
    """Render nothing because the root renderer handles explicit spacing."""
    return ""


def render_report_horizontal_rule(node: RenderTreeNode, context: RenderContext) -> str:
    """Keep the report's compact thematic-break convention."""
    return "---"


class ReportSyntaxExtension:
    """Provide Markdown renderers for report-specific syntax nodes."""

    RENDERERS: ClassVar[Mapping[str, Render]] = MappingProxyType(
        {
            "root": render_report_root,
            "report_frontmatter": render_report_frontmatter,
            "report_line_break": render_report_line_break,
            "report_raw": render_report_raw,
            "hr": render_report_horizontal_rule,
        }
    )
    POSTPROCESSORS: ClassVar[Mapping[str, Postprocess]] = MappingProxyType({})


@dataclass
class MarkdownParser:
    """Parse and serialize Markdown for one report.

    The environment accumulates the link reference definitions collected while
    parsing, so a reference defined in one block resolves in a later one.
    """

    parser: MarkdownIt
    environment: dict[str, Any] = field(default_factory=dict)

    def parse(self, content: str) -> list[Token]:
        """Parse Markdown text into a block-level token stream."""
        return self.parser.parse(content, self.environment)

    def parse_inline(self, content: str) -> Token:
        """Parse inline Markdown into its container token."""
        tokens = self.parser.parseInline(content, self.environment)
        inline = tokens[0]
        inline.block = True
        return inline

    def render(self, tokens: Sequence[Token]) -> str:
        """Serialize a token stream as Markdown, leaving the environment intact."""
        return cast(
            str,
            self.parser.renderer.render(
                list(tokens),
                self.parser.options,
                copy.deepcopy(self.environment),
            ),
        )


def create_parser() -> MarkdownParser:
    """Create the Markdown parser and serializer a report builds with."""
    parser = MarkdownIt(renderer_cls=create_markdown_renderer)
    parser.options["mdformat"] = {"number": True, "wrap": "keep"}
    parser.options["store_labels"] = True
    parser.options["parser_extension"] = []
    parser.options["codeformatters"] = {}

    table_extension = mdformat.plugins.PARSER_EXTENSIONS["tables"]
    parser.options["parser_extension"].append(table_extension)
    table_extension.update_mdit(parser)
    parser.options["parser_extension"].append(ReportSyntaxExtension)
    return MarkdownParser(parser)
