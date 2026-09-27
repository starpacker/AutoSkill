# V10 SEL

`skill_selector_v10/selector.py` implements the validated three-phase selector:

- **P1 direct observation**: use a GT-verified target/source mapping and bypass
  similarity thresholds.
- **P2 nearest neighbor**: choose the best available source by similarity.
- **P3 fallback**: use the v7-style isotonic quality curve plus source quality and
  compatibility bonuses when P2 does not pass.

Compatibility is tiered as same-type, compatible cross-type, or incompatible.
Same-type uses a permissive threshold, compatible tasks use a moderate threshold,
and incompatible tasks are rejected. Baseline gating prevents spending transfer
budget on already-solved targets.

Training data are generated from completed transfer runs and indexed result files;
testing is performed on held-out pairs with `scripts/run_experiments.py`. Configure
all paths through environment variables or `V10Config`鈥攏o server paths or secrets
are embedded in the selector.

```bash
python -m skill_selector_v10.demo
python skill_selector_v10/scripts/run_experiments.py --help
```
