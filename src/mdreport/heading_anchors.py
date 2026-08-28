from __future__ import annotations

import copy
import enum
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode

__all__ = [
    "HeadingAnchor",
    "HeadingAnchorStyle",
    "anchor_link_inline",
    "anchored_inline",
    "anchored_tokens",
    "document_anchors",
    "heading_text",
    "slugify",
]


class HeadingAnchorStyle(enum.StrEnum):
    """How a heading's anchor is written into the rendered Markdown.

    ``IMPLICIT`` writes nothing and relies on the anchor the renderer derives
    from the heading text — what GitHub, GitLab, Pandoc, MkDocs, and Docusaurus
    all do, and what ``slugify`` reproduces. ``HTML`` prefixes the heading with
    an ``<a id="...">`` element, for renderers that generate no anchors of their
    own. ``ATTRIBUTE`` appends the ``{#slug}`` attribute Pandoc, kramdown, and
    python-markdown's ``attr_list`` understand; anything else renders it as
    visible text.
    """

    IMPLICIT = "implicit"
    HTML = "html"
    ATTRIBUTE = "attribute"


@dataclass(frozen=True)
class HeadingAnchor:
    """A heading, its level, and the slug that links to it."""

    level: int
    inline: Token
    slug: str


# Everything a slug does not keep: anything that is not a word character, a
# space, or a hyphen. Dropping the rest is what makes a slug safe to write into
# an HTML id attribute or a link destination without escaping.
DISCARDED_SLUG_CHARACTERS = re.compile(r"[^\w\- ]", flags=re.UNICODE)

# The inline tokens that carry a heading's visible words. Emphasis and link
# markup wrap these rather than containing text of their own, so building the
# slug from these alone strips the markup without a second traversal.
TEXT_TOKEN_TYPES = frozenset({"text", "code_inline"})
BREAK_TOKEN_TYPES = frozenset({"softbreak", "hardbreak"})
LINK_TOKEN_TYPES = frozenset({"link_open", "link_close"})

FALLBACK_SLUG = "section"


def slugify(text: str) -> str:
    """Return the anchor slug a heading of this text is linked by.

    Follows the GitHub algorithm — case folded, punctuation dropped, spaces
    turned into hyphens — so a link to the slug resolves on every renderer that
    derives heading anchors the same way, with nothing written into the
    document. Text that slugifies to nothing yields ``section``.
    """
    folded = unicodedata.normalize("NFKC", text).strip().lower()
    slug = DISCARDED_SLUG_CHARACTERS.sub("", folded).replace(" ", "-")
    return slug or FALLBACK_SLUG


def unique_slug(text: str, taken: set[str]) -> str:
    """Return a slug for text that is not in taken, and record it there.

    Repeats are numbered the way GitHub numbers them, so a second "Revenue"
    heading anchors at ``revenue-1``.
    """
    base = slugify(text)
    slug = base
    occurrence = 0
    while slug in taken:
        occurrence += 1
        slug = f"{base}-{occurrence}"
    taken.add(slug)
    return slug


def heading_text(inline: Token) -> str:
    """Return a heading's visible text, with inline markup removed."""
    if inline.children is None:
        return inline.content

    words: list[str] = []
    for child in inline.children:
        if child.type in TEXT_TOKEN_TYPES:
            words.append(child.content)
        elif child.type in BREAK_TOKEN_TYPES:
            words.append(" ")
    return "".join(words)


def document_anchors(document: SyntaxTreeNode) -> list[HeadingAnchor]:
    """Return every heading in the document, in order, with a unique slug.

    Raises:
        ValueError: if a heading node contains no inline token.
    """
    anchors: list[HeadingAnchor] = []
    taken: set[str] = set()

    for node in document.walk():
        if node.type != "heading":
            continue
        inline_node = next((child for child in node.children if child.type == "inline"), None)
        if inline_node is None:
            continue
        if inline_node.token is None:
            raise ValueError("Heading inline node must contain a token")

        anchors.append(
            HeadingAnchor(
                level=int(node.tag.removeprefix("h")),
                inline=copy.deepcopy(inline_node.token),
                slug=unique_slug(heading_text(inline_node.token), taken),
            )
        )
    return anchors


def anchored_tokens(tokens: Sequence[Token], style: HeadingAnchorStyle) -> list[Token]:
    """Return a token stream whose headings carry an explicit anchor.

    Slugs are derived from the stream itself, so they match the ones
    ``document_anchors`` collects from the same headings. The given tokens are
    left unmodified.
    """
    if style is HeadingAnchorStyle.IMPLICIT:
        return list(tokens)

    taken: set[str] = set()
    anchored: list[Token] = []
    is_heading_inline = False

    for token in tokens:
        if is_heading_inline and token.type == "inline":
            slug = unique_slug(heading_text(token), taken)
            anchored.append(anchored_inline(token, slug, style))
            is_heading_inline = False
            continue
        is_heading_inline = token.type == "heading_open"
        anchored.append(token)
    return anchored


def anchored_inline(inline: Token, slug: str, style: HeadingAnchorStyle) -> Token:
    """Return a copy of a heading's inline content carrying its anchor.

    The slug is written unescaped into an HTML attribute under
    ``HeadingAnchorStyle.HTML``; ``slugify`` is what makes that safe, having
    already dropped every character that could close the attribute or the tag.
    """
    anchored = copy.deepcopy(inline)
    children = list(anchored.children or [])

    match style:
        case HeadingAnchorStyle.IMPLICIT:
            return anchored
        case HeadingAnchorStyle.HTML:
            anchor = Token("html_inline", "", 0, content=f'<a id="{slug}"></a>')
            anchored.children = [anchor, *children]
        case HeadingAnchorStyle.ATTRIBUTE:
            attribute = Token("html_inline", "", 0, content=f" {{#{slug}}}")
            anchored.children = [*children, attribute]
    return anchored


def anchor_link_inline(inline: Token, slug: str) -> Token:
    """Return a copy of inline content wrapped in a link to a heading's anchor.

    A link already inside the content is unwrapped, keeping its text: Markdown
    has no nested links, so the link to the heading has to be the one that
    survives.
    """
    linked = copy.deepcopy(inline)
    children = [child for child in (linked.children or []) if child.type not in LINK_TOKEN_TYPES]

    link_open = Token("link_open", "a", 1)
    link_open.attrSet("href", f"#{slug}")
    linked.children = [link_open, *children, Token("link_close", "a", -1)]
    return linked
