# NASA Space Apps 2026 — submission texts (English)

Copy each block into the matching field of the project page. Everything the form asks for must be in English.
Items in **[brackets]** are for you to fill in or confirm before submitting.

Submission window (local time of your Local Event): opens Sat 14 Nov 2026 9:00, closes Sun 15 Nov 2026 23:59.
Submission is final.

---

## Team Name

BioSpace Systems

## Project Name

BioSpace

## High-Level Project Summary

BioSpace is an offline health-monitoring copilot for astronauts on long missions. It learns each astronaut's
own baseline over 30 days, flags deviations across 16 indicators in 7 physiological systems, explains every
alert in plain language, tracks the follow-up action, and automatically escalates to the medical team if
nobody acts. On Moon and Mars missions, with delayed or absent ground contact, the crew member becomes
the first line of health surveillance; BioSpace gives them a tool that works with no network and produces a
ready-to-send medical report when the link returns. On simulated missions, it detected 7 of 7 anomaly
scenarios in 100 % of runs, with 4.5 % of days showing a false alert on a nominal mission.

## Link to Project Demo

**[Public link to your 30-second video (English subtitles) OR a deck of at most 7 slides in English — see the
plan below. Test the link in a private window.]**

## Link to Final Project

https://github.com/djohozinc-ship-it/NASA-Challenge

(Public repository, no password or registration needed. Quick start: `pip install -r requirements.txt`, then
`python launcher.py`.)

## Detailed Project Description

**The problem.** On long-duration missions, communication with Earth is delayed or interrupted, so astronauts
must notice many of their own health changes. A fixed population norm is a poor yardstick in spaceflight:
what matters is how an astronaut deviates from *their own* normal.

**What BioSpace does.**
- **Personal baseline.** The first 30 days set each indicator's mean and standard deviation.
- **16 indicators, 7 systems:** cardiovascular (resting heart rate, HRV, systolic pressure), bone and muscle,
  neuro-ocular (visual acuity, relevant to spaceflight-associated neuro-ocular syndrome), spine, blood and
  immunity, radiation (dose rate), and behaviour (sleep, mood, stress, social contact).
- **Detection.** 7-day smoothing, a z-score corrected for the uncertainty of the baseline, oriented towards the
  dangerous direction of each indicator, and a persistence rule (3 consecutive days) so an isolated spike does not
  raise an alarm. Orange from 2.5, red from 4.0. Absolute safety thresholds (for example systolic pressure
  below 80 or above 160 mmHg, temperature above 38.5 °C) turn a system red immediately, even during calibration.
- **Explained alerts and action loop.** Every alert states why it fired, which indicator drives it and what to do.
  Actions are tracked (to do, done, postponed, reported to the medical team); without action, the alert escalates
  automatically (1 day for red, 3 days for orange) and closes after 3 consecutive normal days.
- **Medical report.** PDF and CSV exports are generated locally for the medical team.
- **Input.** Guided daily check-in (about one minute, partial entries accepted) and validated CSV import.
- **Offline by design.** Local SQLite storage, no telemetry. Only the optional NASA Data tab uses the network.

**Measured, not claimed.** A Validation tab runs simulated missions with random seeds distinct from the demo.
With 40 missions per scenario: 4.5 % of days with an alert on a nominal mission (0.02 % red); 7 of 7 anomaly
scenarios detected in every mission; median detection delays from 2 days (solar particle event) to 34 days
(isolation), for deliberately slow 150-day drifts. The automated test suite (85 tests) and a code review caught and
fixed two weaknesses: a perfectly regular baseline could disable an indicator, and low blood pressure was not
monitored.

**Tools and technologies.** Python, Streamlit, pandas, NumPy, Plotly, SQLite, ReportLab, PyInstaller
(standalone executable), pytest and GitHub Actions.

**Limitations (stated openly).** Thresholds are illustrative and not clinically validated. The detector runs on
synthetic or self-reported data. The reference period is fixed at 30 days. BioSpace is not a medical device.
Next steps: a physician-validated adaptive baseline, real wearable sensors, encrypted sync with the ground, and
multi-crew support.

## NASA Data

BioSpace's detector is driven by **synthetic and self-reported daily data**, because continuous in-flight
physiological series from astronauts are not openly available. NASA research data shaped the design and is
integrated as a read-only browser:

