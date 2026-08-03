"""Deduplication Engine module for Stage 9 Alert Intelligence Engine."""

from datetime import datetime
from difflib import SequenceMatcher
from typing import List

from src.logger import get_logger
from src.schema import NormalizedAlert

logger = get_logger(__name__)

DUPLICATE_THRESHOLD = 0.75

HAZARD_WEIGHT = 0.35
LOCATION_WEIGHT = 0.30
TIME_WEIGHT = 0.20
ACTION_WEIGHT = 0.15


class DeduplicationEngine:
    """Batch Deduplication Engine identifying duplicate disaster alerts using weighted similarity scoring."""

    def deduplicate(self, alerts: List[NormalizedAlert]) -> List[NormalizedAlert]:
        """Identify duplicate alerts across a normalized batch and mark them with is_duplicate=True.

        The first occurrence of an alert becomes the canonical representative.
        Subsequent alerts are compared only against previously accepted canonical alerts.
        Duplicate alerts are never promoted to canonical status.

        Guarantees input immutability: incoming list and NormalizedAlert objects are never mutated.
        Preserves input list length, order, and object field contents (except setting is_duplicate).

        Args:
            alerts: List of schema-validated NormalizedAlert objects.

        Returns:
            List[NormalizedAlert]: New list of NormalizedAlert objects with duplicate flags updated.
        """
        # The first occurrence of an alert becomes the canonical representative.
        # Subsequent alerts are compared only against previously accepted canonical alerts.
        # Duplicate alerts are never promoted to canonical status.
        if not alerts:
            return []

        canonical_alerts: List[NormalizedAlert] = []
        result: List[NormalizedAlert] = []

        for alert in alerts:
            is_dup = False
            for canonical in canonical_alerts:
                score = self._overall_score(alert, canonical)
                if score >= DUPLICATE_THRESHOLD:
                    is_dup = True
                    logger.info(
                        f"Duplicate alert detected: '{alert.alert_id}' matches canonical '{canonical.alert_id}' "
                        f"with score {score:.4f} >= {DUPLICATE_THRESHOLD}"
                    )
                    break

            if is_dup:
                dup_alert = alert.model_copy(update={"is_duplicate": True})
                result.append(dup_alert)
            else:
                canon_alert = alert.model_copy(update={"is_duplicate": False}) if alert.is_duplicate else alert
                result.append(canon_alert)
                canonical_alerts.append(canon_alert)

        return result

    def _hazard_score(self, alert1: NormalizedAlert, alert2: NormalizedAlert) -> float:
        """Calculate hazard match score (35% weight).

        Returns 1.0 for exact enum match, 0.0 otherwise.
        """
        if alert1.hazard_type == alert2.hazard_type:
            return 1.0
        return 0.0

    def _location_score(self, alert1: NormalizedAlert, alert2: NormalizedAlert) -> float:
        """Calculate location match score (30% weight).

        Priority 1:
        If BOTH alerts have non-null location_id, compare ONLY location_id.
        If equal: score = 1.0, Else: score = 0.0.

        Priority 2:
        Only when one or both location_id values are missing (None),
        compare normalized location_name values using difflib.SequenceMatcher.
        """
        # Priority 1: Both location_id values are non-null
        if alert1.location_id is not None and alert2.location_id is not None:
            id1 = str(alert1.location_id).strip()
            id2 = str(alert2.location_id).strip()
            return 1.0 if id1 == id2 else 0.0

        # Priority 2: One or both location_id values are missing
        loc1 = alert1.location_name.strip().lower() if alert1.location_name else ""
        loc2 = alert2.location_name.strip().lower() if alert2.location_name else ""

        if not loc1 or not loc2:
            return 0.0

        if loc1 == loc2:
            return 1.0

        return float(SequenceMatcher(None, loc1, loc2).ratio())

    def _time_overlap_score(self, alert1: NormalizedAlert, alert2: NormalizedAlert) -> float:
        """Calculate time window overlap score (20% weight).

        Deterministically handles missing start_time, missing end_time, invalid datetimes,
        zero-duration events, and non-overlapping intervals.
        If any required datetime cannot be interpreted, returns 0.0 without raising exceptions.
        """
        if not alert1.start_time or not alert2.start_time:
            return 0.0

        try:
            dt1_start = datetime.fromisoformat(alert1.start_time)
            dt2_start = datetime.fromisoformat(alert2.start_time)
        except (ValueError, TypeError):
            return 0.0

        # Case A: Both alerts have end_time
        if alert1.end_time and alert2.end_time:
            try:
                dt1_end = datetime.fromisoformat(alert1.end_time)
                dt2_end = datetime.fromisoformat(alert2.end_time)
            except (ValueError, TypeError):
                return 0.0

            if dt1_start > dt1_end or dt2_start > dt2_end:
                return 0.0

            dur1 = (dt1_end - dt1_start).total_seconds()
            dur2 = (dt2_end - dt2_start).total_seconds()

            if dur1 == 0 and dur2 == 0:
                return 1.0 if dt1_start == dt2_start else 0.0
            if dur1 == 0:
                return 1.0 if dt2_start <= dt1_start <= dt2_end else 0.0
            if dur2 == 0:
                return 1.0 if dt1_start <= dt2_start <= dt1_end else 0.0

            latest_start = max(dt1_start, dt2_start)
            earliest_end = min(dt1_end, dt2_end)

            if latest_start <= earliest_end:
                overlap_sec = (earliest_end - latest_start).total_seconds()
                min_dur_sec = min(dur1, dur2)
                if min_dur_sec > 0:
                    return min(1.0, max(0.0, overlap_sec / min_dur_sec))
                return 1.0
            return 0.0

        # Case B: Missing end_time on both alerts (compare start_time proximity)
        if not alert1.end_time and not alert2.end_time:
            diff_sec = abs((dt1_start - dt2_start).total_seconds())
            if diff_sec == 0:
                return 1.0
            if diff_sec <= 86400:
                return max(0.0, 1.0 - (diff_sec / 86400.0))
            return 0.0

        # Case C: One alert has end_time and the other does not
        return 0.0

    def _text_similarity_score(self, alert1: NormalizedAlert, alert2: NormalizedAlert) -> float:
        """Calculate recommended action text similarity score (15% weight)."""
        act1 = alert1.recommended_action.strip().lower() if alert1.recommended_action else ""
        act2 = alert2.recommended_action.strip().lower() if alert2.recommended_action else ""

        if not act1 and not act2:
            return 1.0
        if not act1 or not act2:
            return 0.0
        if act1 == act2:
            return 1.0

        return float(SequenceMatcher(None, act1, act2).ratio())

    def _overall_score(self, alert1: NormalizedAlert, alert2: NormalizedAlert) -> float:
        """Calculate total weighted duplicate score across all four components.

        Weights:
        - Hazard match: 35%
        - Location match: 30%
        - Time window overlap: 20%
        - Text similarity: 15%
        """
        score = (
            HAZARD_WEIGHT * self._hazard_score(alert1, alert2)
            + LOCATION_WEIGHT * self._location_score(alert1, alert2)
            + TIME_WEIGHT * self._time_overlap_score(alert1, alert2)
            + ACTION_WEIGHT * self._text_similarity_score(alert1, alert2)
        )
        return round(score, 4)
