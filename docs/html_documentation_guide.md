% Copied from the note-style skill (`dr-guangtou.science/skills/note-style/references/note_style_guide.md`, rule book version 0.6, 2026-11-15) as the skill's portable adoption instruction asks. The project-specific decisions are recorded in [the specification](SPEC.md#9-documentation-system-2026-11-14). Links into the skill folder are given as paths inside that folder.

# note-style Rule Book and Style Guide

Version 0.6, reconciled first-conversion fixes and bilingual examples, 2026-11-15.

## Purpose and adoption status

Use this guide across scientific notes, literature summaries, engineering manuals, and other HTML documentation in independent repositories. Convert and verify documents in their source projects before integrating selected publications into a personal website. Each publication should remain usable at its own URL or under a website subdirectory.

`note-style` is the owner's name for this transferable science and technical documentation standard. Its selected first implementation uses Sphinx, ordinary `.md` files through MyST, and customized Furo. The owner requirements and this implementation direction are confirmed. Detailed typography, final font assets, and other proposed refinements remain subject to review using real documents.

## Confirmed owner requirements

- Present serious scientific and engineering content with simple, elegant, restrained styling.
- Support pleasant Chinese, English, and mixed-language reading.
- Provide left-hand project navigation on desktop.
- Start in dark mode and allow readers to select light mode.
- Support LaTeX-style mathematics and small interactive visualizations.
- Keep this standard transferable across future HTML documentation projects.
- Convert existing documentation gradually within its source repository before website integration.
- Develop customized Furo first and retain ordinary Markdown as the source format. Introduce additional dependencies for a concrete document requirement.
- Apply the profile to the website pages designated by the owner in the website specification. Other page types have their own design briefs.

## Publishing tools and visual style

| Term | Responsibility | Examples |
| --- | --- | --- |
| Source format | Stores prose, equations, references, and document structure | Ordinary `.md` files with MyST where needed |
| Publishing engine | Reads source files and generates linked HTML pages | Sphinx |
| Theme | Supplies typography, layout, colors, and navigation presentation | Customized Furo |
| Shared style guide | Defines the reading experience and content conventions across engines | This document |

### Furo and growth

