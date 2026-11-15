# spherex_psb project instructions

Research project: use SPHEREx spectrophotometric data to study the star formation
history and stellar populations of low-redshift post-starburst / fast-quenching
galaxies, focusing on NIR/MIR continuum and absorption features sensitive to
AGB/TP-AGB stars.

## Project rules (in addition to the global ~/.claude/CLAUDE.md)

- Language: English for all code, docs, commits, and logs.
- Branching: never commit on `main`; use `feature/<topic>` branches and do not merge
  without explicit permission.
- Package management: `uv` only.
- Spec: `docs/SPEC.md` is the source of truth for architecture and scope.
- Lessons: record mistakes and rationale in `docs/lessons.md`; read it at session start.
- Tasks: track work in `docs/todo.md`; add a review section when a task completes.
- SPHEREx knowledge: the documentation site in `docs/` (entry `docs/index.md`) is the project's living
  record of SPHEREx data usage. Its pages `primer.md`, `data_access.md` and `reduction_analysis.md`
  replace the former `docs/spherex_data_guide.md`; `sed_extraction.md` and `spectral_indices.md` record
  the analysis work. `docs/references/` holds per-source notes (official pages, papers, tools),
  `docs/reports/` the checkpoint reports and task specs. Update the pages, not memory, when something
  new is learned about SPHEREx; cite the source and mark measured numbers as measured.
- Documentation standard (2026-11-14): for science and technical HTML documentation, including every
  GitHub Pages site built from this repository, use note-style and only note-style, as defined in
  `docs/html_documentation_guide.md` (the `note-style` skill at
  `/Users/shuang/Dropbox/work/project/vibe/guangtou_vibe/skills/note-style`, read it before changing
  the documentation setup). Its first implementation is Sphinx, MyST Markdown and customised Furo:
  sources stay ordinary `.md` files, the shared assets `docs/_static/note_style.css`,
  `docs/_static/note_style_theme.js`, `docs/_templates/base.html`, `docs/mathjax_config.js`, the
  bundled fonts under `docs/_static/fonts/` and the bundled MathJax under `docs/_static/vendor/` are
  copied from the skill's starter and are not edited here (project additions go in `docs/_static/spherex_psb.css`). Do not introduce another site
  generator, theme or CDN-hosted math runtime. Record the adopted guide version, publisher versions and
  project-specific decisions in `docs/SPEC.md`; preserve source provenance, stable document identifiers
  and working links during conversion. Build both versions with `bash scripts/build_docs.sh` (strict,
  from empty output folders) before committing documentation changes; the public site deploys to
  GitHub Pages from `main`.
- Publication scope (2026-11-15): project documents are never part of the published site. The
  specification, task list, lessons, task specifications, the copied rule book, notes on private
  material (such as the student's repository) and any similar project-management document are listed
  in `INTERNAL_DOCUMENTS` in `docs/conf.py`. The default build (`docs/_build/html`, what GitHub Pages
  publishes) excludes them; `sphinx-build -t internal` builds them into `docs/_build/internal` for the
  owner's review, under an "Internal" navigation section and with a banner on each page. Add every new
  document of that kind to the list when it is created. Public pages must not link to internal ones
  (the strict public build fails if they do).
- Links in published pages (2026-11-15): never print a web address as text. Write a hyperlink with
  descriptive text, `[IRSA Quick Release overview](https://...)`, which the theme shows in the link
  colour. Service endpoints, URL templates with placeholders, example request URLs, install commands
  and quoted source code stay as inline code.
- Always rely on official IRSA / IPAC resources and peer-reviewed or arXiv papers for
  SPHEREx facts. Do not use or consult third-party SPHEREx GitHub tools unless the
  user explicitly asks.
- The external skill `spherex-irsa-access` lives at
  `/Users/shuang/Dropbox/work/project/vibe/guangtou_vibe/skills/spherex-irsa-access`
  and should be kept consistent with the `data_access.md` and `reduction_analysis.md` pages.
- Never estimate numbers about SPHEREx performance; quote the source (paper section,
  documentation page) or measure from data.
