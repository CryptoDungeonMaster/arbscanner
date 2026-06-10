"""Paper trading — logs simulated bets without placing real wagers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from models.odds import ArbitrageOpportunity

logger = logging.getLogger("arb_scanner.executor.paper")


class PaperTrader:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    async def execute(self, opportunities: list[ArbitrageOpportunity]) -> None:
        if not opportunities:
            return

        for arb in opportunities:
            record = {
                "mode": "paper",
                "executed_at": datetime.now(timezone.utc).isoformat(),
                **arb.to_dict(),
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
            logger.info(
                "PAPER TRADE: %s +%.2f%% ($%.2f profit)",
                arb.event_name,
                arb.profit_pct,
                arb.guaranteed_profit,
            )