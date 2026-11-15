"""Sphinx configuration: note-style profile (Sphinx, MyST Markdown, customised Furo)."""

project = "spherex_psb"
copyright = "2026, the spherex_psb project"
extensions = ["myst_parser", "sphinx.ext.mathjax", "sphinx.ext.githubpages", "sphinx_design"]
source_suffix = {".md": "markdown"}
root_doc = "index"
language = "en"
exclude_patterns = ["_build", "references/sources/**", "figures/**", "Thumbs.db", ".DS_Store"]

# Project-management pages (specification, task list, lessons, task specs, the copied rule book) and
# notes on private material are for the owner's review only. The default build, which GitHub Pages
# publishes, leaves them out; `sphinx-build -t internal` adds them under an "Internal" navigation
# section with a banner on each page (scripts/build_docs.sh builds both versions).
INTERNAL_DOCUMENTS = [
    "SPEC",
    "todo",
    "lessons",
    "html_documentation_guide",
    "reports/sed_demo_task",
    "references/studies/photometry_study_2026-11",
]
INTERNAL_NAVIGATION_TITLES = {
    "SPEC": "Specification",
    "todo": "To do",
    "lessons": "Lessons",
    "html_documentation_guide": "note-style rule book",
    "reports/sed_demo_task": "SED demo task",
    "references/studies/photometry_study_2026-11": "Photometry study (2026-11)",
}
internal_build = tags.has("internal")  # noqa: F821 (Sphinx provides `tags` to conf.py)
if not internal_build:
    exclude_patterns += [f"{name}.md" for name in INTERNAL_DOCUMENTS]
nitpicky = True
myst_enable_extensions = ["dollarmath", "colon_fence"]
myst_heading_anchors = 4
# Figures keep the explicit numbers of the analysis reports (figure 1-8 of the SED demonstration,
# made by the scripts of the same name), so Sphinx does not add its own figure numbers.
numfig = False
mathjax_path = "vendor/mathjax/tex-mml-chtml.js"
mathjax_config_path = "mathjax_config.js"

html_theme = "furo"
html_title = "SPHEREx notes for the post-starburst project"
html_short_title = "spherex_psb"
html_baseurl = "https://dr-guangtou.github.io/spherex_psb/"
html_static_path = ["_static"]
templates_path = ["_templates"]
html_css_files = ["note_style.css", "spherex_psb.css"]
html_js_files = ["note_style_theme.js"]
html_theme_options = {
    "top_of_page_buttons": [],
    "source_repository": "https://github.com/dr-guangtou/spherex_psb",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "font-stack": (
            '"Source Sans 3", "Source Han Sans SC", "Noto Sans CJK SC", '
            '"PingFang SC", "Microsoft YaHei", sans-serif'
        ),
        "font-stack--monospace": ('"Source Code Pro", "SFMono-Regular", Consolas, "PingFang SC", monospace'),
        "color-brand-primary": "#236b69",
        "color-brand-content": "#236b69",
        "color-background-primary": "#fafaf8",
        "color-background-secondary": "#f0f1ee",
        "color-foreground-primary": "#262d31",
    },
    "dark_css_variables": {
        "color-brand-primary": "#83b5b2",
        "color-brand-content": "#83b5b2",
        "color-background-primary": "#171b20",
        "color-background-secondary": "#1d2329",
        "color-foreground-primary": "#dce1e5",
        "color-foreground-secondary": "#b0bac2",
    },
}


INTERNAL_BANNER = """
:::{admonition} Internal page
:class: warning
Built only for local review (`sphinx-build -t internal`). It is not part of the published site.
:::
"""


def add_internal_pages(app, docname, source):
    """In the internal build, list the internal pages in the navigation and mark each one."""
    if not internal_build:
        return
    if docname == "index":
        entries = "\n".join(f"{INTERNAL_NAVIGATION_TITLES[name]} <{name}>" for name in INTERNAL_DOCUMENTS)
        source[0] += f"\n\n```{{toctree}}\n:hidden:\n:caption: Internal\n\n{entries}\n```\n"
    elif docname in INTERNAL_DOCUMENTS:
        lines = source[0].split("\n")
        title_index = next(i for i, line in enumerate(lines) if line.startswith("# "))
        lines.insert(title_index + 1, INTERNAL_BANNER)
        source[0] = "\n".join(lines)


def setup(app):
    app.connect("source-read", add_internal_pages)
