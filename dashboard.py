"""Streamlit dashboard for live arbitrage monitoring.

Usage:
    streamlit run dashboard.py
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import sys
import traceback
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import get_settings
from orchestrator import ArbOrchestrator
from utils.logging import setup_logging

st.set_page_config(page_title="Arb Scanner", page_icon="📊", layout="wide")

settings = get_settings()
setup_logging(settings.log_level)


@st.cache_resource
def get_orchestrator() -> ArbOrchestrator:
    return ArbOrchestrator(settings)


def run_scan(timeout_seconds: int = 120) -> None:
    """Run scan in a worker thread (Streamlit already has an event loop)."""
    orchestrator = get_orchestrator()

    def _run() -> None:
        asyncio.run(orchestrator.run_once())

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run)
        future.result(timeout=timeout_seconds)


def load_scan_data() -> dict | None:
    log_path = settings.json_log_path
    if not log_path.exists():
        return None
    with open(log_path, encoding="utf-8") as f:
        return json.load(f)


st.title("Sports Betting Arbitrage Scanner")
st.caption(f"Platforms: {', '.join(settings.enabled_platforms)} | Min profit: {settings.min_profit_pct}%")

if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    st.info(
        "Running on Railway with API-only mode (Polymarket + Cloudbet). "
        "Browser bookmakers are disabled unless you set ENABLE_PLAYWRIGHT_PLATFORMS=true."
    )

col1, col2, col3 = st.columns(3)
with col1:
    scan_clicked = st.button("Scan Now", type="primary")
with col2:
    auto_refresh = st.toggle("Auto-refresh", value=False)
with col3:
    refresh_interval = st.number_input("Interval (s)", min_value=10, value=settings.refresh_interval_seconds)

if scan_clicked:
    with st.spinner("Scanning… this can take up to 2 minutes on first run"):
        try:
            run_scan()
            st.session_state["last_scan_error"] = None
            st.success("Scan complete!")
        except concurrent.futures.TimeoutError:
            st.session_state["last_scan_error"] = "Scan timed out after 2 minutes."
            st.error(st.session_state["last_scan_error"])
        except Exception as exc:
            st.session_state["last_scan_error"] = f"{exc}\n\n{traceback.format_exc()}"
            st.error(f"Scan failed: {exc}")

if st.session_state.get("last_scan_error"):
    with st.expander("Last scan error details", expanded=True):
        st.code(st.session_state["last_scan_error"])

if auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="{int(refresh_interval)}">', unsafe_allow_html=True)

data = load_scan_data()
if data:
    st.subheader(f"Last scan: {data.get('scanned_at', 'N/A')}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Events", data.get("event_count", 0))
    m2.metric("Opportunities", data.get("opportunity_count", 0))
    m3.metric("Platforms", len(data.get("platforms", [])))

    by_platform = data.get("events_by_platform") or {}
    if by_platform:
        st.write("**Events by platform:**", ", ".join(f"{k}: {v}" for k, v in sorted(by_platform.items())))
    elif data.get("event_count", 0) == 0:
        st.warning(
            "Scan finished but fetched 0 events. Check Railway logs, or try fewer sports "
            "(WATCHED_SPORTS=soccer,nba) and ensure Polymarket/Cloudbet are enabled."
        )

    opportunities = data.get("opportunities", [])
    if opportunities:
        for arb in opportunities:
            with st.expander(
                f"+{arb['profit_pct']:.2f}% — {arb['event_name']} ({arb['sport']})",
                expanded=arb == opportunities[0],
            ):
                st.write(f"**League:** {arb['league']} | **Market:** {arb['market_type']}")
                st.write(
                    f"**Stake:** ${arb['total_stake']:.2f} → "
                    f"**Return:** ${arb['guaranteed_return']:.2f} → "
                    f"**Profit:** ${arb['guaranteed_profit']:.2f}"
                )
                if arb.get("warnings"):
                    st.warning("; ".join(arb["warnings"]))

                leg_cols = st.columns(len(arb["legs"]))
                for i, leg in enumerate(arb["legs"]):
                    with leg_cols[i]:
                        st.markdown(f"**{leg['platform']}**")
                        st.write(f"{leg['outcome']} @ {leg['odds']:.2f}")
                        st.write(f"Stake: ${leg['stake']:.2f}")
                        if leg.get("url"):
                            st.link_button("Open", leg["url"])
    else:
        st.info("No arbitrage opportunities above threshold.")
else:
    st.info("No scan data yet. Click **Scan Now** to start.")

st.sidebar.header("Configuration")
st.sidebar.write(f"Bankroll: ${settings.default_bankroll}")
st.sidebar.write(f"Paper trading: {settings.paper_trading}")
st.sidebar.write(f"Watched sports: {', '.join(settings.sports_list)}")
st.sidebar.write(f"Active platforms: {', '.join(settings.enabled_platforms)}")

st.sidebar.warning(
    "Arbitrage betting carries legal and financial risks. "
    "Use paper trading mode for testing."
)
