# BioSpace — Health monitoring software for astronauts

*Français : [README.md](README.md)*

Response to the **NASA Space Apps 2026 challenge: "Create health monitoring software for astronauts on
space missions"**.

On long missions (Moon, Mars) the astronaut must spot many of their own health changes without real-time
ground support. BioSpace gathers the astronaut's indicators, **learns their personal normal**, detects
deviations per physiological system, explains every alert, tracks the follow-up actions and prepares a
report for the medical team. Everything runs **offline**.

> Synthetic or self-reported data, illustrative thresholds. Not a medical device and not medical advice.

## Features

| | |
|---|---|
| **Personal baseline** | Each astronaut is compared with themselves (30-day calibration), not with a population norm. |
| **16 indicators, 7 systems** | Cardiovascular, bone and muscle, neuro-ocular (SANS), spine, blood and immunity, radiation, behaviour. |
| **Daily check-in** | Guided one-minute entry, range-validated, partial entries accepted. |
| **CSV import** | Row-by-row validation with a rejection report, decimal comma accepted. |
| **Absolute critical thresholds** | A dangerous value turns a system red immediately, even during calibration (e.g. systolic pressure < 80 or > 160 mmHg). |
| **Explained action cards** | Why the alert fired, which indicator drives it, what to do. |
| **Tracked action loop** | To do, done, postponed, reported. Automatic escalation to the medical team if nobody acts. |
| **Medical report** | PDF and CSV exports generated locally. |
| **Local persistence** | SQLite database, multiple profiles, event log, one-click backup. |
| **NASA data** | Optional, on-demand browser for public NASA OSDR human studies and their files. |
| **Measured validation** | A dedicated tab measures false alarms and detection delay on simulated missions. |

## Quick start

```bash
pip install -r requirements.txt
python launcher.py          # opens the browser; or: streamlit run app.py
```

No data-generation step: on first launch, create a profile in the sidebar. Choose **Demonstration** for a
simulated scenario, or **Real profile** to enter or import your own data.
Tests: `python -m pytest`. NASA OSDR connection diagnostic: `python -m src.nasa_osdr`.

## Method

1. **Calibration** — the first 30 days set each indicator's mean and standard deviation (with a realistic
   minimum standard deviation per indicator, so a very regular baseline cannot disable the indicator).
2. **Smoothing** — 7-day rolling mean, missing measurements tolerated.
3. **Deviation** — z-score normalised by `σ · √(1/n + 1/n_ref)`, oriented towards the dangerous direction of
   each indicator (both directions for blood pressure).
4. **Persistence** — a deviation must last 3 consecutive days (an isolated spike is ignored).
5. **System state** — the worst indicator of the system. Orange from 2.5, red from 4.0.
6. **Follow-up** — an alert escalates after 1 day (red) or 3 days (orange) without action, and closes after
   3 consecutive days below the threshold.

## Validation results

Measured on 40 simulated missions per scenario (seeds distinct from the demo), 144 evaluated days per
mission after calibration. Reproducible in the **Validation** tab.

- Nominal mission: **4.5 % of days** with at least one orange or red system, **0.02 %** red
  (4.8 % and 0.02 % with 10 % missing measurements).
- **7 of 7 anomaly scenarios detected in 100 % of missions.**

| Scenario | System | Median detection delay |
|---|---|---|
| Solar particle event (3-day peak) | Radiation | 2 days |
| Infection episode | Blood and immunity | 3 days |
| Cardiovascular drift | Cardiovascular | 16 days |
| Deconditioning | Bone and muscle | 20 days |
| Neuro-ocular risk (SANS) | Neuro-ocular | 26 days |
| Sleep and stress degradation | Behaviour | 31 days |
| Isolation and confinement | Behaviour | 34 days |

Simulated drifts are slow (150 days): a 30-day delay corresponds to a still-small deviation. Absolute
critical thresholds are not included in these measurements.

## NASA data

The detector runs on **synthetic and self-reported daily data**. NASA data inspired the design and is
browsable in the app: the **NASA Data** tab queries the public NASA OSDR API on demand (for example
Inspiration4 studies OSD-569, OSD-570, OSD-571, OSD-575, and OSD-53, OSD-484) and previews small public tables.
These observations are not copied into the profile database and are never converted into vital signs
(see [docs/NASA_DATA_SOURCES.md](docs/NASA_DATA_SOURCES.md)). Daily in-flight physiological series from the
NASA Standard Measures programme require an official data request; BioSpace does not bypass these controls.

## Limitations

Illustrative thresholds without clinical validation; fixed 30-day reference; synthetic demonstration data;
general non-medical advice; haemoglobin and symptoms are proxies or self-reports. Next steps: a
physician-validated adaptive baseline, real sensors, encrypted sync with the ground when the link returns,
multi-crew support.

## Project documents

[MIT licence](LICENSE) · [References](REFERENCES.md) · [AI usage](AI_USAGE.md) ·
[NASA data sources](docs/NASA_DATA_SOURCES.md) · [Demo guide](DEMO.md) · [Submission texts](SUBMISSION_EN.md)