Furo is a Sphinx theme. A typical Markdown-based setup combines Sphinx, the MyST parser, and Furo. Sphinx supplies document structure and builds the publication, while Furo styles its HTML output. [Furo quickstart](https://pradyunsg.me/furo/quickstart/)

Furo describes itself as biased toward smaller documentation sets because its sidebar can present the entire hierarchy. This describes a navigation design preference. The documentation gives no numerical page limit. Evaluate a growing collection by how easily readers find a chapter, understand its place, and move between related topics. [Furo design scope](https://pradyunsg.me/furo/)

Sphinx's table-of-contents trees support hierarchies and document ordering. Substantial project books can be built with Sphinx and styled with Furo. A very broad sidebar can motivate a different navigation arrangement or theme. Furo labels custom sidebar-template overrides as unstable, so include navigation and upgrade checks when using such overrides. [Sphinx document trees](https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html), [Furo sidebar customization](https://pradyunsg.me/furo/customisation/sidebar/)

### Selected first implementation

Build the first profile with Sphinx, MyST, Furo, and Sphinx's MathJax extension. Keep prose in ordinary Markdown and use MyST's additional syntax for document trees, labelled equations, and other scientific-document features.

The owner selected this route to build on Furo's simple appearance, keep the authoring format familiar, and explore its capabilities gradually. Book-oriented publishing is a future consideration. Record package versions and customizations in each source project's specification and lockfile.

Start with Furo's existing navigation and small palette, typography, and theme-default adjustments. Keep custom assets separate from upstream theme files. Check the profile when dependencies are upgraded.

## Proposed organization

Organize the collection around coherent projects and manuals. Each collection should have a defined subject, an overview, navigation, and references appropriate to that subject. Add chapter groups as the material develops into a longer work.

```text
Documentation index
  Euclid studies
    Overview
    Data products
    Data access
    Analysis notes
  SPHEREx studies
    Overview
    Instrument and calibration
    Analysis methods
  MUST spectral simulation studies
    Overview
    Physical model
    Validation and worked examples
  MUST engineering documentation
    Overview
    Concepts and conventions
    Selected engineering notes
```

Keep the current book's navigation on the left. Provide links to its overview and the collection index. Add parts or chapter groups when the material develops distinct subjects. Use a page outline for long pages and collapse secondary navigation on narrow screens.

With independently built books, search normally covers the current build. Collection-wide search needs its own implementation. Record search scope explicitly and test Chinese queries alongside English terms. Cross-book numbered references also need deliberate linking or shared build support.

## Proposed reading and visual conventions

### Typography

- Use Source Sans 3 for Latin body text and Source Code Pro for code. The starter bundles variable-weight WOFF2 files for normal and italic text in Latin and Latin Extended subsets under `docs/_static/fonts/`. These files come from the corresponding `@fontsource-variable` packages at version 5.3.1 under SIL Open Font License 1.1. Preserve their license texts and provenance notice (`assets/starter/docs/_static/fonts/NOTICE.md` in the skill folder). Naming an unavailable font in the stack does not load it; verify that the publication actually serves its font files.
- The owner's preferred Chinese face is XiQueSongTiJF_std. Its web-embedding terms need foundry clarification as described in font integration (`references/font_integration.md` in the skill folder). Chinese text continues to use the configured Chinese-capable system fallbacks. The bundled unicode ranges cover Latin; add relevant licensed subsets when other scripts need a fixed appearance.
- Assess Chinese punctuation, Latin symbols, numerals, bold weights, inline mathematics, and mixed-language headings together before adopting font assets.
- Use relative text sizing and content-driven block heights. Preserve reading and navigation when text is enlarged.
- Keep paragraphs within a comfortable reading column. Allow long technical tables, equations, and figures to use a wider region or their own scroll container when needed.
- Declare the page language and mark substantial passages in another language appropriately. Choose the publication's content language according to its repository instructions. Font support and translation coverage are distinct decisions.

The Source Han families provide Chinese-capable font assets. A font name in a configuration requires a corresponding local or downloadable font asset, or an available system fallback. [Source Han Sans](https://github.com/adobe-fonts/source-han-sans)

### Color and navigation

- Use a neutral charcoal dark palette and a coordinated light palette with readable text, links, code, and interface controls.
- Interpret dark by default as the first-visit appearance. Honor a saved reader choice on subsequent visits.
- Expose an accessible theme control and prevent a flash of the wrong theme during loading.
- Keep project navigation and active-page indicators consistent across chapters.
- Use visible keyboard focus, meaningful link labels, and an accessible narrow-screen navigation control.
- Preserve the intended colors, units, legends, and contrast of scientific figures in both modes.
- Use decorative styling only when it serves the document's information hierarchy. Keep motion limited to functional feedback and respect reduced-motion preferences.

### Document content

- Give each page a descriptive title and state the question or purpose near the beginning.
- Organize headings by subject and derivation. Let the publisher generate chapter numbers where the publication uses them.
- Explain notation and assumptions before relying on them. Distinguish measured results, external claims, and proposed models in the prose.
- Give scientific figures informative captions, labelled axes, units, and source or generation information. Provide useful alternative text.
- Keep tables machine-readable and label quantities and units in their headers.
- Use references for external claims and stable links or labels for internal references.
- Use callouts consistently. A note adds context, a caution identifies a relevant failure mode, and an engineering status identifies the maturity or revision of the actual record.
- Preserve meaningful requirement identifiers, release identifiers, and source provenance during conversion.

### Overview pages and card grids

A collection overview may present its main chapters as linked cards when that makes navigation clearer. The starter includes `sphinx-design` 0.8.0 in its lockfile and enables `sphinx_design`. Use `::::{grid} 1 1 2 2` for one column on narrow screens and two on wider screens, with nested `:::{grid-item-card}` directives, `:link: document_name`, and `:link-type: doc`. The starter index (`assets/starter/docs/index.md` in the skill folder) provides a complete two-card example.

Keep the title descriptive and the body to one or two sentences. The shared CSS sets `.sd-card-title` to `1.2rem`, weight 600, in the link color, with an underline on hover or focus within the card. Retain natural card height and keyboard-accessible links. Cards are an optional overview pattern; ordinary lists and the project sidebar remain available.

Preserve `font-size-adjust: none` on `.sd-hide-link-text`. Sphinx Design hides redundant card-link text with a zero font size; the article's inherited font-size adjustment made that text visible during integration testing. The targeted reset retains the link's accessible name and the visible card title.

### Tables and static figures

Keep table cells and headers on normal word boundaries. The shared CSS sets `overflow-wrap: normal` and `word-break: normal` on `td`, `th`, and their paragraph children, overriding article-level emergency wrapping. Let wide scientific tables scroll within the publisher's table region when required. Check long identifiers and URLs explicitly; use a deliberate local layout adjustment if a particular table needs one.

Article images use `max-width: 100%` and `height: auto` so a requested figure width remains bounded by the reading column and its aspect ratio is preserved. Retain intrinsic image dimensions where available. Check captions and labels at narrow widths, as an image that fits may still need larger lettering or a simpler composition.

Use one image per MyST figure directive. For two images, use consecutive figure directives with separate captions and labels. A side-by-side composition, when required, needs a deliberately chosen layout or a prepared composite figure. The layout examples (`assets/starter/docs/layout_examples.md` in the skill folder) include an 820-pixel figure and a table for checking the shared rules.

### Code and query examples

Use the `postgresql` Pygments lexer for SQL or ADQL examples containing brace placeholders such as `{minimum_ra}`. In the tested environment, the generic `sql` lexer produces an error token for those braces and fails the warnings-as-errors build. State which values must be substituted. Highlighting is separate from query validation, and braces are not ADQL or SQL parameter syntax.

````markdown
```postgresql
SELECT source_id, ra, dec
FROM example_catalog
WHERE ra BETWEEN {minimum_ra} AND {maximum_ra}
```
````

### Mathematics and interactive figures

- Keep mathematics in editable LaTeX-style source. Label equations that are referenced elsewhere.
- Let the publisher resolve numbered equation and figure references.
- Check the real macro set, long derivations, inline alignment, and Chinese text around mathematics in the rendered output.
- Place each interactive figure beside the explanation it supports. Describe what the controls change and identify its data, units, assumptions, and initial state.
- Provide keyboard-operable controls and meaningful content before interaction. Include a static or textual explanation for printing and cases where the interactive component cannot run.
- Document how data and figures are generated. If computation is required during a build or visit, record its environment and execution path in the source project.

## Copyable authoring examples

### Reusable Furo starter

The note-style starter (`assets/starter/README.md` in the skill folder) provides a working source layout, locked dependencies, palette and typography settings, a dark-first theme integration, and Markdown sample pages. Copy its source files into a new documentation project or merge the relevant files into an existing project.

```text
pyproject.toml
uv.lock
docs/
  conf.py
  index.md
  signal_noise.md
  bilingual_sample.md
  layout_examples.md
  mathjax_config.js
  _static/
    note_style.css
    note_style_theme.js
    note_style_interactive.js
    exposure_counts.svg
    fonts/             (Latin WOFF2 files, licenses, provenance)
    vendor/
  _templates/
    base.html
```

Run these commands from the copied starter directory.

```sh
uv sync --locked
uv run --locked sphinx-build -E -W --keep-going -b html docs _build/html
uv run python -m http.server 8765 --directory _build/html --bind 127.0.0.1
```

Publish the generated `_build/html/` directory together with its assets. The starter bundles its Latin body and code fonts and the MathJax 4.1.3 runtime and math-font assets, all served from its own static publication. Chinese font distribution and Chinese search remain subsequent profile refinements.

The Sphinx configuration enables the MyST parser and math renderer and selects Furo.

```python
extensions = ["myst_parser", "sphinx.ext.mathjax", "sphinx_design"]
source_suffix = {".md": "markdown"}
html_theme = "furo"
```

Furo's normal default follows browser preferences. The starter applies a saved theme or the requested dark initial theme before rendering the article, using a small template override. Its existing theme buttons cycle between dark, light, and system preference. A small event handler preserves usable switching when storage is blocked and synchronizes changes between tabs. Recheck this integration when upgrading Furo.

### Bilingual paragraphs and an interactive figure

The bilingual exposure note (`assets/starter/docs/bilingual_sample.md` in the skill folder) demonstrates paired Chinese and English passages, mixed-language headings, inline and display mathematics, a caption, and a reference table. This paired format is a reading sample; a project's translation coverage remains its own decision. Its Chinese passages use `<span lang="zh-CN">` within Markdown paragraphs so assistive tools can identify their language while MyST processes the inline mathematics and links.

Its figure uses a native fieldset, labels, range inputs, and SVG. The local script updates the curve, selected point, numeric values, and accessible description. Keyboard arrow keys move a slider by its stated step. An announcement follows a committed control change. The initial curve and textual reference table also explain the model when JavaScript is unavailable. Controls become active after initialization.

When adapting the example, change the scientific model and document its units, parameter ranges, assumptions, and reference values together. Keep labels, SVG descriptions, and captions consistent with the new model. Check both themes and narrow screens after the change. The sample's illustrative parameters and fixed axes serve its exposure-time explanation.

### Labelled equation in Markdown

Keep assumptions and notation alongside the equation in the source note.

````markdown
# Signal and noise

Assume independent Poisson signal and background counts and independent
read noise. Let $S$ and $B$ be expected electron counts, $n$ the number
of detector samples, and $r$ the read noise per sample in electrons.

```{math}
:label: eq_signal_noise
\mathrm{SNR} = \frac{S}{\sqrt{S + B + n r^2}}
```

Equation {eq}`eq_signal_noise` applies under these assumptions.
````

Python build dependencies are managed with `uv` under the owner's existing tooling rules. [MyST mathematics](https://myst-parser.readthedocs.io/en/latest/syntax/math.html), [Sphinx mathematics](https://www.sphinx-doc.org/en/master/usage/extensions/math.html), [Furo setup](https://pradyunsg.me/furo/quickstart/)

### Portable adoption instruction

Copy this guide to `docs/html_documentation_guide.md` in a source repository. Add the following instruction to its agent manual and reconcile any existing project-specific rules explicitly.

```text
For science and technical HTML documentation, use note-style as defined
in docs/html_documentation_guide.md. Its first implementation uses
Sphinx, MyST Markdown, and customized Furo.
Record the adopted guide version, publisher, and project-specific decisions
in docs/SPEC.md. Preserve source provenance, stable document identifiers,
and working links during conversion. Build and verify the documentation
inside this repository before integrating its output into the website.
```

Repository-specific instructions continue to govern language, dependencies, release procedures, and the meaning of engineering records. Record any local adaptations so another agent can reproduce the build.

## Gradual conversion workflow

1. Inventory the chosen source project, including document hierarchy, equations, references, assets, existing URLs, and interactive content.
2. Record the intended book boundary and original source of each converted page.
3. Select one representative chapter with mixed-language text, mathematics, a table, code, and a figure. Include a small interactive example when the source material needs one.
4. Render that chapter with Sphinx, MyST, and the customized Furo profile.
5. Review the acceptance checks below. Record concrete changes needed by the profile.
6. Convert one coherent section at a time, preserving technical meaning and identifiers. Map changed paths and provide redirects where existing published URLs need them.
7. Build and review the complete project publication with its search index and assets. Use `-E -W --keep-going` for the delivery or commit gate, so Sphinx re-reads every source file and re-emits its warnings. An incremental build is useful during editing but is insufficient for that gate.
8. Integrate the verified output into the website when its content is ready for publication. Recheck links and assets at the final subdirectory URL.

## Acceptance checks for each converted publication

| Check | Passing result |
| --- | --- |
| Source and build | A fresh `-E -W --keep-going` build from the recorded environment generates the expected chapters and assets without warnings. |
| Navigation | Readers can identify the current chapter, find related chapters, and return to the book overview. |
| Theme | A fresh visit starts dark, switching works, and a saved choice is honored when storage is available. |
| Languages and fonts | Bundled Latin font files load from the publication; Chinese and English text, punctuation, headings, and code remain readable together. |
| Search | Representative Chinese and English queries find the intended pages within the documented search scope. |
| Mathematics | Real macros render and labelled references resolve to the intended equations. |
| Content | Figures, tables, references, identifiers, and revision information retain their meaning. |
| Interaction | Controls work with keyboard and pointer input, and the figure's assumptions and initial state are clear. |
| Narrow layout and zoom | Text and controls remain usable; table words retain normal boundaries and figures fit without distortion when the viewport narrows or text is enlarged. |
| Portability | The publication and assets work from its intended standalone URL and website subdirectory. |
| Verification record | The review records the browsers actually tested, tool versions, failures, and remaining limitations. |

## Decisions still to make

- Refine Chinese font distribution, palettes, and layout settings after visual comparison. The Latin body and code fonts are settled as Source Sans 3 and Source Code Pro.
- Decide whether individual publications need translated editions, mixed-language pages, or both.
- Define collection-wide search when independently built books are assembled into the website.

Once the prototype resolves these choices, update this guide's version and replace the corresponding proposals with the agreed defaults.
