from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from jinja2 import Template

from .markdown_tokens import NestedListItem

__all__ = ["render_nested_template_items", "render_template", "render_template_items"]


def render_template(text: str, params: Mapping[str, Any] | None = None) -> str:
    """Render a short Jinja template when parameters are supplied."""
    if params is None:
        return text
    return cast(str, Template(text).render(**params))


def render_template_items(
    items: Sequence[object],
    params: Mapping[str, Any] | None = None,
) -> list[str]:
    """Render templates across a flat sequence of list items."""
    return [render_template(str(item), params) for item in items]


def render_nested_template_items(
    items: Sequence[NestedListItem],
    params: Mapping[str, Any] | None = None,
) -> list[NestedListItem]:
    """Render templates throughout a recursively nested list."""
    rendered_items: list[NestedListItem] = []
    for item in items:
        if isinstance(item, list):
            rendered_items.append(render_nested_template_items(item, params))
        else:
            rendered_items.append(render_template(str(item), params))
    return rendered_items
