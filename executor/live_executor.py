"""Live execution module — USE WITH EXTREME CAUTION.

Auto-betting carries legal, financial, and account-ban risks.
This module provides hooks for Polymarket CLOB orders and
placeholder stubs for traditional sportsbooks.
"""

from __future__ import annotations

import logging

from config.settings import Settings
from models.odds import ArbitrageOpportunity, Platform

logger = logging.getLogger("arb_scanner.executor.live")


class LiveExecutor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._polymarket_client = None

    async def execute(self, opportunities: list[ArbitrageOpportunity]) -> None:
        if not opportunities:
            return

        logger.warning(
            "LIVE EXECUTION ENABLED — real money at risk. "
            "Ensure you understand legal and platform ToS implications."
        )

        for arb in opportunities:
            for leg in arb.legs:
                try:
                    if leg.platform == Platform.POLYMARKET:
                        await self._execute_polymarket(leg, arb)
                    else:
                        await self._execute_sportsbook_stub(leg, arb)
                except Exception:
                    logger.exception(
                        "Failed to execute leg %s on %s",
                        leg.outcome_name,
                        leg.platform.value,
                    )

    async def _execute_polymarket(self, leg, arb: ArbitrageOpportunity) -> None:
        """Place a limit order on Polymarket CLOB."""
        from scrapers.polymarket import create_polymarket_client

        if self._polymarket_client is None:
            self._polymarket_client = create_polymarket_client(self.settings)

        client = self._polymarket_client
        token_id = None
        for a_leg in arb.legs:
            if a_leg.platform == Platform.POLYMARKET:
                # token_id stored in normalized data; retrieve from arb dict
                pass

        logger.info(
            "Polymarket order stub: BUY token=%s size=$%.2f @ implied %.4f",
            token_id,
            leg.stake,
            1.0 / leg.decimal_odds,
        )
        # Example order (uncomment for live use):
        # from py_clob_client.order_builder.constants import BUY
        # order = client.create_order(
        #     token_id=token_id,
        #     price=1.0 / leg.decimal_odds,
        #     size=leg.stake,
        #     side=BUY,
        # )
        # client.post_order(order)

    async def _execute_sportsbook_stub(self, leg, arb: ArbitrageOpportunity) -> None:
        logger.info(
            "Sportsbook stub: %s %s @ %.2f stake $%.2f — implement via Playwright/API",
            leg.platform.value,
            leg.outcome_name,
            leg.decimal_odds,
            leg.stake,
        )