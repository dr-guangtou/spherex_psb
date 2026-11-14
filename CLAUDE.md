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
  and working links during conversion. Build with
  `uv run --only-group docs sphinx-build -E -W --keep-going -b html docs docs/_build/html`
  (or `bash scripts/build_docs.sh`) before committing documentation changes; the site deploys to
  GitHub Pages from `main`.
- Always rely on official IRSA / IPAC resources and peer-reviewed or arXiv papers for
  SPHEREx facts. Do not use or consult third-party SPHEREx GitHub tools unless the
  user explicitly asks.
- The external skill `spherex-irsa-access` lives at
  `/Users/shuang/Dropbox/work/project/vibe/guangtou_vibe/skills/spherex-irsa-access`
  and should be kept consistent with the `data_access.md` and `reduction_analysis.md` pages.
- Never estimate numbers about SPHEREx performance; quote the source (paper section,
  documentation page) or measure from data.
