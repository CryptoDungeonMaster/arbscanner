"""Core data models for odds, events, and arbitrage opportunities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Platform(str, Enum):
    POLYMARKET = "polymarket"
    STAKE = "stake"
    BCGAME = "bcgame"
    SHUFFLE = "shuffle"
    CLOUDBET = "cloudbet"
    TGCASINO = "tgcasino"
    THUNDERPICK = "thunderpick"
    THE_ODDS_API = "the_odds_api"


class Sport(str, Enum):
    SOCCER = "soccer"
    NBA = "nba"
    TENNIS = "tennis"
    NFL = "nfl"
    NHL = "nhl"
    MLB = "mlb"
    MMA = "mma"
    ESPORTS = "esports"
    OTHER = "other"


@dataclass
class MarketOutcome:
    """A single bettable outcome within an event."""

    name: str
    decimal_odds: float
    american_odds: int | None = None
    implied_prob: float | None = None
    liquidity_usd: float | None = None
    token_id: str | None = None  # Polymarket CLOB token
    selection_id: str | None = None
    url: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.implied_prob is None and self.decimal_odds > 0:
            self.implied_prob = 1.0 / self.decimal_odds


@dataclass
class ScrapedEvent:
    """Raw event fetched from a platform scraper."""

    platform: Platform
    sport: Sport
    event_id: str
    home_team: str
    away_team: str
    league: str
    start_time: datetime | None
    market_type: str  # e.g. "moneyline", "1x2", "totals", "prediction"
    outcomes: list[MarketOutcome]
    url: str | None = None
    is_live: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        if self.home_team and self.away_team:
            return f"{self.home_team} vs {self.away_team}"
        return self.home_team or self.away_team or self.event_id


@dataclass
class NormalizedOdds:
    """Platform-agnostic normalized odds record."""

    platform: Platform
    sport: Sport
    event_key: str
    home_team: str
    away_team: str
    league: str
    start_time: datetime | None
    market_type: str
    outcome_name: str
    decimal_odds: float
    american_odds: int
    implied_prob: float
    fee_adjusted_prob: float
    liquidity_usd: float | None
    url: str | None
    event_id: str
    selection_id: str | None = None
    token_id: str | None = None


@dataclass
class EventMatch:
    """A group of scraped events believed to represent the same real-world fixture."""

    match_id: str
    sport: Sport
    home_team: str
    away_team: str
    league: str
    start_time: datetime | None
    events: list[ScrapedEvent]
    confidence: float


@dataclass
class StakeAllocation:
    """Recommended stake for one leg of an arbitrage."""

    platform: Platform
    outcome_name: str
    decimal_odds: float
    stake: float
    potential_return: float
    url: str | None
    fee_pct: float


@dataclass
class ArbitrageOpportunity:
    """Detected arbitrage with stake sizing."""

    match_id: str
    sport: Sport
    event_name: str
    league: str
    market_type: str
    profit_pct: float
    total_stake: float
    guaranteed_return: float
    guaranteed_profit: float
    legs: list[StakeAllocation]
    detected_at: datetime
    min_liquidity_usd: float | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "match_id": self.match_id,
            "sport": self.sport.value,
            "event_name": self.event_name,
            "league": self.league,
            "market_type": self.market_type,
            "profit_pct": round(self.profit_pct, 4),
            "total_stake": round(self.total_stake, 2),
            "guaranteed_return": round(self.guaranteed_return, 2),
            "guaranteed_profit": round(self.guaranteed_profit, 2),
            "detected_at": self.detected_at.isoformat(),
            "min_liquidity_usd": self.min_liquidity_usd,
            "warnings": self.warnings,
            "legs": [
                {
                    "platform": leg.platform.value,
                    "outcome": leg.outcome_name,
                    "odds": leg.decimal_odds,
                    "stake": round(leg.stake, 2),
                    "return": round(leg.potential_return, 2),
                    "url": leg.url,
                    "fee_pct": leg.fee_pct,
                }
                for leg in self.legs
            ],
        }