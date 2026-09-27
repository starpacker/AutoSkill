# Transfer protocol

The evaluation compares four arms on held-out BioMniBench targets:

1. **No-skill baseline**: the harness receives no skill bundle.
2. **Oracle skill (SOTA control)**: the target's own oracle bundle.
3. **GT few-shot transfer**: a source trajectory plus ground-truth code/example,
   with no generalized skill selection.
4. **Generalized/V10 SEL transfer**: a source skill is abstracted, matched, and
   selected by the V10 selector before target execution.

Within-domain pairs share an analysis family; cross-domain pairs test robustness
under a different task family. Raw cross-Gemini and within-Gemini controls are
provided by the corresponding runner scripts. Evaluation outputs must remain
outside git because they contain private trajectories and judge artifacts.

```bash
python run_transfer_skill_eval.py --mode within-domain --dry-run
python run_transfer_skill_eval.py --mode all --max-concurrent 2
python run_cross_gemini_12.py --dry-run
python run_within_gemini_pair_controls.py --dry-run
python collect_results.py --transfer
```
