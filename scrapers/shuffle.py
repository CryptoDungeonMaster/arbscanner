"""Shuffle.com sports scraper."""

from __future__ import annotations

from typing import Any

from models.odds import Platform, ScrapedEvent
from scrapers.playwright_base import PlaywrightScraper, parse_generic_odds_json


class ShuffleScraper(PlaywrightScraper):
    platform = Platform.SHUFFLE
    fee_pct = 1.0
    base_url = "https://shuffle.com/sports"
    api_patterns = ["/api/", "/sports/", "/events"]

    def _parse_intercepted(self, captured: list[dict[str, Any]]) -> list[ScrapedEvent]:
        events: list[ScrapedEvent] = []
        for entry in captured:
            events.extend(parse_generic_odds_json(entry["data"], Platform.SHUFFLE))
        return events