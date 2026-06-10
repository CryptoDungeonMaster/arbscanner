"""Stake.com scraper — intercepts internal sports API via Playwright."""

from __future__ import annotations

from typing import Any

from models.odds import Platform, ScrapedEvent, Sport
from scrapers.playwright_base import PlaywrightScraper, parse_generic_odds_json


class StakeScraper(PlaywrightScraper):
    platform = Platform.STAKE
    fee_pct = 0.0
    base_url = "https://stake.com/sports/home"
    api_patterns = ["/api/sports", "/graphql", "/sports/"]

    def _parse_intercepted(self, captured: list[dict[str, Any]]) -> list[ScrapedEvent]:
        events: list[ScrapedEvent] = []
        for entry in captured:
            data = entry["data"]
            if isinstance(data, dict):
                # GraphQL response shape
                if "data" in data:
                    for key, val in data["data"].items():
                        if isinstance(val, list):
                            events.extend(parse_generic_odds_json(val, Platform.STAKE))
                else:
                    events.extend(parse_generic_odds_json(data, Platform.STAKE))
        return events

    async def _fallback_fetch(self) -> list[ScrapedEvent]:
        # Stake has no stable public API; scraping is primary path
        self.logger.info("Stake: no API data captured — ensure proxy/geo access")
        return []