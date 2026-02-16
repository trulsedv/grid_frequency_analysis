# Analysis Plan: Nordic Grid Frequency Improvement Attribution

## Goal
Quantify whether the 2025 reduction in minutes outside 49.9–50.1 Hz can be explained by damping in specific oscillation period ranges.

## Hypotheses
- **H1 (balancing):** oscillations with periods ~15 min to 2 h are reduced in/after 2025.
- **H2 (local control):** oscillations with periods ~30 s to 2 min are reduced in/after 2025.
- **H3 (impact):** damping in those ranges materially reduces minutes outside 49.9–50.1 Hz.

## Data and outputs
- Input: Fingrid historical frequency, 1 Hz samples.
- Core outcome: minutes outside 49.9–50.1 Hz by week/year.
- Spectral features: weekly power/amplitude summaries by period bins.

## Pipeline (implementation roadmap)
1. **Ingest**
   - download `.7z` archives
   - extract daily CSV
2. **Standardize**
   - convert Helsinki -> Oslo timezone
   - aggregate/fill to regular 1 Hz weekly files
3. **Outcome metric**
   - compute weekly minutes outside 49.9–50.1
   - cumulative minutes by week (per year)
4. **Week-vs-week spectral comparison**
   - same summer week: 2024 vs 2025
   - compare FFT/PSD curves
5. **Weekly spectral tracking**
   - for each week, compute spectral summary per period bin
   - plot bin amplitudes vs `YYYY-WW`
6. **Reconstruction validation**
   - reconstruct signal from selected frequency content
   - compare estimated vs observed out-of-band minutes
7. **Counterfactual attribution**
   - modify 2025 spectra by restoring selected bins to pre-2025 levels
   - reconstruct and recompute out-of-band minutes
   - run one-bin-at-a-time and combined scenarios

## Method notes
- Prefer **Welch PSD** (stability) + FFT for visual diagnostics.
- Use consistent preprocessing per week (detrend, windowing rules).
- Treat counterfactuals as attribution evidence under quasi-linear assumptions.
- Add sensitivity checks (week choice, preprocessing, threshold variants).

## Initial period bins
- `primary_local_control`: 30 s – 2 min
- `balancing_15m_to_2h`: 15 min – 2 h

These are configurable and can be extended later.