- **NASA Open Science Data Repository (OSDR)** public API: the *NASA Data* tab lists public human studies and
  their files on demand, and previews small tables. Studies referenced: Inspiration4 (OSD-569 whole blood,
  OSD-570 PBMC, OSD-571 plasma, OSD-575 serum metabolic panel and cytokines), OSD-53 (gene expression in
  astronauts) and OSD-484 (plasma exosomes).
- **NASA Spaceflight Standard Measures** and **NASA Life Sciences Portal (NLSP)**: used to choose the monitored
  variables (actigraphy, sleep, cardiovascular, sensorimotor, muscle). Detailed individual data require an
  official request, which BioSpace does not bypass.

OSDR observations are laboratory biomarkers taken at discrete time points; they are never copied into the
profile database and never converted into heart rate, blood pressure or other vital signs.
Details: `docs/NASA_DATA_SOURCES.md` and `REFERENCES.md` in the repository.

**[Before submitting: run `python -m src.nasa_osdr` on your computer. If every step shows OK, keep the sentence
about browsing OSDR as written. If a step fails, say instead that the OSDR browser is an optional, experimental
feature.]**

## Space Agency Partner & Other Data

- NASA OSDR public datasets (CC0 as shown on the OSD-575 study page), accessed through the public API.
- Synthetic mission data generated by the project's own code (`src/generator.py`); every demo profile is labelled
  as a demonstration.
- Open-source libraries: Streamlit, pandas, NumPy, Plotly, ReportLab, Matplotlib, certifi (permissive licences).
- Code released under the MIT licence. No copyrighted images, text or music from third parties.
- **[Add anything else you used: fonts, icons, screenshots of third-party material, music in the video.]**

## Use of Artificial Intelligence

Yes. Generative AI assistants were used during development:

- **ChatGPT (OpenAI):** drafting and correcting portions of Python code, an initial NASA OSDR client, suggestions
  for unit tests and the GitHub Actions workflow, and structuring documentation.
- **Claude (Anthropic), through Claude Code:** code review of the detection logic (two weaknesses found and fixed
  with regression tests), hardening of the NASA OSDR client, interface performance fixes, and drafting the
  English submission texts.

The algorithm itself is a documented statistical method (personal baseline, z-scores, persistence rule), and its
performance was measured by the project's own simulation tests. The code and the scientific claims were reviewed
and tested by the project owner. **[Confirm: no AI-generated images, video, voice or music are used in the demo
and screenshots. If any are, they need a visible AI watermark (images/video) and a mention here (audio).]**
AI was not used to create or modify NASA branding.

---

## 30-second video script (English subtitles required)

| Time | On screen | Caption / voice |
|---|---|---|
| 0–5 s | Home page, "offline mode" badge | "On Mars, there is no real-time link to Earth. Astronauts must watch their own health." |
| 5–12 s | Infection-scenario profile: red banner, radar chart | "BioSpace learns each astronaut's own normal and flags deviations by body system." |
| 12–19 s | Actions tab: explained alert card, then escalation toast | "Every alert explains why and what to do. No action? It escalates to the medical team." |
| 19–25 s | Validation tab | "Measured on simulated missions: 7 of 7 anomaly scenarios detected, 4.5 % false-alert days." |
| 25–30 s | Report tab, PDF, logo/title | "A medical report, ready when the link returns. BioSpace." |

## 7-slide deck plan (English, title slide counts)

1. **Title** — BioSpace: an offline health copilot for astronauts. Team name, challenge name.
2. **Problem** — Long missions, delayed contact: the crew is the first line of health surveillance.
3. **Idea** — Compare each astronaut with their own baseline; 16 indicators, 7 body systems.
4. **How it works** — Baseline → smoothing → z-score → 3-day persistence → orange / red → action → escalation (one diagram).
5. **Demo** — 2–3 real screenshots: alert with explanation, action tracking, medical report.
6. **Results** — Validation table: 7/7 scenarios detected, 4.5 % false-alert days, delays 2–34 days; limitations stated.
7. **NASA data and next steps** — OSDR browser, Standard Measures; roadmap: real sensors, clinical validation, multi-crew.

## Final checklist

- [ ] `python -m src.nasa_osdr` run on your computer; the NASA Data paragraph matches what works
- [ ] Screenshots taken from the real app (JPG, PNG or GIF, 10 MB max each), no personal data
- [ ] Video (30 s, English subtitles) or deck (7 slides, English) hosted with a **public** link, tested in a private window
- [ ] Team name and team members confirmed at the same Local Event
- [ ] AI paragraph checked (images, video, audio)
- [ ] "Terms and Conditions" and "Confirm All Work is Original" boxes ticked, then "Submit for Judging"
