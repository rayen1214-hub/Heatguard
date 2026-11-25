# IEEE paper reference audit

Checked on 26 November 2026. The table covers the 35 entries in order of first citation. Journals and datasets were checked against bibliographic records or publisher records, and institutional publications against their source. The claim review below identifies statements cross-checked against source text or project code. This record is for team review before submission.

## Claims checked against sources and code

- The MoHRE guide supplies the midday-break dates and hours. The Dubai guideline supplies the 40–45 °C high-risk band. The locked C2 simulation uses the NWS formula with the 40 °C threshold, and the post-hoc C2b uses a Humidex approximation checked against five Dubai chart cells.
- The Abu Dhabi code calls for using TWL as part of a heat-management process. C3 implements specific thresholds from published TWL sources and is described as the study's rule. C4 uses NIOSH limits.
- The Tustin case series supports 22 of 25 cases meeting or exceeding WBGT-based limits. The Sousan field study supplies a separate example of high WBGT risk ratings relative to a physiological index. These are separate datasets.
- The nearest wearable studies support methods for core-temperature estimation, physiological classification and exposure-time prediction. The paper now defines its contribution around the simulated comparison of warning outcomes and avoids a universal priority claim.
- The Guatemala rates are a self-pacing calibration target. Qatar and UAE comparator values are descriptive field summaries. PROSPIE fitted one simulated parameter in a separate follow-up, and the Australian group trace provided a descriptive comparison.
- The scoring code stops at the first event and excludes new false episodes in the final 30 minutes of event-free shifts. The paper reports the locked warning-minute totals and false-episode counts. The exploratory percentage-of-work-time and episode-precision proxies were omitted because their denominators differ from those literal descriptions.

## Reference checks

