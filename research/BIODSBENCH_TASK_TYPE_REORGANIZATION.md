# BioDSBench-R Task-Type Reorganization

The headline comparison uses 39 evaluation tasks and groups them by their
primary biological analysis objective. The original fine-grained labels include
14 `data-wrangling` and 2 `visualization` tasks. Those broad labels are folded
into the analysis they support; the task count and the three arm totals are
unchanged.

| Reorganized task type | No Skill | SkillOpt transfer | Ours (V10 SEL) | Delta vs No Skill |
| --- | ---: | ---: | ---: | ---: |
| Pathway enrichment | 6/10 (60.0%) | 8/10 (80.0%) | 10/10 (100%) | +40.0 pp |
| Expression analysis | 19/21 (90.5%) | 18/21 (85.7%) | 21/21 (100%) | +9.5 pp |
| Survival analysis | 2/3 (66.7%) | 2/3 (66.7%) | 3/3 (100%) | +33.3 pp |
| Clustering | 3/4 (75.0%) | 2/4 (50.0%) | 4/4 (100%) | +25.0 pp |
| Cross-cohort comparison | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | +100.0 pp |
| **All tasks** | **30/39 (76.9%)** | **31/39 (79.5%)** | **39/39 (100%)** | **+23.1 pp** |

`Delta` is an absolute percentage-point difference:

```text
100 * (Ours_passes / n - NoSkill_passes / n)
```

For example, pathway enrichment is `100% - 60% = +40.0 pp`. Counts are
aggregated from the stored per-task comparison arms and SkillOpt transfer
results. Ours refers to the BioDSBench-native V10 SEL arm; SkillOpt refers to the
BioMNIBench-trained SkillOpt skill transferred to BioDSBench.

## Reassigned generic-label tasks

The following 16 tasks carry an original generic label and were assigned by the
primary objective stated in the task description/rationale:

| New group | Tasks | Rationale |
| --- | --- | --- |
| Expression analysis | `23502430_q2`, `32637351_q0`, `32637351_q1`, `33591944_q0`, `34092242_q0`, `34305920_q0`, `37091789_q0`, `38342795_q1` | Expression visualization, sample/group summaries, or expression matrix preparation for expression analysis |
| Pathway enrichment | `33176622_q3`, `33591944_q5`, `34565373_q5`, `34621245_q5` | DEG filtering and identifier conversion for downstream enrichment |
| Survival analysis | `34238253_q0` | Expression and survival data integration |
| Clustering | `35222524_q2`, `37255653_q2` | Joining precomputed cluster labels with expression data |
| Cross-cohort comparison | `34305920_q1` | CD161 expression comparison and visualization across cancer types |

This is a reporting regrouping, not a change to task-level scores or the
original task annotations. The original labels remain useful when reproducing
the selector's controlled-vocabulary analyses.
