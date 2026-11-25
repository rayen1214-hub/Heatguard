# External measurements used in the exploratory follow-up

Retrieved 17 November 2026. Source workbooks are preserved as downloaded.

- PROSPIE, Loughborough University repository, https://doi.org/10.17028/rd.lboro.26076577.v1. Original file https://ndownloader.figshare.com/files/47227096. Licence CC BY-NC 4.0, https://creativecommons.org/licenses/by-nc/4.0/. The workbook includes its data dictionary and condition descriptions. Controlled walking and rest trials with measured heart rate and rectal temperature. Used to fit heart-rate recovery, with participants held out for checking.
- Taggart et al., Comparing thermal strain in outdoor maintenance and indoor service workers in the mining industry during summer, PLOS ONE, https://doi.org/10.1371/journal.pone.0292436, CC BY. Supplement files s003, s008 and s009 contain checkpoint physiology, group-average heart rate and environmental conditions. Download each from https://journals.plos.org/plosone/article/file?type=supplementary&id=info:doi/10.1371/journal.pone.0292436.s003 (substitute s008 or s009). These field measurements are used for descriptive comparison only.
- Dubai Airport OMDB station observations, Iowa Environmental Mesonet archive, https://mesonet.agron.iastate.edu/request/download.phtml. CSV contains decoded temperature, dew point and wind plus original METAR reports, in UTC, 31 May through 30 September 2025. Used for a separate check of the 2025 Dubai weather input.

The Dubai worker readings remain simulated. No measured UAE worker physiology is included.

Reproduce calibration and retraining from the repository root with Python 3.13, requirements.txt and openpyxl installed:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python retrain_prospie.py
```

The script writes new outputs under outputs/prospie_retrained. Saved results are in [the retraining directory](../../docs/results/prospie_retrained/). The [method and comparisons](../../docs/prospie_recovery.md) describe both follow-up runs. The completed retraining used 768 training shifts, 288 validation shifts and 480 test shifts, separate virtual workers and seeds, 2025 weather for training/validation and 2024 weather for testing. Both versions were trained separately and tuned on validation workers. They missed 3 of 84 events each. This is an exploratory follow-up.

The run manifest retains the original local source paths used at execution time and SHA-256 checksums. The same source bytes are now available here.
