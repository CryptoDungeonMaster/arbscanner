"""Conceptual crypto deposit/withdrawal helpers for cross-platform bankroll management.

NOT production wallet code — use official platform UIs and audited bridges.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Chain(str, Enum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    TRON = "tron"
    BSC = "bsc"
    BITCOIN = "bitcoin"


@dataclass
class PlatformWallet:
    platform: str
    supported_assets: list[str]
    preferred_chain: Chain
    deposit_notes: str


PLATFORM_WALLETS: dict[str, PlatformWallet] = {
    "polymarket": PlatformWallet(
        platform="polymarket",
        supported_assets=["USDC"],
        preferred_chain=Chain.POLYGON,
        deposit_notes="Bridge USDC to Polygon via official Polymarket deposit flow.",
    ),
    "stake": PlatformWallet(
        platform="stake",
        supported_assets=["BTC", "ETH", "USDT", "LTC", "DOGE"],
        preferred_chain=Chain.ETHEREUM,
        deposit_notes="Multi-chain deposits; confirm network before sending USDT.",
    ),
    "bcgame": PlatformWallet(
        platform="bcgame",
        supported_assets=["BTC", "ETH", "USDT", "100+ altcoins"],
        preferred_chain=Chain.BSC,
        deposit_notes="Use platform-generated deposit address; verify chain tag.",
    ),
    "cloudbet": PlatformWallet(
        platform="cloudbet",
        supported_assets=["BTC", "ETH", "USDT", "BCH"],
        preferred_chain=Chain.BITCOIN,
        deposit_notes="BTC deposits require 1+ confirmations before crediting.",
    ),
}


def estimate_transfer_fee(asset: str, chain: Chain) -> float:
    """Rough USD fee estimates for planning (not live quotes)."""
    estimates = {
        (Chain.BITCOIN, "BTC"): 3.0,
        (Chain.ETHEREUM, "ETH"): 2.0,
        (Chain.ETHEREUM, "USDT"): 5.0,
        (Chain.POLYGON, "USDC"): 0.05,
        (Chain.TRON, "USDT"): 1.0,
        (Chain.BSC, "USDT"): 0.30,
    }
    return estimates.get((chain, asset.upper()), 2.0)


def min_viable_arb_bankroll(
    platforms: list[str],
    arb_stake: float,
    buffer_pct: float = 20.0,
) -> dict[str, float]:
    """Suggest per-platform balance needed to cover arb legs + fees."""
    per_platform = arb_stake / max(len(platforms), 1)
    buffer = 1 + buffer_pct / 100
    return {p: round(per_platform * buffer, 2) for p in platforms}