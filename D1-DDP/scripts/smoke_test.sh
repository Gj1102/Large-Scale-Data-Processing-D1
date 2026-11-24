#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1
python src/train.py --fake-data --batch 1 --accum-steps 1 --warmup 0 --steps 1 --experiment-id smoke_single
torchrun --standalone --nproc-per-node=2 src/train.py --fake-data --batch 1 --accum-steps 4 --strategy delayed --warmup 0 --steps 1 --check-ranks --experiment-id smoke_ddp
