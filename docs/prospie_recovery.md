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

## Follow-up using independent training, validation and test shifts

The paired run above kept one predictor fixed. A later exploratory run trained **two separate logistic regressions** on matched Dubai simulations. It used 768 training shifts and 288 threshold-selection shifts in 2025, then 480 test shifts in 2024. Each cohort had separate virtual workers. Both versions used the same shift schedules, body model and fault-free test inputs apart from the recovery rate applied to simulated heart rate during rest.

| Test metric | Original recovery | PROSPIE recovery | WBGT |
|---|---:|---:|---:|
| Missed events | 3 / 84 | 3 / 84 | 0 / 84 |
| Mean warning minutes per shift | 122.98 | 122.12 | 502.66 |

The gain on the held-out lab recordings did little to change warning performance in this Dubai simulation. Saved shift scores, model-selection tables and the run manifest are in [the retraining results](results/prospie_retrained/).

### Australian field comparison

Taggart et al.'s Western Australian mine-worker study supplied measured summer maintenance-worker checkpoints (S3) and a group-average heart-rate trace (S8). S9 records field conditions. The comparison was descriptive and did not tune or train a model.

| Measure | Western Australian field data | PROSPIE-calibrated Dubai simulation |
|---|---:|---:|
| First six-hour mean heart rate (bpm) | 80.6 | 100.9 |
| Mid-shift median heart rate (bpm) | 87.0 | 92.6 |
| Mid-shift median core or rectal temperature (°C) | 37.50 | 37.71 |

The Australian sample covers 12 summer maintenance workers. The field mid-shift temperature estimate is based on 28 readings from 10 of them. A group-average trace cannot test individual recovery or alert accuracy. Differences in jobs, work-rest schedules and climate limit the comparison. In particular, the heart-rate gap remains after calibration and shows where the simulated shifts differ from this measured workforce.

### Dubai weather cross-check

Dubai Airport METAR observations cover temperature at a local station. For the 2025 morning period from 06:00 to 11:59 Dubai time, station reports with matching hourly timestamps were compared with ERA5. Multiple station reports at the same timestamp were reduced to their median. There were 731 matched hours and a mean absolute temperature difference of 1.117 °C. This check describes air temperature at the airport. The project still uses the ERA5 inputs and has no measured UAE worker physiology.

[Source workbooks and licences](../data/external/README.md) · [Verification script](validation/check-results.py)
