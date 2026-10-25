from src.build import EntityRecord, Tables
from src.catalog import Scored
from src.constants import CONFIDENCE_DECIMALS, FULL_CONFIDENCE, MAX_ALTERNATIVES, Status
from src.models import Alternative, Resolution


class Decider:
    def __init__(self, tables: Tables) -> None:
        self.tables = tables

    def decide(self, scored: Scored) -> Resolution:
        ranked = sorted(scored, key=lambda item: (-item[0], item[2]))
        thresholds = self.tables.thresholds
        if not ranked or ranked[0][0] < thresholds.t_low:
            return Resolution.no_match(self.tables.index_version)
        top_score, top_raw, top_id = ranked[0]
        margin = top_score - (ranked[1][0] if len(ranked) > 1 else 0.0)
        if top_raw >= thresholds.t_high and margin >= thresholds.margin:
            return self._resolved(self.tables.entities[top_id], top_raw)
        return self._ambiguous([item for item in ranked if item[0] >= thresholds.t_low])

    def _resolved(self, record: EntityRecord, score: float) -> Resolution:
        return Resolution(
            id=record.id,
            canonical_name=record.canonical_name,
            vendor=record.vendor_name,
            category=record.category,
            confidence=self._calibrate(score),
            status=Status.RESOLVED,
            index_version=self.tables.index_version,
        )

    def _ambiguous(self, ranked: Scored) -> Resolution:
        shown = ranked[:MAX_ALTERNATIVES]
        total = sum(score for score, _, _ in shown)
        alternatives = tuple(
            Alternative(id=entity_id, canonical_name=self.tables.entities[entity_id].canonical_name, confidence=round(score / total, CONFIDENCE_DECIMALS))
            for score, _, entity_id in shown
        )
        empty = Resolution.no_match(self.tables.index_version)
        top = self._calibrate(shown[0][0])
        return empty.model_copy(update={"status": Status.AMBIGUOUS, "confidence": top, "alternatives": alternatives})

    def _calibrate(self, score: float) -> float:
        capped = min(score, FULL_CONFIDENCE)
        scale = next((s for low, high, s in self.tables.calibration if low <= capped < high), FULL_CONFIDENCE)
        return round(min(capped * scale, FULL_CONFIDENCE), CONFIDENCE_DECIMALS)
