"""Console table output for arbitrage opportunities."""

from __future__ import annotations

import logging

from models.odds import ArbitrageOpportunity

logger = logging.getLogger("arb_scanner.notifier.console")

try:
    from rich.console import Console
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ConsoleNotifier:
    def __init__(self) -> None:
        self.console = Console() if RICH_AVAILABLE else None

    def notify(self, opportunities: list[ArbitrageOpportunity]) -> None:
        if not opportunities:
            logger.info("No arbitrage opportunities above threshold.")
            if self.console:
                self.console.print("[yellow]No arbitrage opportunities found.[/yellow]")
            return

        if RICH_AVAILABLE and self.console:
            self._rich_table(opportunities)
        else:
            self._plain_table(opportunities)

    def _rich_table(self, opportunities: list[ArbitrageOpportunity]) -> None:
        table = Table(title="Arbitrage Opportunities", show_lines=True)
        table.add_column("Event", style="cyan", max_width=30)
        table.add_column("Sport")
        table.add_column("Profit %", style="green")
        table.add_column("Stake", justify="right")
        table.add_column("Profit $", justify="right", style="green")
        table.add_column("Platforms")
        table.add_column("Warnings", style="yellow", max_width=25)

        for arb in opportunities:
            platforms = ", ".join({leg.platform.value for leg in arb.legs})
            warnings = "; ".join(arb.warnings) if arb.warnings else "-"
            table.add_row(
                arb.event_name[:30],
                arb.sport.value,
                f"{arb.profit_pct:.2f}%",
                f"${arb.total_stake:.2f}",
                f"${arb.guaranteed_profit:.2f}",
                platforms,
                warnings,
            )

            for leg in arb.legs:
                table.add_row(
                    f"  -> {leg.outcome_name}",
                    leg.platform.value,
                    f"@{leg.decimal_odds:.2f}",
                    f"${leg.stake:.2f}",
                    f"-> ${leg.potential_return:.2f}",
                    leg.url or "-",
                    "",
                )

        self.console.print(table)

    def _plain_table(self, opportunities: list[ArbitrageOpportunity]) -> None:
        print("\n" + "=" * 80)
        print("ARBITRAGE OPPORTUNITIES")
        print("=" * 80)
        for arb in opportunities:
            print(f"\n{arb.event_name} | {arb.sport.value} | +{arb.profit_pct:.2f}%")
            print(f"  Stake: ${arb.total_stake:.2f} -> Profit: ${arb.guaranteed_profit:.2f}")
            for leg in arb.legs:
                print(
                    f"    {leg.platform.value}: {leg.outcome_name} "
                    f"@ {leg.decimal_odds:.2f} stake ${leg.stake:.2f}"
                )
            if arb.warnings:
                print(f"  Warnings: {', '.join(arb.warnings)}")
        print("=" * 80 + "\n")