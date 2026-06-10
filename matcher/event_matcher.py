"""Fuzzy event matching across platforms."""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta

from rapidfuzz import fuzz

from models.odds import EventMatch, ScrapedEvent, Sport
from normalizer.odds_normalizer import OddsNormalizer

logger = logging.getLogger("arb_scanner.matcher")


class EventMatcher:
    def __init__(
        self,
        threshold: int = 75,
        max_time_diff_minutes: int = 120,
    ) -> None:
        self.threshold = threshold
        self.max_time_diff = timedelta(minutes=max_time_diff_minutes)
        self.normalizer = OddsNormalizer()

    def match_events(self, events: list[ScrapedEvent]) -> list[EventMatch]:
        if not events:
            return []

        groups: list[list[ScrapedEvent]] = []
        used: set[int] = set()

        for i, event_a in enumerate(events):
            if i in used:
                continue
            group = [event_a]
            used.add(i)

            for j, event_b in enumerate(events):
                if j in used or i == j:
                    continue
                score = self._match_score(event_a, event_b)
                if score >= self.threshold:
                    group.append(event_b)
                    used.add(j)

            if len(group) >= 2:
                groups.append(group)

        matches: list[EventMatch] = []
        for group in groups:
            match = self._build_match(group)
            if match:
                matches.append(match)

        logger.info("Matched %d cross-platform event groups from %d events", len(matches), len(events))
        return matches

    def _match_score(self, a: ScrapedEvent, b: ScrapedEvent) -> float:
        if a.sport != b.sport and a.sport != Sport.OTHER and b.sport != Sport.OTHER:
            return 0.0
        if a.market_type != b.market_type:
            return 0.0

        home_a = self.normalizer.clean_team_name(a.home_team)
        away_a = self.normalizer.clean_team_name(a.away_team)
        home_b = self.normalizer.clean_team_name(b.home_team)
        away_b = self.normalizer.clean_team_name(b.away_team)

        if not home_a and not away_a:
            title_score = fuzz.token_sort_ratio(a.display_name, b.display_name)
            return float(title_score)

        direct = (
            fuzz.ratio(home_a, home_b) + fuzz.ratio(away_a, away_b)
        ) / 2
        swapped = (
            fuzz.ratio(home_a, away_b) + fuzz.ratio(away_a, home_b)
        ) / 2
        team_score = max(direct, swapped)

        if a.start_time and b.start_time:
            diff = abs(a.start_time - b.start_time)
            if diff > self.max_time_diff:
                team_score *= 0.5

        league_score = fuzz.partial_ratio(a.league.lower(), b.league.lower())
        return team_score * 0.8 + league_score * 0.2

    def _build_match(self, group: list[ScrapedEvent]) -> EventMatch | None:
        platforms = {e.platform for e in group}
        if len(platforms) < 2:
            return None

        anchor = max(group, key=lambda e: len(e.home_team) + len(e.away_team))
        confidence = sum(
            self._match_score(anchor, e) for e in group if e != anchor
        ) / max(len(group) - 1, 1)

        match_id = hashlib.md5(
            f"{anchor.sport}:{anchor.home_team}:{anchor.away_team}:{anchor.start_time}".encode()
        ).hexdigest()[:12]

        return EventMatch(
            match_id=match_id,
            sport=anchor.sport,
            home_team=anchor.home_team,
            away_team=anchor.away_team,
            league=anchor.league,
            start_time=anchor.start_time,
            events=group,
            confidence=confidence,
        )