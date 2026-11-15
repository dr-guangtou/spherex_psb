# Internal pages

Project documents, checkpoint reports and notes on third-party or private material. They are built only
for the owner's review (`sphinx-build -t internal`, `docs/_build/internal`) and are never part of the
published site; the list of what is internal is `INTERNAL_PATTERNS` in `docs/conf.py`.

```{toctree}
:caption: Project
:maxdepth: 1

Specification <SPEC>
To do <todo>
Lessons <lessons>
note-style rule book <html_documentation_guide>
```

```{toctree}
:caption: Reports
:maxdepth: 1

SED demo report <reports/demo_sed_report>
H-minus bump feasibility <reports/hminus_bump_feasibility>
SED demo task <reports/sed_demo_task>
Third-party tool review <reports/spherex_tools_review>
```

```{toctree}
:caption: Studies
:maxdepth: 1

Photometry study (2026-11) <references/studies/photometry_study_2026-11>
```

```{toctree}
:caption: Third-party tools
:maxdepth: 1

GitHub survey (2026-09) <references/tools/github_survey_2026-09-23>
references/tools/spherex-retrieval
references/tools/tractorjax-spherex
references/tools/Caltech-IPAC_spherex-pipelines
references/tools/Caltech-IPAC_tractor-spherex
references/tools/SPHEREx_pipeline
references/tools/SPHERExSpecPhot
references/tools/SPIFF
references/tools/spexpi
references/tools/spherex-cutoutdb
references/tools/spherex-tools
references/tools/spherex_spectra
references/tools/spherextract
references/tools/sphx_spec_stack
references/tools/spxquery
references/tools/xcavation
```
