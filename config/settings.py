"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    log_level: str = "INFO"
    refresh_interval_seconds: int = 30
    min_profit_pct: float = 2.0
    default_bankroll: float = 1000.0
    paper_trading: bool = True
    auto_execute: bool = False

    # Fee / slippage assumptions (percent)
    default_platform_fee_pct: float = 2.0
    slippage_pct: float = 1.0
    liquidity_buffer_pct: float = 5.0

    # Watched sports (comma-separated in .env)
    watched_sports: str = "soccer,nba,tennis,nfl,nhl,mlb"

    # Polymarket
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"
    polymarket_data_url: str = "https://data-api.polymarket.com"
    polymarket_private_key: str = ""
    polymarket_api_key: str = ""
    polymarket_api_secret: str = ""
    polymarket_api_passphrase: str = ""

    # The Odds API (optional fallback aggregator)
    the_odds_api_key: str = ""
    the_odds_api_url: str = "https://api.the-odds-api.com/v4"

    # Cloudbet (public, no key required for odds)
    cloudbet_api_url: str = "https://sports-api.cloudbet.com/pub/v2"

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_enabled: bool = False

    # Proxy rotation (comma-separated URLs)
    proxy_list: str = ""
    use_playwright_headless: bool = True
    playwright_timeout_ms: int = 30000

    # Platform toggles
    enable_polymarket: bool = True
    enable_stake: bool = True
    enable_bcgame: bool = True
    enable_shuffle: bool = True
    enable_cloudbet: bool = True
    enable_tgcasino: bool = True
    enable_thunderpick: bool = True

    # Output
    json_log_path: Path = Field(default=PROJECT_ROOT / "data" / "arbs.json")
    arb_history_path: Path = Field(default=PROJECT_ROOT / "data" / "arb_history.jsonl")

    # Matcher
    fuzzy_match_threshold: int = 75
    max_event_time_diff_minutes: int = 120

    # Execution mode
    execution_mode: Literal["paper", "live"] = "paper"

    @field_validator("json_log_path", "arb_history_path", mode="before")
    @classmethod
    def resolve_path(cls, v: str | Path) -> Path:
        p = Path(v)
        return p if p.is_absolute() else PROJECT_ROOT / p

    @model_validator(mode="after")
    def disable_playwright_on_railway(self) -> Settings:
        """Browser scrapers need Chromium + long timeouts; skip on Railway by default."""
        on_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PUBLIC_DOMAIN"))
        if not on_railway:
            return self
        if os.getenv("ENABLE_PLAYWRIGHT_PLATFORMS", "").lower() in ("1", "true", "yes"):
            return self
        self.enable_stake = False
        self.enable_bcgame = False
        self.enable_shuffle = False
        self.enable_tgcasino = False
        self.enable_thunderpick = False
        return self

    @property
    def sports_list(self) -> list[str]:
        return [s.strip().lower() for s in self.watched_sports.split(",") if s.strip()]

    @property
    def proxies(self) -> list[str]:
        return [p.strip() for p in self.proxy_list.split(",") if p.strip()]

    @property
    def enabled_platforms(self) -> list[str]:
        platforms: list[str] = []
        if self.enable_polymarket:
            platforms.append("polymarket")
        if self.enable_stake:
            platforms.append("stake")
        if self.enable_bcgame:
            platforms.append("bcgame")
        if self.enable_shuffle:
            platforms.append("shuffle")
        if self.enable_cloudbet:
            platforms.append("cloudbet")
        if self.enable_tgcasino:
            platforms.append("tgcasino")
        if self.enable_thunderpick:
            platforms.append("thunderpick")
        return platforms


@lru_cache
def get_settings() -> Settings:
    return Settings()