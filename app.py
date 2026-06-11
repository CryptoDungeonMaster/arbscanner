"""Vercel web entrypoint — landing page for the arb scanner repo."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Arb Scanner")

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Arb Scanner</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 3rem auto; padding: 0 1.5rem; line-height: 1.6; color: #111; }
    code, pre { background: #f4f4f5; border-radius: 6px; }
    code { padding: 0.15rem 0.35rem; }
    pre { padding: 1rem; overflow-x: auto; }
    a { color: #0969da; }
    .note { background: #fff8c5; border: 1px solid #d4a72c; padding: 1rem; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>Sports Betting Arbitrage Scanner</h1>
  <p>This site is the project home page. The scanner runs as a Python app on your machine (or Streamlit Cloud for the dashboard).</p>
  <div class="note">
    <strong>Run locally</strong>
    <pre>git clone https://github.com/CryptoDungeonMaster/arbscanner.git
cd arbscanner
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
copy .env.example .env
python scan.py --once --platforms polymarket,cloudbet
streamlit run dashboard.py</pre>
  </div>
  <p><a href="https://github.com/CryptoDungeonMaster/arbscanner">View source on GitHub</a></p>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return HTML


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "arb-scanner",
        "note": "Scanner runs locally; this endpoint is informational only.",
        "github": "https://github.com/CryptoDungeonMaster/arbscanner",
    }
