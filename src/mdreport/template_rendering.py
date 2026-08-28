from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from jinja2 import Template

from .markdown_tokens import NestedListItem

__all__ = ["render_template", "render_template_items"]


def render_template(text: str, params: Mapping[str, Any] | None = None) -> str:
    """Render a short Jinja template when parameters are supplied."""
    if params is None:
        return text
    return cast(str, Template(text).render(**params))


def render_template_items(
    items: Sequence[NestedListItem],
    params: Mapping[str, Any] | None = None,
) -> list[NestedListItem]:
    """Render templates across list items, descending into nested sublists."""
    rendered_items: list[NestedListItem] = []
    for item in items:
        if isinstance(item, list):
            rendered_items.append(render_template_items(item, params))
        else:
            rendered_items.append(render_template(str(item), params))
    return rendered_items
