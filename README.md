# 🏗️ Multimodal Construction Intelligence Platform

Skill Wallet Capstone - **Project 1**. A Streamlit app that combines Google Gemini multimodal analysis
with construction-domain calculators. No database, no external services to provision - deploy in one click
on Streamlit Community Cloud.

## Features

| Tab | What it does |
|---|---|
| 🦺 **Site Safety & PPE Audit** | Upload a site photo → structured JSON: `safety_score` (0-100), `overall_status`, PPE checklist (helmet, hi-vis vest, steel-toe boots, harness), hazards with severity (Low/Medium/High/Critical) and corrective remedies. Metric cards, status pills, downloadable JSON. |
| 🧱 **Crack Diagnostics** | Upload a concrete/wall photo → defect type (Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling), estimated crack width (mm), root causes, repair methods (epoxy injection, structural re-grouting…), urgency. |
| 📐 **Planning & Valuation** | Structure type, built-up sq ft, location tier, completion slider → total budget, capex incurred, current asset valuation (₹ Lakhs/Crores), steel & cement requirements, milestone progress, plus a conceptual 3D rendering via Pollinations AI. |
| ⛅ **Site Assistant & Weather** | Pick High Wind / Heavy Rain / Extreme Heat / Normal (with an intensity slider) for live safety alerts (crane suspension, electrical hazards, concrete curing protocol), plus a multi-turn engineering chatbot. |

**Demonstration mode:** with no API key the app still runs. Image analyses return clearly labelled *sample*
reports (not an analysis of your upload) and the chatbot answers from a small built-in knowledge base.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Paste your Gemini API key in the sidebar (get one at <https://aistudio.google.com/apikey>), or set it once:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then edit the key (file is git-ignored)
```

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. On <https://share.streamlit.io>, click **New app**, pick the repo, branch `main`, main file `app.py`.
3. *(Optional)* In **Advanced settings → Secrets** add `GEMINI_API_KEY = "your-key"` so visitors don't need their own key.
   Without it, users can paste their own key in the sidebar and otherwise get demo mode.

> ⚠️ Never commit a real API key. `.streamlit/secrets.toml` is in `.gitignore`.

## Project structure

```
app.py                    # page config, sidebar, tab wiring
core/
  gemini_client.py        # Gemini wrapper (retries, friendly errors, demo fallback)
  prompts.py              # all prompt templates
  schemas.py              # normalises/validates model JSON before display
  analysis.py             # live-vs-demo orchestration for image analyses
  valuation.py            # budget / asset value / material maths + render prompt
  weather.py              # weather rules, thresholds and alerts
  demo_data.py            # sample reports + rule-based demo chatbot
  ui.py                   # CSS + HTML components (all text HTML-escaped)
  utils.py                # INR formatting, JSON extraction, image prep
tabs/                     # one Streamlit renderer per feature
tests/test_core.py        # pytest suite for the non-UI logic
```

Run the tests with `pip install pytest && pytest -q`.

## Assumptions & limits (please read)

- **Valuation rates are indicative planning defaults**, not market quotes. They are editable in the app
  (*Advanced → edit rate assumptions*); the methodology is shown in an expander. Steel/cement figures use
  rule-of-thumb intensities per sq ft.
- **AI output can be wrong.** Safety scores and crack diagnoses from a photo are advisory. Structural and
  safety decisions must be verified on site by qualified, licensed professionals. Crack width from a photo
  is only reliable with a scale reference (ruler/crack gauge) in frame.
- Weather thresholds are conservative guides; crane wind limits are set by the manufacturer and the
  competent person on site.
- Uploaded photos are sent to the Gemini API in live mode and are not stored by this app.
- Default models: `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-2.0-flash`. If Google retires a name, choose
  **Custom...** in the sidebar and enter the current model ID.
- The 3D rendering uses the free Pollinations image endpoint, which can be slow or rate-limited; the app
  shows a direct link if generation fails.
