# PROSPIE calibration of simulated heart-rate recovery

This exploratory analysis starts from HeatGuard v0.5 at `83a0518`. It estimates one parameter, the fraction of the gap to the resting heart-rate target closed per minute after work. The original generator closes half the gap each minute. The lab fit uses measured data to estimate a separate recovery fraction while retaining the existing response during work.

## Data sources

- Human observations come from the **Data** and **Key** sheets of the [PROSPIE workbook](https://doi.org/10.17028/rd.lboro.26076577.v1) deposited with Loughborough University. The [original workbook](https://ndownloader.figshare.com/files/47227096) is distributed under CC BY-NC 4.0 (publisher MD5 `cdbdb0795d3c5d2923d199466513c163`). These are controlled heat-chamber walking and rest trials. This analysis uses participant and condition codes, elapsed time, work/rest status, measured heart rate and probe-measured rectal temperature.
- Dubai inputs are the repository's `data/weather_hourly.csv` (2025) and `data/weather_hourly_2024.csv` (2024), sourced from the Open-Meteo historical API with ERA5 selected. Both use Dubai local time. These weather files drive the v0.5 physiological simulation, schedules and alerts.
- The Australian mine-worker files and Dubai Airport station measurements belong to separate field and weather comparisons. This experiment fits the recovery parameter using PROSPIE.

## Method

1. Within each trial, estimate resting heart rate and rectal temperature as medians during the initial ten-minute chamber-rest period. Require at least five valid readings of each. Keep transitions with five consecutive work minutes followed by ten consecutive rest minutes, a usable initial heart rate above the resting median, and complete heart-rate and rectal-temperature records for the prediction window. Values outside 30–220 bpm or 34–43 °C are missing for this analysis, including the workbook's 9999 sentinel.
2. Initialise each recovery prediction at the measured heart rate immediately before rest. At each subsequent minute, set the target to the trial's resting heart rate plus the existing 25 bpm/°C gain applied to the positive measured rectal-temperature change from baseline. Predict all ten minutes without feeding in later measured heart rates. Split by participant with seed 305. Fit the recovery fraction by minimising mean absolute error, averaging windows within participant and weighting participants equally. Compare with the original 0.50 fraction on held-out participants.
3. Apply the recovery fraction during resting and midday-break minutes in the v0.5 wearable generator. The simulation supplies the temperature used by its original heart-rate target. Generate 192 candidate training shifts in 2025 and 144 candidate test shifts in 2024 from different virtual workers, with four randomly sampled dates per worker and separate seeds. Fit one logistic regression model on original simulated 2025 inputs. Use its frozen predictions pipeline and v0.5's published operating point (0.32 threshold, 30-minute hold) on both versions of each clean-sensor 2024 test shift. Pair the comparisons by using the same underlying trajectories, reference events, and random seeds for wearable noise.

This checks conditional heart-rate recovery given the temperature trajectory. It does not validate the full temperature model or prove prediction accuracy on lab participants. The recovery fit uses rectal temperature as a proxy for the lab target's thermal forcing, whereas Dubai uses the simulator's internal core state. Lab rest arrangements, cooling and workloads vary from a UAE site. The Dubai exercise is a paired sensitivity analysis on a smaller, independently generated simulation cohort and has no prespecified success criterion.

## Reproduce

From the repository root with Python 3.13 and the repository dependencies installed, install `openpyxl` for reading the source and run:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python calibrate_hr_recovery.py /path/to/PROSPIE-original.xlsx
```

Add `--lab-only` to run the measured-data calibration without simulating Dubai shifts. The script writes the fitted parameter, holdout errors and paired Dubai scores to `outputs/prospie_recovery/`.

## Measured-data result

Twenty participants had eligible recovery windows. Fifteen participants (60 windows) were used to fit the rate, and five participants (22 windows) were held out. The fitted fraction was **0.43877 per minute**, compared with **0.50** in the original. On held-out participants, mean absolute error averaged **6.69 bpm** after calibration and **6.96 bpm** with the original fraction, a reduction of **0.26 bpm** (about **3.8%**). This is a small descriptive improvement in a small sample. No confidence interval was estimated.

## Dubai follow-up result

All 192 training and 144 test shifts were valid. Both variants saw the same 25 simulated test events.

| Test metric | Original recovery | PROSPIE-calibrated recovery |
|---|---:|---:|
| Missed events | 3 / 25 | 3 / 25 |
| Median lead time, with misses assigned zero | 30 min | 30 min |
| Mean false episodes per shift | 0.569 | 0.563 |
| Mean warning minutes per shift | 76.70 | 75.99 |

Both variants missed the same three events. One event's lead time, one shift's false-episode count and twelve shifts' warning duration changed. The slower recovery setting made little difference to warnings in this paired run. This result applies to the one fitted parameter and this test cohort. The separately locked 4,000-shift v0.5 run remains the primary study.

The repository test suite returned 46 passed, 5 skipped and 1 expected failure.
