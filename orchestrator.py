"""Main scan loop — coordinates scrapers, matching, and notifications."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from calculator.arb_calculator import ArbCalculator
from config.settings import Settings
from executor.live_executor import LiveExecutor
from executor.paper_trader import PaperTrader
from matcher.event_matcher import EventMatcher
from models.odds import ArbitrageOpportunity, ScrapedEvent
from normalizer.odds_normalizer import OddsNormalizer
from notifier.console import ConsoleNotifier
from notifier.telegram import TelegramNotifier
from scrapers.registry import build_scrapers

logger = logging.getLogger("arb_scanner.orchestrator")


class ArbOrchestrator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.scrapers = build_scrapers(settings)
        self.normalizer = OddsNormalizer(
            default_fee_pct=settings.default_platform_fee_pct,
            slippage_pct=settings.slippage_pct,
        )
        self.matcher = EventMatcher(
            threshold=settings.fuzzy_match_threshold,
            max_time_diff_minutes=settings.max_event_time_diff_minutes,
        )
        self.calculator = ArbCalculator(
            min_profit_pct=settings.min_profit_pct,
            bankroll=settings.default_bankroll,
            default_fee_pct=settings.default_platform_fee_pct,
            slippage_pct=settings.slippage_pct,
            liquidity_buffer_pct=settings.liquidity_buffer_pct,
        )
        self.console = ConsoleNotifier()
        self.telegram = TelegramNotifier(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
            enabled=settings.telegram_enabled,
        )
        self.paper_trader = PaperTrader(settings.arb_history_path)
        self.live_executor = LiveExecutor(settings)
        self._latest_opportunities: list[ArbitrageOpportunity] = []
        self._latest_events: list[ScrapedEvent] = []

    @property
    def latest_opportunities(self) -> list[ArbitrageOpportunity]:
        return self._latest_opportunities

    @property
    def latest_events(self) -> list[ScrapedEvent]:
        return self._latest_events

    async def run_once(self) -> list[ArbitrageOpportunity]:
        logger.info("Starting scan cycle across %d platforms", len(self.scrapers))

        # Fetch from all platforms concurrently
        tasks = [scraper.safe_fetch() for scraper in self.scrapers]
        results = await asyncio.gather(*tasks)
        all_events: list[ScrapedEvent] = []
        for platform_events in results:
            all_events.extend(platform_events)

        self._latest_events = all_events
        logger.info("Total events fetched: %d", len(all_events))

        # Normalize
        normalized = self.normalizer.normalize_all(all_events)
        logger.debug("Normalized %d outcome records", len(normalized))

        # Match cross-platform events
        matches = self.matcher.match_events(all_events)

        # Detect cross-platform arbs
        cross_arbs = self.calculator.find_arbitrages(matches)

        # Detect intra-platform arbs (especially Polymarket)
        intra_arbs = self.calculator.find_intra_platform_arbs(all_events)

        # Deduplicate by match_id
        seen: set[str] = set()
        opportunities: list[ArbitrageOpportunity] = []
        for arb in cross_arbs + intra_arbs:
            if arb.match_id not in seen:
                seen.add(arb.match_id)
                opportunities.append(arb)

        opportunities.sort(key=lambda a: a.profit_pct, reverse=True)
        self._latest_opportunities = opportunities

        # Output
        self.console.notify(opportunities)
        await self.telegram.notify(opportunities)
        self._write_json_log(opportunities)

        # Execute
        if self.settings.execution_mode == "paper" or self.settings.paper_trading:
            await self.paper_trader.execute(opportunities)
        elif self.settings.auto_execute:
            await self.live_executor.execute(opportunities)

        return opportunities

    async def run_loop(self) -> None:
        logger.info(
            "Arb scanner running. Refresh: %ds, min profit: %.1f%%",
            self.settings.refresh_interval_seconds,
            self.settings.min_profit_pct,
        )
        while True:
            try:
                await self.run_once()
            except Exception:
                logger.exception("Scan cycle failed")
            await asyncio.sleep(self.settings.refresh_interval_seconds)

    def _write_json_log(self, opportunities: list[ArbitrageOpportunity]) -> None:
        self.settings.json_log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "platforms": self.settings.enabled_platforms,
            "event_count": len(self._latest_events),
            "opportunity_count": len(opportunities),
            "opportunities": [arb.to_dict() for arb in opportunities],
        }
        with open(self.settings.json_log_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        logger.info("Wrote JSON log to %s", self.settings.json_log_path)