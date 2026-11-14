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
- SPHEREx knowledge: the documentation site in `docs/` (MkDocs, entry `docs/index.md`) is the
  project's living record of SPHEREx data usage. Its pages `primer.md`, `data_access.md` and
  `reduction_analysis.md` replace the former `docs/spherex_data_guide.md`; `sed_extraction.md`
  and `spectral_indices.md` record the analysis work. `docs/references/` holds per-source notes
  (official pages, papers, tools), `docs/reports/` the checkpoint reports and task specs.
  Update the pages, not memory, when something new is learned about SPHEREx; cite the source
  and mark measured numbers as measured. Build with `uv run --only-group docs mkdocs build --strict`
  before committing documentation changes; the site deploys to GitHub Pages from `main`.
- Always rely on official IRSA / IPAC resources and peer-reviewed or arXiv papers for
  SPHEREx facts. Do not use or consult third-party SPHEREx GitHub tools unless the
  user explicitly asks.
- The external skill `spherex-irsa-access` lives at
  `/Users/shuang/Dropbox/work/project/vibe/guangtou_vibe/skills/spherex-irsa-access`
  and should be kept consistent with the `data_access.md` and `reduction_analysis.md` pages.
- Never estimate numbers about SPHEREx performance; quote the source (paper section,
  documentation page) or measure from data.
