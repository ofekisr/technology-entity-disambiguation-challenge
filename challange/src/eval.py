import json
import time
from dataclasses import dataclass, replace
from pathlib import Path

from src.build import Tables
from src.constants import CALIBRATION_BINS, DATA_DIR, EXACT_ONLY_MAX_LEN, VENDOR_CATEGORY, Status, Strength
from src.models import Sources
from src.normalize import normalize
from src.resolver import Resolver

MIN_TYPO_TOKEN_LEN = 6
MS_PER_SECOND = 1000
P50, P99 = 0.50, 0.99
REQUESTS_PER_MILLION = 1_000_000
VCPU_USD_PER_SECOND = 0.04 / 3600
SWEEP_T_HIGH = (0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)
ROUND_TO = 4

# Offline-evaluation stub (D-38, D-40): in production the gold set is 300-500 hand-labeled cases
# split dev / test; the calibration bins are fitted on dev, the regression gate runs in CI on every
# source-file PR, and the report is diffed against the last published index_version.


@dataclass(frozen=True)
class GoldCase:
    input: str
    expected_id: str | None
    expected_status: Status
    kind: str
    held_out: str | None = None


def load_hand_cases(path: Path) -> list[GoldCase]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [GoldCase(row["input"], row["expected_id"], Status(row["expected_status"]), row["kind"]) for row in rows]


def leave_one_out_cases(sources: Sources) -> list[GoldCase]:
    manual = [row for row in sources.aliases if row.strength is Strength.STRONG]
    return [
        GoldCase(row.alias, row.entity_id, Status.RESOLVED, "leave-one-out", held_out=normalize(row.alias))
        for row in manual
        if len(normalize(row.alias)) > EXACT_ONLY_MAX_LEN
    ]


def typo_cases(tables: Tables) -> list[GoldCase]:
    cases = []
    for record in tables.entities.values():
        if record.category == VENDOR_CATEGORY:
            continue
        words = record.canonical_name.split()
        longest = max(words, key=len)
        if len(longest) >= MIN_TYPO_TOKEN_LEN:
            middle = len(longest) // 2
            typo = record.canonical_name.replace(longest, longest[:middle] + longest[middle + 1 :], 1)
            cases.append(GoldCase(typo, record.id, Status.RESOLVED, "typo"))
    return cases


def build_gold_set(sources: Sources, tables: Tables, data_dir: Path = DATA_DIR) -> list[GoldCase]:
    return [*load_hand_cases(data_dir / "gold.jsonl"), *leave_one_out_cases(sources), *typo_cases(tables)]


def without_alias(tables: Tables, alias_norm: str) -> Tables:
    aliases = {key: hits for key, hits in tables.aliases.items() if key != alias_norm}
    postings = {token: tuple(a for a in found if a != alias_norm) for token, found in tables.postings.items()}
    return replace(tables, aliases=aliases, postings=postings)


@dataclass(frozen=True)
class Outcome:
    case: GoldCase
    status: Status
    predicted_id: str | None
    confidence: float
    latency_s: float


def run_case(tables: Tables, case: GoldCase) -> Outcome:
    resolver = Resolver(without_alias(tables, case.held_out) if case.held_out else tables)
    started = time.perf_counter()
    result = resolver.resolve(case.input)
    elapsed = time.perf_counter() - started
    return Outcome(case, result.status, result.id, result.confidence, elapsed)


def is_correct(outcome: Outcome) -> bool:
    expected = outcome.case
    return outcome.status is expected.expected_status and outcome.predicted_id == expected.expected_id


def quality(outcomes: list[Outcome]) -> dict[str, float]:
    resolved = [o for o in outcomes if o.status is Status.RESOLVED]
    expected = [o for o in outcomes if o.case.expected_status is Status.RESOLVED]
    correct = [o for o in resolved if is_correct(o)]
    precision = len(correct) / len(resolved) if resolved else 0.0
    coverage = len(correct) / len(expected) if expected else 0.0
    f1 = 2 * precision * coverage / (precision + coverage) if precision + coverage else 0.0
    ambiguous = sum(o.status is Status.AMBIGUOUS for o in outcomes) / len(outcomes)
    values = {"precision_on_resolved": precision, "coverage": coverage, "f1": f1, "ambiguous_rate": ambiguous}
    return {key: round(value, ROUND_TO) for key, value in values.items()}


def latency(outcomes: list[Outcome]) -> dict[str, float]:
    ordered = sorted(o.latency_s for o in outcomes)
    p50, p99 = ordered[int(P50 * (len(ordered) - 1))], ordered[int(P99 * (len(ordered) - 1))]
    cost = p50 * REQUESTS_PER_MILLION * VCPU_USD_PER_SECOND
    return {"p50_ms": round(p50 * MS_PER_SECOND, ROUND_TO), "p99_ms": round(p99 * MS_PER_SECOND, ROUND_TO),
            "cost_per_1m_usd": round(cost, ROUND_TO)}


def reliability_table(outcomes: list[Outcome]) -> tuple[list[dict[str, float]], float]:
    resolved = [o for o in outcomes if o.status is Status.RESOLVED]
    rows, ece = [], 0.0
    for index in range(CALIBRATION_BINS):
        low, high = index / CALIBRATION_BINS, (index + 1) / CALIBRATION_BINS
        members = [o for o in resolved if low <= o.confidence < high or (high == 1 and o.confidence == 1)]
        if members:
            accuracy = sum(map(is_correct, members)) / len(members)
            mean_conf = sum(o.confidence for o in members) / len(members)
            ece += len(members) / len(resolved) * abs(accuracy - mean_conf)
            rows.append({"bin": low, "n": len(members), "accuracy": round(accuracy, ROUND_TO), "confidence": round(mean_conf, ROUND_TO)})
    return rows, round(ece, ROUND_TO)


def sweep_thresholds(tables: Tables, cases: list[GoldCase]) -> list[dict[str, float]]:
    rows = []
    for t_high in SWEEP_T_HIGH:
        swept = replace(tables, thresholds=tables.thresholds.model_copy(update={"t_high": t_high}))
        rows.append({"t_high": t_high, **quality([run_case(swept, case) for case in cases])})
    return rows


def evaluate(sources: Sources, tables: Tables) -> dict[str, object]:
    cases = build_gold_set(sources, tables)
    outcomes = [run_case(tables, case) for case in cases]
    bins, ece = reliability_table(outcomes)
    metrics = quality(outcomes)
    return {
        "index_version": tables.index_version,
        "cases": len(cases),
        **metrics,
        **latency(outcomes),
        "gate_passed": metrics["precision_on_resolved"] >= tables.thresholds.precision_target,
        "sweep": sweep_thresholds(tables, cases),
        "reliability": bins,
        "ece": ece,
        "misses": [o.case.input for o in outcomes if not is_correct(o)],
    }
