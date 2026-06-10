"""BC.Game sports scraper."""

from __future__ import annotations

from typing import Any

from models.odds import Platform, ScrapedEvent
from scrapers.playwright_base import PlaywrightScraper, parse_generic_odds_json


class BCGameScraper(PlaywrightScraper):
    platform = Platform.BCGAME
    fee_pct = 1.0
    base_url = "https://bc.game/sports"
    api_patterns = ["/api/", "/sports/", "/odds"]

    def _parse_intercepted(self, captured: list[dict[str, Any]]) -> list[ScrapedEvent]:
        events: list[ScrapedEvent] = []
        for entry in captured:
            events.extend(parse_generic_odds_json(entry["data"], Platform.BCGAME))
        return events