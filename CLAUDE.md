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
- SPHEREx knowledge: `docs/spherex_data_guide.md` is the project's living guide to
  SPHEREx data usage. `docs/reference_notes/` holds per-source notes (official pages,
  papers). Update the guide, not memory, when something new is learned about SPHEREx.
- Always rely on official IRSA / IPAC resources and peer-reviewed or arXiv papers for
  SPHEREx facts. Do not use or consult third-party SPHEREx GitHub tools unless the
  user explicitly asks.
- The external skill `spherex-irsa-access` lives at
  `/Users/shuang/Dropbox/work/project/vibe/guangtou_vibe/skills/spherex-irsa-access`
  and should be kept consistent with `docs/spherex_data_guide.md`.
- Never estimate numbers about SPHEREx performance; quote the source (paper section,
  documentation page) or measure from data.
