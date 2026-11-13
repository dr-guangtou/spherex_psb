#!/bin/zsh
# After run_all.sh: screen, assemble SEDs and make figures 2-4 per galaxy, run the validation items, then the
# sample-level figures. Serial, so that IRSA and Data Lab see one client at a time.
cd "$(dirname "$0")/../.."
LOG=/Users/shuang/data/spherex/scratch/run_validation.log
for g in g1_reference g2_compact g3_large g4_neighbour g5_no_legacy g6_post_starburst; do
  echo "=== $g figures $(date) ===" >> "$LOG"
  uv run python -u scripts/sed_demo/make_galaxy_figures.py "$g" 2>&1 | grep -v "FITSFixedWarning\|warnings.warn\|VerifyWarning\|^  " >> "$LOG"
  echo "=== $g validation $(date) ===" >> "$LOG"
  uv run python -u scripts/sed_demo/validate_galaxy.py "$g" 2>&1 | grep -v "FITSFixedWarning\|warnings.warn\|VerifyWarning\|^  " >> "$LOG"
done
echo "=== sample figures $(date) ===" >> "$LOG"
uv run python -u scripts/sed_demo/make_sample_figures.py 2>&1 | grep -v "FITSFixedWarning\|warnings.warn\|VerifyWarning\|^  " >> "$LOG"
echo "=== done $(date) ===" >> "$LOG"
