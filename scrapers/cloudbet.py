"""Cloudbet public sports API scraper.

Docs: https://www.cloudbet.com/api/
Public endpoint: https://sports-api.cloudbet.com/pub/v2/odds/{sport}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.odds import MarketOutcome, Platform, ScrapedEvent, Sport
from scrapers.base import BaseScraper

SPORT_MAP: dict[str, Sport] = {
    "soccer": Sport.SOCCER,
    "basketball": Sport.NBA,
    "tennis": Sport.TENNIS,
    "american-football": Sport.NFL,
    "ice-hockey": Sport.NHL,
    "baseball": Sport.MLB,
    "mma": Sport.MMA,
}

CLOUDBET_SPORT_KEYS: dict[str, str] = {
    "soccer": "soccer",
    "nba": "basketball",
    "tennis": "tennis",
    "nfl": "american-football",
    "nhl": "ice-hockey",
    "mlb": "baseball",
}


class CloudbetScraper(BaseScraper):
    platform = Platform.CLOUDBET
    fee_pct = 0.0

    async def fetch_events(self) -> list[ScrapedEvent]:
        events: list[ScrapedEvent] = []
        base_url = self.settings.cloudbet_api_url.rstrip("/")

        for watched in self.settings.sports_list:
            cb_sport = CLOUDBET_SPORT_KEYS.get(watched)
            if not cb_sport:
                continue
            try:
                data = await self.http.get(f"{base_url}/odds/{cb_sport}")
                sport = SPORT_MAP.get(cb_sport, Sport.OTHER)
                events.extend(self._parse_response(data, sport, cb_sport))
            except Exception:
                self.logger.warning("Cloudbet fetch failed for %s", watched)
        return events

    def _parse_response(self, data: dict[str, Any], sport: Sport, cb_sport: str) -> list[ScrapedEvent]:
        results: list[ScrapedEvent] = []
        competitions = data.get("competitions") or []

        for comp in competitions:
            league = comp.get("name") or comp.get("key", "")
            for event in comp.get("events") or []:
                home = event.get("home", {}).get("name", "")
                away = event.get("away", {}).get("name", "")
                event_id = str(event.get("id", ""))
                start_time = None
                if event.get("cutoffTime"):
                    start_time = datetime.fromtimestamp(
                        event["cutoffTime"] / 1000, tz=timezone.utc
                    )

                for market in event.get("markets") or []:
                    market_type = market.get("key", "moneyline")
                    if market_type not in ("moneyline", "1x2", "winner"):
                        continue

                    outcomes: list[MarketOutcome] = []
                    for selection in market.get("selections") or []:
                        price = selection.get("price")
                        if not price or price <= 1:
                            continue
                        outcomes.append(
                            MarketOutcome(
                                name=selection.get("name", ""),
                                decimal_odds=float(price),
                                selection_id=str(selection.get("id", "")),
                                url=f"https://www.cloudbet.com/en/sports/{cb_sport}",
                                raw=selection,
                            )
                        )

                    if len(outcomes) < 2:
                        continue

                    results.append(
                        ScrapedEvent(
                            platform=Platform.CLOUDBET,
                            sport=sport,
                            event_id=event_id,
                            home_team=home,
                            away_team=away,
                            league=league,
                            start_time=start_time,
                            market_type=market_type,
                            outcomes=outcomes,
                            url=f"https://www.cloudbet.com/en/sports/{cb_sport}",
                            raw=event,
                        )
                    )
        return results