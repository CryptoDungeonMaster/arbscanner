"""Optional aggregator via The Odds API (the-odds-api.com)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from models.odds import MarketOutcome, Platform, ScrapedEvent, Sport
from scrapers.base import BaseScraper

SPORT_KEY_MAP: dict[str, str] = {
    "soccer": "soccer_epl",
    "nba": "basketball_nba",
    "tennis": "tennis_atp_french_open",
    "nfl": "americanfootball_nfl",
    "nhl": "icehockey_nhl",
    "mlb": "baseball_mlb",
}

SPORT_ENUM: dict[str, Sport] = {
    "soccer": Sport.SOCCER,
    "nba": Sport.NBA,
    "tennis": Sport.TENNIS,
    "nfl": Sport.NFL,
    "nhl": Sport.NHL,
    "mlb": Sport.MLB,
}


class TheOddsApiScraper(BaseScraper):
    platform = Platform.THE_ODDS_API
    fee_pct = 0.0

    async def fetch_events(self) -> list[ScrapedEvent]:
        if not self.settings.the_odds_api_key:
            return []

        events: list[ScrapedEvent] = []
        base = self.settings.the_odds_api_url.rstrip("/")

        for watched in self.settings.sports_list:
            sport_key = SPORT_KEY_MAP.get(watched)
            if not sport_key:
                continue
            params = {
                "apiKey": self.settings.the_odds_api_key,
                "regions": "us,eu,uk,au",
                "markets": "h2h",
                "oddsFormat": "decimal",
            }
            try:
                data = await self.http.get(f"{base}/sports/{sport_key}/odds", params=params)
                sport = SPORT_ENUM.get(watched, Sport.OTHER)
                events.extend(self._parse(data, sport))
            except Exception:
                self.logger.warning("The Odds API fetch failed for %s", watched)
        return events

    def _parse(self, data: list[dict[str, Any]], sport: Sport) -> list[ScrapedEvent]:
        results: list[ScrapedEvent] = []
        for item in data:
            home = item.get("home_team", "")
            away = item.get("away_team", "")
            start_time = None
            if item.get("commence_time"):
                start_time = datetime.fromisoformat(
                    item["commence_time"].replace("Z", "+00:00")
                )

            for bookmaker in item.get("bookmakers") or []:
                for market in bookmaker.get("markets") or []:
                    if market.get("key") != "h2h":
                        continue
                    outcomes: list[MarketOutcome] = []
                    for outcome in market.get("outcomes") or []:
                        price = outcome.get("price")
                        if price and price > 1:
                            outcomes.append(
                                MarketOutcome(
                                    name=outcome.get("name", ""),
                                    decimal_odds=float(price),
                                    raw=outcome,
                                )
                            )
                    if len(outcomes) < 2:
                        continue
                    results.append(
                        ScrapedEvent(
                            platform=Platform.THE_ODDS_API,
                            sport=sport,
                            event_id=item.get("id", ""),
                            home_team=home,
                            away_team=away,
                            league=sport.value,
                            start_time=start_time,
                            market_type="moneyline",
                            outcomes=outcomes,
                            url=item.get("sport_key"),
                            raw={"bookmaker": bookmaker.get("key"), "event": item},
                        )
                    )
        return results