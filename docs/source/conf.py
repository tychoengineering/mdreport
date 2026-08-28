"""Sphinx configuration for the mdreport documentation.

The package is imported by autodoc rather than read from source, so the docs must be
built in an environment where `mdreport` is installed — `uv run manage.py docs` does
that. There is no `sys.path` manipulation here on purpose (style-guide.md §3).
"""

from __future__ import annotations

from mdreport import __version__

# -- Project information -----------------------------------------------------

project = "Markdown Report"
copyright = "Tycho Engineering, MIT License"
author = "Tycho Engineering"
release = __version__
version = __version__

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx_copybutton",
    "myst_parser",
    "sphinx_llm.txt",
]

# sphinx-llm: project blurb for the llms.txt sitemap. Without this the extension
# falls back to scraping the first content line of index.
llms_txt_description = "Build Markdown reports with Python."

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autosummary_generate = True
autosummary_imported_members = False

# Napoleon settings for the Google-style docstrings the package uses.
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
# Render an `Attributes:` section as a field list on the class rather than as
# separate attribute directives, which would collide with the ones autodoc emits
# for the same dataclass fields under `undoc-members`.
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_attr_annotations = True

# Autodoc settings.
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    "exclude-members": "__weakref__",
    "show-inheritance": False,
}
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"

# Every public name is re-exported from the top-level package, so document it under
# `mdreport.Thing` rather than the module it happens to live in.
add_module_names = False

toc_object_entries = True
toc_object_entries_show_parents = "hide"

# MyST parser settings — the user guide pages are Markdown.
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_admonition",
    "html_image",
    "smartquotes",
]
myst_heading_anchors = 4
myst_url_schemes = ["http", "https", "mailto"]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "polars": ("https://docs.pola.rs/api/python/stable", None),
}

pygments_style = "monokai"

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_book_theme"
html_title = "Markdown Report"
html_short_title = "mdreport"
html_static_path = ["_static"]
html_show_sourcelink = False
html_baseurl = "https://mdreport.tycho.engineering"

html_theme_options = {
    "logo": {"text": "Markdown Report"},
    "show_toc_level": 3,
    # pydata-sphinx-theme defaults this to ["search-button-field"], which puts a
    # second search box in the header on top of the sidebar one. The sidebar field
    # and the Ctrl+K dialog are enough.
    "navbar_persistent": [],
    # sphinx-book-theme (pydata-based) uses these instead of pygments_style
    "pygments_light_style": "xcode",
    "pygments_dark_style": "monokai",
}

html_css_files = ["custom.css"]

# Copybutton configuration
copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True
