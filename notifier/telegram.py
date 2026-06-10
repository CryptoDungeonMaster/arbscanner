"""Telegram alert notifications."""

from __future__ import annotations

import logging

import httpx

from models.odds import ArbitrageOpportunity

logger = logging.getLogger("arb_scanner.notifier.telegram")


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, enabled: bool = True) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = enabled and bool(bot_token and chat_id)

    async def notify(self, opportunities: list[ArbitrageOpportunity]) -> None:
        if not self.enabled or not opportunities:
            return

        for arb in opportunities[:5]:  # Limit to top 5 per cycle
            message = self._format_message(arb)
            await self._send(message)

    def _format_message(self, arb: ArbitrageOpportunity) -> str:
        lines = [
            f"ARB ALERT: +{arb.profit_pct:.2f}%",
            f"{arb.event_name} ({arb.sport.value})",
            f"League: {arb.league}",
            f"Stake: ${arb.total_stake:.2f} -> Profit: ${arb.guaranteed_profit:.2f}",
            "",
            "Legs:",
        ]
        for leg in arb.legs:
            url = leg.url or "N/A"
            lines.append(
                f"  {leg.platform.value}: {leg.outcome_name} "
                f"@ {leg.decimal_odds:.2f} (${leg.stake:.2f})"
            )
            lines.append(f"    {url}")
        if arb.warnings:
            lines.append("")
            lines.append("Warnings: " + "; ".join(arb.warnings))
        return "\n".join(lines)

    async def _send(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    url,
                    json={"chat_id": self.chat_id, "text": text, "disable_web_page_preview": True},
                )
                response.raise_for_status()
        except Exception:
            logger.exception("Failed to send Telegram notification")