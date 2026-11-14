#!/usr/bin/env python3
"""Driver with a per-step timeout: measure the named galaxies (resumable; cutouts already on disk are kept),
then run the validation driver. A step that exceeds its time limit is killed and retried once.

usage: uv run python scripts/sed_demo/run_remaining.py g3_large g5_no_legacy g6_post_starburst
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = Path("/Users/shuang/data/spherex/scratch/run_remaining.log")
MEASURE_TIMEOUT_S = 2 * 3600
VALIDATION_TIMEOUT_S = 4 * 3600


def run(command: list[str], timeout: int, label: str) -> bool:
    for attempt in (1, 2):
        with LOG.open("a") as log:
            log.write(f"=== {label} attempt {attempt} {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            log.flush()
            try:
                completed = subprocess.run(
                    command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False
                )
            except subprocess.TimeoutExpired:
                log.write(f"=== {label}: timed out after {timeout} s ===\n")
                continue
            if completed.returncode == 0:
                return True
            log.write(f"=== {label}: exit code {completed.returncode} ===\n")
            time.sleep(120)
    return False


def main() -> None:
    galaxies = sys.argv[1:]
    for galaxy in galaxies:
        ok = run(
            ["uv", "run", "python", "-u", "scripts/sed_demo/measure_galaxy.py", galaxy],
            MEASURE_TIMEOUT_S,
            f"measure {galaxy}",
        )
        LOG.open("a").write(f"=== measure {galaxy}: {'ok' if ok else 'FAILED'} ===\n")
    run(["zsh", "scripts/sed_demo/run_validation.sh"], VALIDATION_TIMEOUT_S, "validation")
    LOG.open("a").write(f"=== all done {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")


if __name__ == "__main__":
    main()
