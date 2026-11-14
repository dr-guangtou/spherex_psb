#!/usr/bin/env python3
"""Markdown tables for the SED demo report from the per-galaxy results and validation outputs.

usage: uv run python scripts/sed_demo/summarise_demo.py [--root /Users/shuang/data/spherex/results]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sample_definition import DEMO_GALAXIES  # noqa: E402

from spherex_psb import RESULTS_ROOT  # noqa: E402
from spherex_psb.validation.boundary import BOUNDARIES_UM, boundary_ratios  # noqa: E402
from spherex_psb.validation.errors import MAX_PAIR_SEPARATION_UM  # noqa: E402

SHORT = {g: g[3:].replace("_", " ") for g in DEMO_GALAXIES}


def markdown(frame: pd.DataFrame, floatfmt: str = "%.3f") -> str:
    columns = list(frame.columns)
    rows = ["| " + " | ".join(str(c) for c in columns) + " |", "|" + "---|" * len(columns)]
    for _, row in frame.iterrows():
        cells = []
        for c in columns:
            v = row[c]
            if isinstance(v, float):
                cells.append("" if not np.isfinite(v) else floatfmt % v)
            else:
                cells.append(str(v))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def weighted_mean(values, errors) -> tuple[float, float, float]:
    """Inverse-variance weighted mean, its error, and chi2 of the values about it."""
    values, errors = np.asarray(values, float), np.asarray(errors, float)
    ok = np.isfinite(values) & np.isfinite(errors) & (errors > 0)
    w = 1 / errors[ok] ** 2
    mean = np.sum(w * values[ok]) / np.sum(w)
    return float(mean), float(1 / np.sqrt(np.sum(w))), float(np.sum(w * (values[ok] - mean) ** 2))


def section_sample(root: Path) -> None:
    rows = []
    for g, d in DEMO_GALAXIES.items():
        s = json.load(open(root / g / "sed_summary.json"))
        r = pd.read_parquet(root / g / "records_screened.parquet")
        used = r[r.screen_reason == ""]
        chi2 = used.groupby("detector").chi2_dof_near.median()
        point = (used.flux_point_ujy / used.flux_model_ujy).groupby(used.detector).median()
        rows.append(
            {
                "galaxy": SHORT[g],
                "z": d.redshift,
                "profile": f'n={d.shape.sersic_index:.0f}, Re={d.shape.effective_radius_arcsec:.1f}"',
                "exposures": s["n_records"],
                "DR1/QR3": f"{(r.release == 'dr1').sum()}/{(r.release == 'qr3').sum()}",
                "used": s["n_used"],
                "rejected": sum(
                    v
                    for k, v in s["screening"].items()
                    if k in ("model_weight_masked", "target_outside_cutout", "cutout_truncated")
                ),
                "screened": sum(v for k, v in s["screening"].items() if k.endswith("outlier")),
                "chi2 D1-D6": "/".join(f"{chi2.get(k, np.nan):.1f}" for k in range(1, 7)),
                "point/model D1-D6": "/".join(f"{point.get(k, np.nan):.2f}" for k in range(1, 7)),
                "E(B-V)": s["ebv"]["ebv_sandf"],
            }
        )
    print("### Sample and measurements\n")
    print(markdown(pd.DataFrame(rows)))


def section_estimators(root: Path) -> None:
    rows = []
    for g in DEMO_GALAXIES:
        v = json.load(open(root / g / "validation" / "summary.json"))["estimator_consistency"]
        rows.append(
            {
                "galaxy": SHORT[g],
                "n": v["n"],
                "median model/aperture(2px)": v["median_ratio"],
                "change 0.75-5 um [mag]": v["change_over_band_mag"],
                "scatter (MAD)": v["scatter_mad"],
            }
        )
    print("\n### Estimator consistency (model flux / model-corrected 2 px aperture)\n")
    print(markdown(pd.DataFrame(rows)))


def section_boundaries(root: Path) -> None:
    table = pd.concat(
        [pd.read_parquet(root / g / "validation" / "boundary_ratios.parquet") for g in DEMO_GALAXIES]
    )
    for column, label in (("flux_model_ujy", "model flux"), ("flux_point_ujy", "point-source control")):
        sub = table[table.flux_column == column]
        wide = sub.pivot(index="galaxy", columns="boundary", values="ratio_mag")
        err = sub.pivot(index="galaxy", columns="boundary", values="ratio_mag_err")
        out = pd.DataFrame(
            {"galaxy": [SHORT[g] for g in wide.index], "z": [DEMO_GALAXIES[g].redshift for g in wide.index]}
        )
        for b in BOUNDARIES_UM:
            out[b] = [f"{v:+.3f} ± {e:.3f}" for v, e in zip(wide[b], err[b], strict=True)]
        means = {"galaxy": "weighted mean", "z": ""}
        for b in BOUNDARIES_UM:
            m, e, chi2 = weighted_mean(wide[b], err[b])
            means[b] = f"{m:+.3f} ± {e:.3f} (chi2 {chi2:.0f}/{len(wide) - 1})"
        out = pd.concat([out, pd.DataFrame([means])], ignore_index=True)
        print(f"\n### Detector-boundary steps, {label}: -2.5 log10(F_B/F_A) [mag]\n")
        print(markdown(out))


def median_near(flux: np.ndarray, cwave: np.ndarray, ok: np.ndarray, wavelength: float) -> float:
    sel = ok & (np.abs(cwave - wavelength) < 0.1)
    return float(np.nanmedian(flux[sel])) if sel.sum() else np.nan


def section_stellar_boundaries(root: Path) -> None:
    """The same boundary test on the bright stars fitted jointly with each target (per-source fluxes)."""
    rows = []
    for g in DEMO_GALAXIES:
        r = pd.read_parquet(root / g / "records_screened.parquet")
        if "source_fluxes_ujy" not in r.columns:
            continue
        neighbours = pd.read_parquet(root / g / "neighbours.parquet")
        used = r[(r.screen_reason == "") & r.source_fluxes_ujy.notna()].copy()
        fluxes = [json.loads(s) for s in used.source_fluxes_ujy]
        stars = neighbours[(neighbours.source_type == "star") | (neighbours.r_e_arcsec <= 0)]
        for i, star in stars.iterrows():
            if star.sep_arcsec > 60 or not np.isfinite(star.mag_z) or star.mag_z > 16.5:
                continue
            name = f"n{i:03d}"
            flux = np.array([f.get(name, [np.nan, np.nan])[0] for f in fluxes])
            err = np.array([f.get(name, [np.nan, np.nan])[1] for f in fluxes])
            series = used[["detector", "cwave_um", "screen_reason"]].copy()
            series["flux_model_ujy"], series["flux_model_err_ujy"] = flux, err
            ok = np.isfinite(flux) & (flux > 0)
            if ok.sum() < 100:
                continue
            steps = boundary_ratios(series[ok], "flux_model_ujy")

            row = {
                "galaxy": SHORT[g],
                "star": name,
                'sep ["]': round(float(star.sep_arcsec), 1),
                "z mag": round(float(star.mag_z), 2),
                "F(1.25)/F(2.2)": round(
                    median_near(flux, used.cwave_um.to_numpy(), ok, 1.25)
                    / median_near(flux, used.cwave_um.to_numpy(), ok, 2.2),
                    2,
                ),
                "F(2.2)/F(3.4)": round(
                    median_near(flux, used.cwave_um.to_numpy(), ok, 2.2)
                    / median_near(flux, used.cwave_um.to_numpy(), ok, 3.4),
                    2,
                ),
            }
            for _, s in steps.iterrows():
                row[s.boundary] = f"{s.ratio_mag:+.3f} ± {s.ratio_mag_err:.3f}"
            rows.append(row)
    if rows:
        print("\n### Detector-boundary steps for bright stars in the same cutouts (point templates) [mag]\n")
        print(markdown(pd.DataFrame(rows)))


def section_pulls(root: Path) -> None:
    p = pd.concat(
        [pd.read_parquet(root / g / "validation" / "pull_statistics.parquet") for g in DEMO_GALAXIES]
    )
    out = p.pivot(index="galaxy", columns="detector", values="pull_std_robust").round(2)
    n = p.pivot(index="galaxy", columns="detector", values="n_pairs")
    snr = p.pivot(index="galaxy", columns="detector", values="median_snr").round(0)
    table = pd.DataFrame({"galaxy": [SHORT[g] for g in out.index]})
    for d in range(1, 7):
        table[f"D{d}"] = [
            f"{v:.2f} ({int(k)}, S/N {int(s)})" for v, k, s in zip(out[d], n[d], snr[d], strict=True)
        ]
    print("\n### Error calibration: robust width of the repeat-pair pull per detector (pairs, median S/N)\n")
    print(f"Pairs: same detector, |Δλ| < {MAX_PAIR_SEPARATION_UM} um, different observations.\n")
    print(markdown(table))
    print("\nMedian over galaxies: " + ", ".join(f"D{d} {out[d].median():.2f}" for d in range(1, 7)))


def section_injection_cross_code(root: Path) -> None:
    rows = []
    for g in DEMO_GALAXIES:
        v = json.load(open(root / g / "validation" / "summary.json"))
        inj, cc = v.get("injection", {}), v.get("cross_code", {})
        rows.append(
            {
                "galaxy": SHORT[g],
                "injected (n)": inj.get("n"),
                "model": inj.get("model_ratio_median"),
                "model MAD": inj.get("model_ratio_mad"),
                "aperture 2 px": inj.get("aperture_ratio_median"),
                "point": inj.get("point_ratio_median"),
                "cross-code n": cc.get("n"),
                "ours / tractorjax": cc.get("ratio_median"),
                "16-84 %": f"{cc.get('ratio_16', np.nan):.3f}-{cc.get('ratio_84', np.nan):.3f}",
            }
        )
    print("\n### Injection-recovery (recovered / injected, median) and cross-code ratio\n")
    print(markdown(pd.DataFrame(rows)))


def section_releases(root: Path) -> None:
    """DR1 versus QR3: ratio of the inverse-variance weighted mean fluxes of matched exposures (same detector,
    wavelengths within the repeat-pair separation), which stays unbiased at low signal-to-noise."""
    rows = []
    for g in DEMO_GALAXIES:
        r = pd.read_parquet(root / g / "records_screened.parquet")
        used = r[r.screen_reason == ""].sort_values("cwave_um")
        row = {"galaxy": SHORT[g]}
        for d, grp in used.groupby("detector"):
            dr1, qr3 = grp[grp.release == "dr1"], grp[grp.release == "qr3"]
            a_rows, q_rows = [], []
            for _, q in qr3.iterrows():
                close = dr1[np.abs(dr1.cwave_um - q.cwave_um) < MAX_PAIR_SEPARATION_UM]
                if len(close):
                    q_rows.append(q)
                    a_rows.append(close.iloc[int(np.argmin(np.abs(close.cwave_um - q.cwave_um)))])
            if not q_rows:
                row[f"D{int(d)}"] = ""
                continue
            q_frame, a_frame = pd.DataFrame(q_rows), pd.DataFrame(a_rows)
            wq, wa = 1 / q_frame.flux_model_err_ujy**2, 1 / a_frame.flux_model_err_ujy**2
            mean_q = np.sum(wq * q_frame.flux_model_ujy) / np.sum(wq)
            mean_a = np.sum(wa * a_frame.flux_model_ujy) / np.sum(wa)
            err = (
                mean_q / mean_a * np.hypot(1 / np.sqrt(np.sum(wq)) / mean_q, 1 / np.sqrt(np.sum(wa)) / mean_a)
            )
            row[f"D{int(d)}"] = f"{mean_q / mean_a:.3f} ± {err:.3f} ({len(q_rows)})"
        rows.append(row)
    print("\n### QR3 / DR1 flux ratio at matched wavelengths (weighted means, number of matched exposures)\n")
    print(markdown(pd.DataFrame(rows)))


def section_external(root: Path) -> None:
    e = pd.concat(
        [pd.read_parquet(root / g / "validation" / "external_comparison.parquet") for g in DEMO_GALAXIES]
    )
    keep = e[
        e.origin.isin(["SDSS DR17", "Legacy DR10 forced", "2MASS XSC", "AllWISE"])
        & e.aperture.isin(["model", "cmodel", "Tractor model", "total (ext)", "elliptical (gmag)"])
    ]
    keep = keep[keep.spherex_synthetic_ujy.notna()]
    keep["label"] = keep.origin + " " + keep.aperture + " " + keep.band
    wide = keep.pivot_table(index="galaxy", columns="label", values="spherex_over_external")
    wide.index = [SHORT[g] for g in wide.index]
    print("\n### SPHEREx synthetic / external broadband flux\n")
    print(markdown(wide.reset_index().rename(columns={"index": "galaxy"}), "%.2f"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=RESULTS_ROOT)
    args = parser.parse_args()
    pd.set_option("display.width", 250)
    section_sample(args.root)
    section_estimators(args.root)
    section_boundaries(args.root)
    section_stellar_boundaries(args.root)
    section_pulls(args.root)
    section_injection_cross_code(args.root)
    section_releases(args.root)
    section_external(args.root)


if __name__ == "__main__":
    main()
