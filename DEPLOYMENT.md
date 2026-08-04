# Streamlit Community Cloud Deployment Guide

This guide provides step-by-step instructions for deploying the **Alert Intelligence Engine** presentation layer to **Streamlit Community Cloud** directly from GitHub.

---

## Prerequisites

- A [GitHub](https://github.com/) account containing this repository (`alert-intelligence-engine`).
- An optional Google Gemini API Key (get one from [Google AI Studio](https://aistudio.google.com/)).

---

## Step-by-Step Deployment Instructions

### Step 1: Sign In to Streamlit Community Cloud
1. Navigate to [share.streamlit.io](https://share.streamlit.io/).
2. Click **Continue with GitHub** and authorize Streamlit to access your GitHub repositories.

### Step 2: Create a New App
1. Click the **New app** button in the top right corner.
2. Select **Use existing repo**.

### Step 3: Configure Repository Details
Fill in the deployment configuration form:

- **Repository:** `tkapilkishore-oss/alert-intelligence-engine` (or your fork)
- **Branch:** `main`
- **Main file path:** `app.py`
- **App URL (optional):** Choose a custom slug (e.g. `alert-intelligence-engine`).

### Step 4: Add Environment Secrets
Before clicking Deploy, set up your secrets:

1. Click **Advanced settings...** at the bottom of the form (or navigate to **Settings -> Secrets** after deployment).
2. Under the **Secrets** text box, paste the following snippet:

```toml
# Streamlit Community Cloud Secrets Configuration
GEMINI_API_KEY = "YOUR_ACTUAL_GOOGLE_GEMINI_API_KEY"
```

> **Note:** If `GEMINI_API_KEY` is omitted, the application will still process all structured alert formats (JSON, CAP XML, RSS XML) and plaintext deterministic extractions cleanly. Only Gemini AI fallback enrichment will be skipped with a graceful warning.

### Step 5: Deploy
1. Click **Deploy!**
2. Streamlit Cloud will build the Python environment (using `requirements.txt`) and launch `app.py`.
3. Your app will be live at `https://<your-app-slug>.streamlit.app`.

---

## Environment Verification Checklist

| Check Item | Requirement | Status |
|---|---|---|
| **Entry Point** | `app.py` | Verified |
| **Dependencies** | Listed in `requirements.txt` | Verified |
| **Secrets Configuration** | Defined via Streamlit Secrets (`GEMINI_API_KEY`) | Verified |
| **Dataset Paths** | `Path(__file__).resolve().parent.parent / "data"` | Verified |
| **Engine Code** | Production-frozen (`src/`) | Verified |

---

## Troubleshooting Guide

### Issue 1: `ModuleNotFoundError: No module named 'src'`
- **Cause**: Streamlit working directory shifted.
- **Fix**: The repository imports use package-level relative paths (`from src.pipeline import AlertPipeline`). Streamlit Cloud automatically sets the repository root as `PYTHONPATH`. Ensure `app.py` is selected as the main entry point.

### Issue 2: `Gemini fallback skipped: GEMINI_API_KEY missing`
- **Cause**: Secrets not configured in Streamlit Cloud settings.
- **Fix**: Open your app dashboard on Streamlit Cloud, click **Manage app** (bottom right) -> **Settings** -> **Secrets**, and add `GEMINI_API_KEY = "your_key"`.

### Issue 3: `429 RESOURCE_EXHAUSTED` (Gemini Rate Limit)
- **Cause**: Exceeded Google Gemini API free tier request limits.
- **Fix**: The engine handles 429 quota errors gracefully without crashing, logging a parse warning and displaying processed alerts. Wait 30–60 seconds for quota window reset or provide a paid Gemini API key.

### Issue 4: `FileNotFoundError: data/raw_alerts_json.json`
- **Cause**: Absolute file path reference failure on remote Linux container.
- **Fix**: All sample loading in `ui/utils.py` uses `Path(__file__).resolve().parent.parent / "data"`, ensuring dataset loading succeeds on both local systems and cloud containers.

---

## Summary

The repository is **100% Streamlit Community Cloud ready**. Pushing the latest commit to GitHub and pointing Streamlit Cloud to `app.py` delivers an instant, zero-configuration live deployment.