| # | Source | Record checked |
|---|---|---|
| 1 | Heat, Human Performance, and Occupational Health: A Key Issue for the Assessment of Global Climate Change Impacts | [Crossref metadata](https://doi.org/10.1146/annurev-publhealth-032315-021740) |
| 2 | MoHRE occupational health and safety guide | [Official guide](https://www.mohre.gov.ae/assets/download/6ef28a8/Occupational-Health-and-Safety-Guide-EN.pdf.aspx) |
| 3 | Dubai Municipality heat stress guideline, v3.0 | [Official guideline](https://www.dm.gov.ae/wp-content/uploads/2024/07/DM-HSD-GU38-MHSW2_Technical-Guidelines-for-Management-of-Heat-Stress-at-Work_V3.pdf) |
| 4 | ADOSH-SF CoP 11.0, v4.0 | [Official code](https://www.adphc.gov.ae/-/media/Project/ADPHC/ADPHC/PDF/OSHAD-SF/Codes-of-Practise/11---Safety-in-the-Heat-v31-English.pdf) |
| 5 | Limiting Metabolic Rate (Thermal Work Limit) as an Index of Thermal Stress | [Crossref metadata](https://doi.org/10.1080/104732202753438261) |
| 6 | ISO 7243:2017 | [ISO catalogue](https://www.iso.org/standard/67188.html) |
| 7 | NIOSH occupational exposure criteria | [CDC publication](https://www.cdc.gov/niosh/publications/numbered/2016-106.html) |
| 8 | EGA wearable technology trial announcement | [Company announcement](https://media.ega.ae/ega-extends-use-of-wearable-technology-to-beat-the-heat-in-the-uae-summer/) |
| 9 | Predicting Occupational Heat Stress in Critical Sectors: A Sector-Based Systematic Review of Wearable Sensing, IoT Platforms, and Machine Learning Models | [Crossref metadata](https://doi.org/10.18196/jrc.v6i5.27377) |
| 10 | Miller and Bates, Thermal Work Limit | [Journal](https://academic.oup.com/annweh/article-abstract/51/6/553/183107) |
| 11 | Bates and Schneider, UAE construction workers | [Article in PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC2561022/) |
| 12 | Tustin et al., exposure limits in outdoor workers | [CDC journal](https://www.cdc.gov/mmwr/volumes/67/wr/mm6726a1.htm) |
| 13 | Sousan et al., wearable monitoring in agricultural workers | [Journal](https://onlinelibrary.wiley.com/doi/full/10.1002/ajim.70103) |
| 14 | Hirata et al., wearable core-temperature estimation | [Author institution and IEEE DOI](https://research.tcu.ac.jp/en/publications/body-core-temperature-estimation-using-new-compartment-model-with/) |
| 15 | Accuracy of Algorithm to Non-Invasively Predict Core Body Temperature Using the Kenzen Wearable Device | [Crossref metadata](https://doi.org/10.3390/ijerph182413126) |
| 16 | Heat Stroke Prevention in Hot Specific Occupational Environment Enhanced by Supervised Machine Learning with Personalized Vital Signs | [Crossref metadata](https://doi.org/10.3390/s22010395) |
| 17 | Worker-centric heat strain analysis: Integrating physiological signals with ensemble learning and domain adaptation | [Crossref metadata](https://doi.org/10.1016/j.autcon.2024.105670) |
| 18 | A machine learning-based forecasting model for personal maximum allowable exposure time under extremely hot environments | [Crossref metadata](https://doi.org/10.1016/j.scs.2023.105140) |
| 19 | Hersbach et al., ERA5 global reanalysis | [Journal](https://rmets.onlinelibrary.wiley.com/doi/10.1002/qj.3803) |
| 20 | Open-Meteo Weather API | [Official software citation and DataCite](https://open-meteo.com/en/licence) |
| 21 | Modeling the Wet Bulb Globe Temperature Using Standard Meteorological Measurements | [Crossref metadata](https://doi.org/10.1080/15459620802310770) |
| 22 | Thermofeel: A python thermal comfort indices library | [Crossref metadata](https://doi.org/10.1016/j.softx.2022.101005) |
| 23 | Rothfusz, Heat Index equation | [NOAA technical documentation](https://www.wpc.ncep.noaa.gov/heat_index/details_hi.html) |
| 24 | ISO 7933:2023 | [ISO catalogue](https://www.iso.org/standard/78240.html) |
| 25 | pythermalcomfort: A Python package for thermal comfort research | [Crossref metadata](https://doi.org/10.1016/j.softx.2020.100578) |
| 26 | Exercise and Fluid Replacement | [Crossref metadata](https://doi.org/10.1249/mss.0b013e31802ca597) |
| 27 | Self-Pacing as a Protective Mechanism against the Effects of Heat Stress | [Crossref metadata](https://doi.org/10.1093/annhyg/mer012) |
| 28 | Heat exposure, heat strain, and off-work recovery of Guatemalan sugarcane workers | [Crossref metadata](https://doi.org/10.1152/ajpregu.00004.2025) |
| 29 | ILO/FAME Laboratory, Qatar field study | [ILO report](https://www.ilo.org/publications/assessment-occupational-heat-strain-and-mitigation-strategies-qatar) |
| 30 | Pedregosa et al., scikit-learn | [Journal](https://jmlr.org/papers/v12/pedregosa11a.html) |
| 31 | Leakage and the reproducibility crisis in machine-learning-based science | [Crossref metadata](https://doi.org/10.1016/j.patter.2023.100804) |
| 32 | Enhancing the explanatory power of usability heuristics | [Crossref metadata](https://doi.org/10.1145/191666.191729) |
| 33 | Masterton and Richardson, Humidex | [Environment Canada report](https://publications.gc.ca/collections/collection_2018/eccc/En57-23-1-79-eng.pdf) |
| 34 | Havenith et al., PROSPIE dataset | [Repository metadata and DataCite](https://api.figshare.com/v2/articles/26076577/versions/1) |
| 35 | Comparing thermal strain in outdoor maintenance and indoor service workers in the mining industry during summer | [Crossref metadata](https://doi.org/10.1371/journal.pone.0292436) |
