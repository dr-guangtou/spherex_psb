"""Shared figure style for the SED demo: journal widths, LaTeX Computer Modern text, inward ticks, one fixed
colour-blind-safe colour per detector.
"""

from __future__ import annotations

import os

import matplotlib as mpl

SINGLE_COLUMN_IN = 3.4
DOUBLE_COLUMN_IN = 7.0
DPI = 300

# Okabe-Ito palette (colour-blind safe), one colour per detector D1-D6.
DETECTOR_COLOURS = {1: "#0072B2", 2: "#56B4E9", 3: "#009E73", 4: "#E69F00", 5: "#D55E00", 6: "#CC79A7"}
NEUTRAL_GREY = "#7F7F7F"
BLACK = "#000000"

AIRGLOW_LINES_UM = {"He I": 1.083}


def apply_style() -> None:
    os.environ["PATH"] = "/Library/TeX/texbin:" + os.environ.get("PATH", "")
    mpl.rcParams.update(
        {
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "legend.fontsize": 7.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.top": True,
            "ytick.right": True,
            "xtick.minor.visible": True,
            "ytick.minor.visible": True,
            "xtick.major.size": 3.5,
            "ytick.major.size": 3.5,
            "xtick.minor.size": 2.0,
            "ytick.minor.size": 2.0,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.0,
            "legend.frameon": False,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "figure.dpi": 110,
        }
    )


def panel_label(ax, text: str, x: float = 0.03, y: float = 0.95) -> None:
    ax.text(x, y, text, transform=ax.transAxes, ha="left", va="top", fontsize=9)


WAVELENGTH_LABEL = r"$\lambda_{\rm obs}\ [\mu{\rm m}]$"
REST_WAVELENGTH_LABEL = r"$\lambda_{\rm rest}\ [\mu{\rm m}]$"
FLUX_LABEL = r"$F_\nu\ [{\rm mJy}]$"
