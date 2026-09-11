# Example Analysis Skill

## Workflow

Inspect the input schema first, validate missing values, then compute concise
summary statistics and save machine-readable output.

## Output Contract

Write `report.json` with a stable schema and mention assumptions in a short
text field. Never invent values that are not present in the input.
