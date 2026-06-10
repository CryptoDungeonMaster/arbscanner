"""Streamlit dashboard for live arbitrage monitoring.

Usage:
    streamlit run dashboard.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config.settings import get_settings
from orchestrator import ArbOrchestrator
from utils.logging import setup_logging

st.set_page_config(page_title="Arb Scanner", page_icon="📊", layout="wide")

settings = get_settings()
setup_logging("WARNING")


@st.cache_resource
def get_orchestrator() -> ArbOrchestrator:
    return ArbOrchestrator(settings)


def run_scan() -> None:
    orchestrator = get_orchestrator()
    asyncio.run(orchestrator.run_once())


st.title("Sports Betting Arbitrage Scanner")
st.caption(f"Platforms: {', '.join(settings.enabled_platforms)} | Min profit: {settings.min_profit_pct}%")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Scan Now", type="primary"):
        with st.spinner("Scanning..."):
            run_scan()
        st.success("Scan complete!")
with col2:
    auto_refresh = st.toggle("Auto-refresh", value=False)
with col3:
    refresh_interval = st.number_input("Interval (s)", min_value=10, value=settings.refresh_interval_seconds)

if auto_refresh:
    st.markdown(f'<meta http-equiv="refresh" content="{int(refresh_interval)}">', unsafe_allow_html=True)

# Load latest JSON log
log_path = settings.json_log_path
if log_path.exists():
    with open(log_path, encoding="utf-8") as f:
        data = json.load(f)

    st.subheader(f"Last scan: {data.get('scanned_at', 'N/A')}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Events", data.get("event_count", 0))
    m2.metric("Opportunities", data.get("opportunity_count", 0))
    m3.metric("Platforms", len(data.get("platforms", [])))

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
    st.info("No scan data yet. Click 'Scan Now' to start.")

st.sidebar.header("Configuration")
st.sidebar.write(f"Bankroll: ${settings.default_bankroll}")
st.sidebar.write(f"Paper trading: {settings.paper_trading}")
st.sidebar.write(f"Watched sports: {', '.join(settings.sports_list)}")

st.sidebar.warning(
    "Arbitrage betting carries legal and financial risks. "
    "Use paper trading mode for testing."
)