import json
import random
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from statistics import mean

from src.alias_sources import DEFAULT_ALIAS_SOURCES, AliasSource, Records
from src.build import build_tables
from src.tables import AliasTriple, Tables
from src.constants import (
    CALIBRATION_BINS,
    CONFIDENCE_DECIMALS,
    DATA_DIR,
    EXACT_ONLY_MAX_LEN,
    FULL_CONFIDENCE,
    VENDOR_CATEGORY,
    Status,
    Strength,
)
from src.models import Sources
from src.normalize import normalize
from src.resolver import Resolver

MIN_TYPO_TOKEN_LEN = 6
MS_PER_SECOND = 1000
P50, P99 = 0.50, 0.99
REQUESTS_PER_MILLION = 1_000_000
VCPU_USD_PER_SECOND = 0.04 / 3600
SWEEP_T_HIGH = (0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95)
CURVE_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)
CURVE_SEEDS = 5

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


def run_cases(tables: Tables, cases: list[GoldCase]) -> list[Outcome]:
    shared = Resolver(tables)
    return [run_case(Resolver(without_alias(tables, c.held_out)) if c.held_out else shared, c) for c in cases]


def run_case(resolver: Resolver, case: GoldCase) -> Outcome:
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
    return {key: round(value, CONFIDENCE_DECIMALS) for key, value in values.items()}


def latency(outcomes: list[Outcome]) -> dict[str, float]:
    ordered = sorted(o.latency_s for o in outcomes)
    p50, p99 = ordered[int(P50 * (len(ordered) - 1))], ordered[int(P99 * (len(ordered) - 1))]
    cost = p50 * REQUESTS_PER_MILLION * VCPU_USD_PER_SECOND
    return {"p50_ms": round(p50 * MS_PER_SECOND, CONFIDENCE_DECIMALS), "p99_ms": round(p99 * MS_PER_SECOND, CONFIDENCE_DECIMALS),
            "cost_per_1m_usd": round(cost, CONFIDENCE_DECIMALS)}


def reliability_table(outcomes: list[Outcome]) -> tuple[list[dict[str, float]], float]:
    resolved = [o for o in outcomes if o.status is Status.RESOLVED]
    rows, ece = [], 0.0
    for index in range(CALIBRATION_BINS):
        low, high = index / CALIBRATION_BINS, (index + 1) / CALIBRATION_BINS
        members = [o for o in resolved if low <= o.confidence < high or (high == FULL_CONFIDENCE and o.confidence == FULL_CONFIDENCE)]
        if members:
            accuracy = sum(map(is_correct, members)) / len(members)
            mean_conf = sum(o.confidence for o in members) / len(members)
            ece += len(members) / len(resolved) * abs(accuracy - mean_conf)
            rows.append({"bin": low, "n": len(members), "accuracy": round(accuracy, CONFIDENCE_DECIMALS), "confidence": round(mean_conf, CONFIDENCE_DECIMALS)})
    return rows, round(ece, CONFIDENCE_DECIMALS)


def sweep_thresholds(tables: Tables, cases: list[GoldCase]) -> list[dict[str, float]]:
    rows = []
    for t_high in SWEEP_T_HIGH:
        swept = replace(tables, thresholds=tables.thresholds.model_copy(update={"t_high": t_high}))
        rows.append({"t_high": t_high, **quality(run_cases(swept, cases))})
    return rows


def evaluate(sources: Sources, tables: Tables) -> dict[str, object]:
    cases = build_gold_set(sources, tables)
    outcomes = run_cases(tables, cases)
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


class SampledAliases:
    def __init__(self, fraction: float, seed: int, inner: Sequence[AliasSource] = DEFAULT_ALIAS_SOURCES) -> None:
        self.fraction, self.seed, self.inner = fraction, seed, inner

    def aliases(self, sources: Sources, records: Records) -> Iterator[AliasTriple]:
        rng = random.Random(self.seed)
        for source in self.inner:
            for alias, entity_id, strength in source.aliases(sources, records):
                if strength is Strength.CANONICAL or rng.random() < self.fraction:
                    yield alias, entity_id, strength


def alias_budget(sources: Sources, tables: Tables) -> dict[str, object]:
    return {"ablation": source_ablation(sources, tables), "curve": alias_curve(sources, tables)}


def source_ablation(sources: Sources, tables: Tables) -> list[dict[str, object]]:
    cases = build_gold_set(sources, tables)
    base = quality(run_cases(tables, cases))["coverage"]
    rows: list[dict[str, object]] = []
    for source in DEFAULT_ALIAS_SOURCES:
        ablated = build_tables(sources, alias_sources=tuple(s for s in DEFAULT_ALIAS_SOURCES if s is not source))
        metrics = quality(run_cases(ablated, cases))
        rows.append({"source": type(source).__name__, "alias_keys_lost": len(tables.aliases) - len(ablated.aliases),
                     "coverage_lost": round(base - metrics["coverage"], CONFIDENCE_DECIMALS),
                     "precision_on_resolved": metrics["precision_on_resolved"]})
    return rows


def alias_curve(sources: Sources, tables: Tables) -> list[dict[str, float]]:
    cases = [*load_hand_cases(DATA_DIR / "gold.jsonl"), *typo_cases(tables)]
    return [_curve_point(sources, cases, fraction) for fraction in CURVE_FRACTIONS]


def _curve_point(sources: Sources, cases: list[GoldCase], fraction: float) -> dict[str, float]:
    runs = [build_tables(sources, alias_sources=(SampledAliases(fraction, seed),)) for seed in range(CURVE_SEEDS)]
    metrics = [quality(run_cases(sampled, cases)) for sampled in runs]
    per_entity = mean(sum(map(len, sampled.aliases.values())) / len(sampled.entities) for sampled in runs)
    return {"fraction": fraction, "aliases_per_entity": round(per_entity, CONFIDENCE_DECIMALS),
            "coverage": round(mean(m["coverage"] for m in metrics), CONFIDENCE_DECIMALS),
            "precision_on_resolved": round(mean(m["precision_on_resolved"] for m in metrics), CONFIDENCE_DECIMALS)}
