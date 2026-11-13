#!/bin/zsh
# Measure every wide-survey exposure of the six demo galaxies, one galaxy at a time (no concurrent IRSA jobs).
cd "$(dirname "$0")/../.."
LOG=/Users/shuang/data/spherex/scratch/run_all.log
for g in g1_reference g2_compact g3_large g4_neighbour g5_no_legacy g6_post_starburst; do
  echo "=== $g $(date) ===" >> "$LOG"
  uv run python -u scripts/sed_demo/measure_galaxy.py "$g" 2>&1 | grep -v "FITSFixedWarning\|warnings.warn\|VerifyWarning\|^  " >> "$LOG"
done
echo "=== done $(date) ===" >> "$LOG"
