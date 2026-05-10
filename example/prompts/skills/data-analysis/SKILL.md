---
name: data-analysis
description: Guidelines for reliable exploratory data analysis.
tags:
  - data
  - pandas
  - analytics
version: "1.0"
---

## Data Loading

Always inspect shape, dtypes, and null counts before any analysis.
Document all data sources and their refresh cadence.

## Data Cleaning

Be explicit about how nulls are handled (drop, fill, flag).
Validate column ranges and categorical values before transforming.
Never modify the original DataFrame in-place without a backup.

## Visualisation

Use matplotlib or seaborn. Label all axes with units. Include a title.
Use colorblind-friendly palettes.