"""Thunderpick esports/sports scraper."""

from __future__ import annotations

from typing import Any

from models.odds import Platform, ScrapedEvent, Sport
from scrapers.playwright_base import PlaywrightScraper, parse_generic_odds_json


class ThunderpickScraper(PlaywrightScraper):
    platform = Platform.THUNDERPICK
    fee_pct = 1.0
    base_url = "https://thunderpick.io/sports"
    api_patterns = ["/api/", "/matches", "/odds", "/graphql"]

    def _parse_intercepted(self, captured: list[dict[str, Any]]) -> list[ScrapedEvent]:
        events: list[ScrapedEvent] = []
        for entry in captured:
            parsed = parse_generic_odds_json(entry["data"], Platform.THUNDERPICK, Sport.ESPORTS)
            events.extend(parsed)
        return events