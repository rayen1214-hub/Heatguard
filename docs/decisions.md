# Design decisions (v0.1)

| # | Decision | Why | Alternative rejected or deferred |
|---|----------|-----|---------------------------------|
| D1 | Thursday build is a small pilot (10 workers × 10 dates, 44 same-partition shifts); the full 30 × 60 design is one flag away | A small version that runs end to end shows progress and lets us find problems cheaply | Full design only: slower to debug |
| D2 | Report danger-event counts as they are; never lower the danger limit or raise workloads to create events | Tuning the experiment until it "works" is a form of bias | Changing limits after seeing results |
| D3 | PHS is run one minute at a time, carrying body state between minutes | Weather changes during the shift; pythermalcomfort 4.8.0 accepts and returns the state needed | One steady PHS run per shift: ignores changing weather |
| D4 | Logistic regression first; random forest and gradient boosting in Week 8 | Fast, explainable, enough to prove the pipeline | Deep learning: too little data, harder to explain |
| D5 | One-screen Streamlit dashboard | It is the demo for the lab and the symposium | Separate evaluation app: not needed |
| D6 | Messages replayed in Python on MQTT-style topics, no broker | Tests the message format and fault handling with less infrastructure | Mosquitto broker: network behaviour is out of scope |
| D7 | Worker split alternates acclimatised and unacclimatised workers | The first split put only unacclimatised workers in the test set (see iteration log) | Purely random split |
| D8 | Direct sunlight faded in between cos(solar zenith) 0.05 and 0.15 in the WBGT calculation | Hour-averaged radiation divided by a tiny cos(zenith) gave impossible sunrise WBGT values; a hard cut-off caused a 2 °C jump | Using the raw value; a hard cut-off |
| D9 | Air speed for PHS = 10 m wind × 0.75, clipped to 0.2–3.0 m/s | PHS needs air speed at body height and has a valid range of 0–3 m/s | Using 10 m wind directly |
