# Validation

The locked v0.5 results and the archived demo are checked separately. Browser interaction checks used Chrome offline at 1440 × 1050, with a 390 px viewport for one responsive check.

| ID | What to try in the browser | Expected and observed |
|---|---|---|
| D01 | Open the page with the network disabled | The site board lists 12 workers, and the detail area offers five shift stories. |
| D02 | Focus a shift-story button and press Enter | The button becomes selected and its worker details appear. |
| D03 | Reset the first story, then select **Go to first warning** | 06:00 starts at **OK**. The first warning changes the watch to **STOP** and shows rest instructions. |
| D04 | At minute 60, switch the heart-rate sensor off. Inspect minute 65 | The heart-rate reading disappears and the WBGT fallback banner appears. |
| D05 | Clear that fault, freeze the sensor at minute 60, then inspect minute 66 | The reading is labelled frozen and the WBGT fallback banner appears. |
| D06 | Select **Repair sensor** | The fallback banner clears and a heart-rate value appears. |
| D07 | Select the first site tile and move the clock to minute 400 | The tile becomes selected and the watch displays **BREAK**. |
| D08 | Resize the viewport to 390 px | The clock slider fits inside the viewport, the worker state still renders and Chrome reports no page error. |

[Browser run log](demo-checks.txt) · [Engine agreement](engine-agreement.txt) · [Score and data checks](results-checks.txt)

[Normal state](screenshots/ready.png) · [Warning state](screenshots/warning.png) · [WBGT fallback](screenshots/fallback.png)

The screenshots are from an earlier offline walkthrough of the same archived page. The eight checks above were run by Codex using Playwright. The case table gives steps a reviewer can repeat by hand. It supplies engineering validation for the demo. The independent student-authored test comparison has its own record in [the edge-case log](../test_cases.md).

## Python and pipeline checks

The complete Python suite on the submission copy finished with **46 passed, 5 skipped and 1 expected failure**. The five skipped entries are empty student-case fixtures. The expected failure records the original Week 7 model's handling of missing heart rate.

The v0.5 smoke run completed data generation, model selection and final scoring on its tiny synthetic fixture. Its scripted verdict was PARTLY CLOSED. This fixture checks that the stages execute and is excluded from the reported research scores.

The measured-data lab-only command reproduced the saved recovery fraction and held-out errors. The score verification script checked source hashes and all paired shift scores against the saved retraining summary. The full retraining uses the archived run.

## Run the checks

From the repository root:

```sh
python -m pytest -q
node docs/demo/check_engine.js
python docs/validation/check-results.py
```

The browser interaction runner requires Node.js, Playwright and Google Chrome. Set `NODE_PATH` to the directory containing the installed `playwright` package:

```sh
NODE_PATH=/path/to/node_modules node docs/validation/check-demo.cjs
```
