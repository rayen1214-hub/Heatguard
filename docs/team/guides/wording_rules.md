# What to say and what never to say

Use this for the milestones, the paper, the slides and the Q&A. Markers check claims against the evidence,
so an overclaim costs more marks than a careful sentence.

## Safe sentences you can copy

- "HeatGuard is a **simulation testbed**: both warning methods are tested on exactly the same simulated shifts."
- "In the v0.2 test set, both methods caught all 4 danger events. The ML model raised far fewer alarms
  (0.49 vs 1.04 false episodes and 14 vs 274 warning minutes per six-hour shift)."
- "The WBGT rule had the longer median lead time (30 vs 26 minutes) because it is on for about three quarters
  of every shift, so it always gets the full 30-minute window."
- "With only 4 test events, these results are **preliminary**."
- "The danger limits of 38.2 °C and 38.5 °C are **study definitions**, not clinical thresholds."
- "Heart rate is generated from the same simulated body that defines danger, so the ML model has an easier task
  than it would with real sensors. We test this with a weaker heart-rate link."
- "The code was developed with an AI coding assistant (Claude Code). This is declared in our GenAI log, and each
  part was checked by its owner."
- "I'll check that and come back to you." (A fine answer in Q&A. Guessing is not.)

## Never write or say

| Don't | Why | Say instead |
|-------|-----|-------------|
| "ML is better than WBGT" | The data doesn't show it | "ML raised fewer alarms; both caught all test events" |
| "ML warns earlier" | It warned slightly later (26 vs 30 min) | Report both lead times |
| "HeatGuard keeps workers safe" / "prevents heat stroke" | Nothing was tested on people | "could support a future pilot" |
| "accuracy of X%" | We don't use accuracy; danger is rare | Lead time, misses, false episodes |
| "real-time IoT system" | There is no device or broker | "MQTT-style messages replayed in Python" |
| "digital twin" | No live link to a real person | "simulation" or "simulated worker model" |
| "first AI heat-warning system" | Not true, and not our claim | "an open comparison against a defined WBGT baseline" |
| Any number from a run labelled SYNTHETIC | Synthetic weather only tests the code | Wait for the real run |
| "The AI did it" / "Rayen did all of it" | Ownership is marked individually | Say what **you** did and how you checked it |

## Tense

The method is now done, so write it in the **past tense** ("we simulated", not "we will simulate").
