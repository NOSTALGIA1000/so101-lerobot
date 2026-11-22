# Step 7: Evaluation

Date: 2026-07-22

## Status

Implemented baseline evaluation for the lightweight BC policy.

## Files

- `evaluation/evaluate_bc.py`
- `evaluation/evaluation_result.json`
- `evaluation/evaluation_result_bc_50ep.json`
- `evaluation/evaluation_result_bc_phase_50ep.json`

## Latest Result

Policy:

```text
training/outputs/chunk_bc_bootstrap_20_c10.npz
```

Evaluation:

```text
episodes: 20
max_steps: 420
execute_chunk: 10
success_rate: 0.60
mean_max_cube_height: 0.0830 m
```

## Interpretation

Chunked BC improves the 20-episode benchmark from 0.25 to 0.60 success compared
with scalar-action BC. This confirms that the task needs chunked action
prediction before investing in image encoders or larger datasets.

The next evaluation target is full ACT-style training with image observations,
using the current chunked BC result as the state-based reference baseline.
