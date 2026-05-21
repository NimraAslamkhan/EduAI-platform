# EduAI Platform — Streamlit UI

This repository contains the EduAI Platform Streamlit UI with a modern dark theme, neon highlights, glassmorphism cards, Plotly charts, and reusable components ready for Streamlit Cloud deployment.

Quick start (local):

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Environment & deployment:
- Use `.env` or Streamlit Cloud secrets to store API keys (`OPENAI_API_KEY`, `DATABASE_URL`, etc.).
- Streamlit config lives in `.streamlit/config.toml` (dark theme preset).

Recommended next steps:
- Review `.env.example` and provide real credentials.
- Deploy to Streamlit Cloud by connecting this repo and setting secrets via the Streamlit Cloud UI.
