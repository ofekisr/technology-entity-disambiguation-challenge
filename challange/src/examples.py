import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path

from src.build import build_tables
from src.catalog import Catalog, Scored
from src.constants import BASE_BY_STRENGTH, CONFIDENCE_DECIMALS, DATA_DIR, MAX_ALTERNATIVES
from src.fuzzy import FuzzyAlias
from src.matchers import CamelCaseSplit, ExactAlias, JoinedWords, Matcher, Query, SynonymRewrite, WithoutNumbers, joined_variants
from src.models import Filters, Hints, load_sources
from src.normalize import normalize
from src.resolver import Resolver, canonical_filters, split_norm
from src.tables import Tables
from src.typos import EXACT_QUALITY, TypoCorrector

Json = dict[str, object]

DOCS_DIR = Path(__file__).parent.parent / "docs"
GUIDE = DOCS_DIR / "solution.guide.html"
GUIDE_DATA = re.compile(r'(<script type="application/json" id="examples-data">).*?(</script>)', re.S)
STEPS_A = ("ExactAlias", "JoinedWords", "CamelCaseSplit", "WithoutNumbers")
STEPS_B = ("ExactAlias", "JoinedWords", "WithoutNumbers", "FuzzyAlias")
STEP_ORDER = (*(f"A · {name}" for name in STEPS_A), *(f"B · {name}" for name in STEPS_B))
@dataclass(frozen=True)
class Group:
    title: str
    shows: str


GROUPS = {
    "exact": Group("Exact name or alias", "The input is already in the alias table; the alias strength sets the score: canonical 1.0, curated 0.97, generated 0.9, weak 0.8."),
    "vendor": Group("Vendor names and prefixes", "A bare vendor name maps to the vendor entity; a prefix such as MS only counts next to a product (D-41)."),
    "look-alike": Group("Look-alikes kept apart", "Names that share letters or words but are different products each resolve to their own id."),
    "cleaning": Group("Cleaning and retries", "Versions are dropped, split words are joined, CamelCase is split at inner capitals, a trailing number is retried without it."),
    "context": Group("Same name, different products", "A bare shared name is ambiguous; a hint, a filter or a context word picks one (D-48)."),
    "semantic": Group("Paraphrases (semantic layer)", "Vendor × concept phrases are compiled into aliases at build time; slang is rewritten at query time (D-49)."),
    "typo": Group("Typos", "Fuzzy matching fixes small misspellings, weighted by how rare each word is; words of 3 letters or fewer are never corrected."),
    "outside": Group("Must not resolve", "Products outside the catalog stay unresolved even when they share words with known ones."),
    "known-limit": Group("Known limits", "Cases the resolver misses today, tracked in docs/GAPS.md."),
}


@dataclass(frozen=True)
class Case:
    input: str
    group: str
    expected_status: str
    expected_id: str | None
    note: str | None = None
    hints: Hints | None = None
    filters: Filters | None = None


CASES = (
    Case("CrowdStrike Falcon", "exact", "resolved", "crowdstrike/falcon", "canonical name"),
    Case("Amazon Elastic Kubernetes Service", "exact", "resolved", "aws/eks", "curated full name"),
    Case("F5 NGINX", "exact", "resolved", "nginx/nginx", "generated vendor × product"),
    Case("EKS", "exact", "resolved", "aws/eks", "weak: a bare acronym"),
    Case("Microsoft", "vendor", "resolved", "microsoft/*", "vendor entity"),
    Case("MS Teams", "vendor", "resolved", "microsoft/teams", "prefix next to a product (G-06)"),
    Case("MS", "vendor", "no_match", None, "a prefix alone never resolves"),
    Case("C", "look-alike", "resolved", "c/c"),
    Case("C#", "look-alike", "resolved", "csharp/csharp", "symbols are kept"),
    Case("C++", "look-alike", "resolved", "cpp/cpp", "symbols are kept"),
    Case("Microsoft Copilot", "look-alike", "resolved", "microsoft/copilot"),
    Case("GitHub Copilot", "look-alike", "resolved", "github/copilot"),
    Case("SentinelOne", "look-alike", "resolved", "sentinelone/sentinelone", "not Microsoft Sentinel"),
    Case("Apache Log4j 2.14", "cleaning", "resolved", "apache/log4j", "dotted version dropped"),
    Case("Log4j 2", "cleaning", "resolved", "apache/log4j", "bare number kept"),
    Case("Share Point", "cleaning", "resolved", "microsoft/sharepoint", "split words joined"),
    Case("Windows 10", "cleaning", "resolved", "microsoft/windows", "retried without the number"),
    Case("RedHat", "cleaning", "resolved", "redhat/*", "split at inner capitals (D-50)"),
    Case("Sentinel", "context", "ambiguous", None, "two products share the name"),
    Case("Sentinel", "context", "resolved", "microsoft/sentinel", "vendor hint", hints=Hints(vendor="Microsoft")),
    Case("Sentinel", "context", "resolved", "hashicorp/sentinel", "vendor filter", filters=Filters(vendors=("hashicorp",))),
    Case("Sentinel SIEM", "context", "resolved", "microsoft/sentinel", "context word in the input"),
    Case("Falcon", "context", "resolved", "crowdstrike/falcon", "category hint", hints=Hints(category="edr")),
    Case("AWS managed Kubernetes", "semantic", "resolved", "aws/eks", "build-time concept alias"),
    Case("Fortinet firewall", "semantic", "resolved", "fortinet/fortigate", "build-time concept alias"),
    Case("Amazon managed k8", "semantic", "resolved", "aws/eks", "k8 rewritten to kubernetes"),
    Case("managed kubernetes", "semantic", "ambiguous", None, "no vendor: a concept alone is never an alias"),
    Case("Crowdstrik Falcon", "typo", "resolved", "crowdstrike/falcon", "vendor misspelled"),
    Case("Crowdstrike Falcn", "typo", "resolved", "crowdstrike/falcon", "rank above 1, confidence stays raw"),
    Case("Kubernets", "typo", "resolved", "kubernetes/kubernetes", "one word, one letter missing"),
    Case("AWS Foo", "outside", "no_match", None, "known vendor, unknown product"),
    Case("Amazon Prime", "outside", "no_match", None, "the vendor word alone is not enough"),
    Case("Microsoft 365", "outside", "no_match", None, "not in the catalog"),
    Case("Splunk Enterprise Security", "outside", "no_match", None, "shares words with Splunk Enterprise"),
    Case("Acme Widget Pro", "outside", "no_match", None, "nothing known"),
    Case("AWS EKS cluster", "known-limit", "resolved", "aws/eks", "G-05: an extra generic word"),
    Case("Crwdstrk Falcon", "known-limit", "resolved", "crowdstrike/falcon", "more than 2 letters wrong"),
)


def _round(value: float) -> float:
    return round(value, CONFIDENCE_DECIMALS)


def _candidates(hits: Scored) -> list[Json]:
    ranked = sorted(hits, key=lambda item: (-item[0], item[2]))[:MAX_ALTERNATIVES]
    return [{"entity": e, "raw": _round(raw), "bonus": _round(score - raw), "rank": _round(score)} for score, raw, e in ranked]


def _step(stage: str, name: str, text: str, outcome: str, detail: Json | None = None) -> Json:
    return {"stage": stage, "step": name, "text": text, "outcome": outcome, "detail": detail or {}}


class Tracer:
    def __init__(self, tables: Tables) -> None:
        self.tables = tables
        self.resolver = Resolver(tables)
        self.catalog = Catalog(tables)
        exact = ExactAlias(tables, self.catalog)
        self.fuzzy = FuzzyAlias(tables, self.catalog, TypoCorrector(tables.idf))
        self.matchers: dict[str, Matcher] = {
            "ExactAlias": exact, "JoinedWords": JoinedWords(exact),
            "CamelCaseSplit": CamelCaseSplit(exact), "WithoutNumbers": WithoutNumbers(exact, self.catalog), "FuzzyAlias": self.fuzzy,
        }
        self.rewriter = SynonymRewrite(exact, tables.synonyms, tables.idf)

    def trace(self, case: Case) -> Json:
        hints = self.resolver.canonical_hints(case.hints or Hints())
        input_norm = normalize(case.input)
        query = Query(input_norm, hints, canonical_filters(case.filters), split_norm(case.input, input_norm))
        steps, hits, winner = self._run_steps(query)
        result = self.resolver.resolve(case.input, hints=case.hints, filters=case.filters)
        rewritten = self.rewriter.rewrite(query.text)
        decision = self._decision(hits)
        answer = {"status": result.status.value, "id": result.id, "canonical_name": result.canonical_name,
                  "confidence": result.confidence,
                  "alternatives": [{"id": a.id, "share": a.confidence} for a in result.alternatives]}
        return {
            "normalized": query.text, "rewritten": rewritten if rewritten != query.text else None,
            "hints": {key: value for key, value in hints.model_dump().items() if value},
            "filters": {"vendors": list(query.filters.vendors)} if case.filters else {},
            "steps": steps, "winner": winner, "decision": decision, "result": answer,
            "final": {"answer": _answer(answer), "why": _why_confidence(answer, decision)},
        }

    def _plan(self, query: Query) -> list[tuple[str, str, Query]]:
        rewritten = replace(query, text=self.rewriter.rewrite(query.text))
        plan = [("A", name, query) for name in STEPS_A] + [("B", "SynonymRewrite", rewritten)]
        return plan + [("B", name, rewritten) for name in STEPS_B]

    def _run_steps(self, query: Query) -> tuple[list[Json], Scored, str | None]:
        steps: list[Json] = []
        hits: Scored = []
        winner: str | None = None
        for stage, name, step_query in self._plan(query):
            if not query.text or winner:
                steps.append(_step(stage, name, step_query.text, "skipped"))
            elif name == "SynonymRewrite":
                steps.append(self._rewrite_step(query.text, step_query.text))
            else:
                found = self.matchers[name].match(step_query)
                steps.append(_step(stage, name, step_query.text, "hit" if found else "miss", self._detail(name, step_query, found)))
                hits, winner = (found, f"{stage} · {name}") if found else (hits, winner)
        return steps, hits, winner

    def _rewrite_step(self, original: str, rewritten: str) -> Json:
        changes = [{"from": a, "to": b} for a, b in zip(original.split(), rewritten.split()) if a != b]
        return _step("B", "SynonymRewrite", rewritten, "rewrote" if changes else "no change", {"changes": changes})

    def _detail(self, name: str, query: Query, hits: Scored) -> Json:
        if name == "FuzzyAlias":
            return self._fuzzy_detail(query, hits)
        looked_up = {"ExactAlias": query.text, "JoinedWords": self._joined_hit(query.text), "CamelCaseSplit": query.split_text or None, "WithoutNumbers": _without_numbers(query.text)}[name]
        detail: Json = {"looked_up": looked_up, "alias_rows": self._alias_rows(looked_up), "candidates": _candidates(hits)}
        if name == "WithoutNumbers":
            detail["note"] = "vendor entities dropped, capped at weak 0.8"
        return detail

    def _joined_hit(self, text: str) -> str | None:
        return next((variant for variant in joined_variants(text.split()) if self.tables.aliases.get(variant)), None)

    def _alias_rows(self, text: str | None) -> list[Json]:
        hits = self.tables.aliases.get(text or "", ())
        return [{"alias": text, "entity": hit.entity_id, "strength": hit.strength.value, "base": BASE_BY_STRENGTH[hit.strength]} for hit in hits]

    def _fuzzy_detail(self, query: Query, hits: Scored) -> Json:
        tokens = query.text.split()
        vendor_id, residue = self.fuzzy.decompose(tokens)
        corrections = self.fuzzy.typos.corrections(tokens)
        weighted = dict(corrections.get(token, (token, EXACT_QUALITY)) for token in tokens)
        required = {corrections.get(token, (token, EXACT_QUALITY))[0] for token in residue} if vendor_id else set()
        best = self._best_aliases(weighted, required, query.filters)
        return {
            "vendor_found": vendor_id, "required_words": sorted(required),
            "typo_fixes": [{"typed": typed, "fixed": fixed, "quality": _round(q)} for typed, (fixed, q) in corrections.items()],
            "word_weights": [{"token": t, "idf": _round(self.fuzzy.idf(t)), "known": t in self.tables.idf} for t in weighted],
            "candidates": [self._fuzzy_row(c, best[str(c["entity"])], weighted) for c in _candidates(hits)],
        }

    def _best_aliases(self, weighted: dict[str, float], required: set[str], filters: Filters) -> dict[str, tuple[float, str]]:
        best: dict[str, tuple[float, str]] = {}
        for alias_norm in sorted({a for token in weighted for a in self.tables.postings.get(token, ())}):
            alias_tokens = set(alias_norm.split())
            if required and not required & alias_tokens:
                continue
            score = self.fuzzy.jaccard(weighted, alias_tokens)
            for hit in self.tables.aliases[alias_norm]:
                if self.catalog.passes(hit.entity_id, filters) and score > best.get(hit.entity_id, (-1.0, ""))[0]:
                    best[hit.entity_id] = (score, alias_norm)
        return best

    def _fuzzy_row(self, candidate: Json, best: tuple[float, str], weighted: dict[str, float]) -> Json:
        alias_tokens = set(best[1].split())
        common = [token for token in sorted(weighted) if token in alias_tokens]
        union = sorted(set(weighted) | alias_tokens)
        return {
            **candidate, "best_alias": best[1],
            "common": [{"token": t, "idf": _round(self.fuzzy.idf(t)), "quality": _round(weighted[t])} for t in common],
            "common_weight": _round(sum(self.fuzzy.idf(t) * weighted[t] for t in common)),
            "union_weight": _round(sum(self.fuzzy.idf(t) for t in union)),
        }

    def _decision(self, hits: Scored) -> Json:
        thresholds = self.tables.thresholds
        ranked = sorted((item for item in hits if item[1] >= thresholds.t_low), key=lambda item: (-item[0], item[2]))
        if not ranked:
            best = max((raw for _, raw, _ in hits), default=None)
            return {"rule": "no step found a candidate" if best is None else f"best raw {_round(best)} is below t_low {thresholds.t_low}"}
        top_score, top_raw, top_id = ranked[0]
        margin = top_score - (ranked[1][0] if len(ranked) > 1 else 0.0)
        return {
            "top": top_id, "top_raw": _round(top_raw), "top_rank": _round(top_score), "margin": _round(margin),
            "second_rank": _round(top_score - margin), "margin_passes": margin >= thresholds.margin,
            "raw_passes": top_raw >= thresholds.t_high, "above_t_low": top_raw >= thresholds.t_low,
        }


def _answer(result: Json) -> str:
    if result["status"] == "resolved":
        return f"resolved → {result['id']} ({result['canonical_name']}), confidence {result['confidence']}"
    if result["status"] == "ambiguous":
        options = ", ".join(f"{a['id']} {a['share']}" for a in result["alternatives"])
        return f"ambiguous → the caller picks one of: {options}; confidence {result['confidence']}"
    return "no_match → confidence 0.0; the input goes to the review queue"


def _why_confidence(result: Json, decision: Json) -> str:
    if result["status"] == "no_match":
        return str(decision["rule"])
    raw, rank = decision["top_raw"], decision["top_rank"]
    ordered = f"; rank {rank} = raw {raw} + bonus only ordered the candidates" if rank != raw else ""
    shares = "; shares = each rank ÷ sum of shown ranks" if result["status"] == "ambiguous" else ""
    return f"confidence = raw {raw} after calibration, capped at 1.0{ordered}{shares}"


def _without_numbers(text: str) -> str | None:
    stripped = " ".join(token for token in text.split() if not token.isdigit())
    return stripped if stripped and stripped != text else None


def _verdict(case: Case, result: Json) -> str:
    if result["status"] == case.expected_status and result["id"] == case.expected_id:
        return "pass"
    if case.group == "outside" and result["status"] != "resolved":
        return "safe"
    return "gap" if case.group == "known-limit" else "fail"


def build_cases(tracer: Tracer) -> list[Json]:
    cases: list[Json] = []
    for index, case in enumerate(CASES):
        trace = tracer.trace(case)
        expected = {"status": case.expected_status, "id": case.expected_id}
        cases.append({"key": f"c{index}", "input": case.input, "group": case.group, "note": case.note,
                      "expected": expected, "verdict": _verdict(case, trace["result"]), **trace})
    return cases


def _label(case: Json) -> str:
    extra = [f"{key}={value}" for key, value in case["hints"].items()]
    extra += [f"filter vendors={','.join(case['filters']['vendors'])}"] if case["filters"] else []
    return f"`{case['input']}`" + (f" ({', '.join(extra)})" if extra else "")


def _result_text(result: Json) -> str:
    if result["status"] == "resolved":
        return f"resolved `{result['id']}` · {result['confidence']}"
    if result["status"] == "ambiguous":
        return "ambiguous · " + ", ".join(f"`{a['id']}` {a['share']}" for a in result["alternatives"][:3])
    return "no_match"


def _why(decision: Json) -> str:
    if "rule" in decision:
        return str(decision["rule"])
    bonus = f" · +bonus → rank {decision['top_rank']}" if decision["top_rank"] != decision["top_raw"] else ""
    return f"raw {decision['top_raw']}{bonus} · margin {decision['margin']}"


def _expected_text(case: Json) -> str:
    expected = case["expected"]
    want = f"{expected['status']} `{expected['id']}`" if expected["id"] else str(expected["status"])
    return {"pass": "✅", "safe": f"✅ not resolved (gold: {want})", "gap": f"gap · want {want}", "fail": f"❌ want {want}"}[str(case["verdict"])]


def _md_header(tables: Tables) -> list[str]:
    th = tables.thresholds
    return [
        "# Resolve examples", "",
        f"Every case below ran through the real resolver on index `{tables.index_version}` ({len(tables.entities)} entities, {len(tables.aliases)} aliases).",
        "Each row shows where the match happened and the numbers behind the answer.",
        f"Rule (D-22, D-48): `resolved` iff raw score ≥ {th.t_high} and margin ≥ {th.margin}; `ambiguous` iff raw score ≥ {th.t_low} (D-51: candidates below are dropped); else `no_match`.",
        f"Hints and the vendor found in the input add a bonus of {th.hint_bonus} that ranks and widens the margin, never the raw score.", "",
        "Steps: **A** = exact on the input as typed (ExactAlias, JoinedWords, CamelCaseSplit, WithoutNumbers); **B** = SynonymRewrite, then ExactAlias, JoinedWords, WithoutNumbers and FuzzyAlias.", "",
        "Regenerate with `make examples`. Interactive version with full traces: guide › Examples tab.", "",
    ]


def _md_row(case: Json) -> str:
    note = f" ({case['note']})" if case["note"] else ""
    return f"| {_label(case)}{note} | {case['winner'] or '—'} | {_result_text(case['result'])} | {_why(case['decision'])} | {_expected_text(case)} |"


def _md_table(key: str, group: list[Json]) -> list[str]:
    rows = [_md_row(case) for case in group]
    return [f"## {GROUPS[key].title}", "", GROUPS[key].shows, "", "| Input | Matched at | Final answer | Why | Expected |", "|---|---|---|---|---|", *rows, ""]


def _md_step(step: Json) -> list[str]:
    lines = [f"- **{step['stage']} · {step['step']}** on `{step['text']}` → {step['outcome']}"]
    detail = step["detail"]
    lines += [f"  - alias `{r['alias']}` → `{r['entity']}` ({r['strength']}, base {r['base']})" for r in detail.get("alias_rows", [])]
    for cand in detail.get("candidates", [])[:3]:
        if "best_alias" in cand:
            common = " + ".join(f"{w['token']} {w['idf']}" for w in cand["common"])
            lines.append(f"  - `{cand['entity']}` via `{cand['best_alias']}`: common {common} = {cand['common_weight']} / union {cand['union_weight']} = raw {cand['raw']}")
    return lines


def _check(passed: object) -> str:
    return "yes" if passed else "no"


def _md_decide(case: Json, tables: Tables) -> str:
    d, th = case["decision"], tables.thresholds
    raw = f"raw {d['top_raw']} (≥ {th.t_high}: {_check(d['raw_passes'])})"
    margin = f"margin {d['margin']} (≥ {th.margin}: {_check(d['margin_passes'])})"
    return f"- **Decide:** top `{d['top']}` {raw}, {margin} → {_result_text(case['result'])}\n- **Final answer:** {case['final']['answer']}. {case['final']['why'].capitalize()}."


def _md_trace(case: Json, tables: Tables) -> list[str]:
    rewritten = f" · rewritten: `{case['rewritten']}`" if case["rewritten"] else ""
    lines = [f"### {GROUPS[str(case['group'])].title}: {_label(case)}", "", f"Normalized: `{case['normalized']}`{rewritten}", ""]
    for step in case["steps"]:
        lines += _md_step(step) if step["outcome"] != "skipped" else []
    lines += [_md_decide(case, tables)] if "rule" not in case["decision"] else []
    return [*lines, ""]


def write_markdown(cases: list[Json], tables: Tables, path: Path) -> None:
    lines = _md_header(tables)
    groups = {key: [c for c in cases if c["group"] == key] for key in GROUPS}
    for key, group in groups.items():
        lines += _md_table(key, group) if group else []
    lines += ["## Appendix — optional (+5 minutes)", "", "One full trace per group: the data each step read.", ""]
    for group in filter(None, groups.values()):
        lines += _md_trace(max(group, key=lambda c: STEP_ORDER.index(c["winner"]) if c["winner"] else -1), tables)
    path.write_text("\n".join(lines))


def write_json(cases: list[Json], tables: Tables, path: Path) -> str:
    groups = {key: {"title": group.title, "shows": group.shows} for key, group in GROUPS.items()}
    payload = {"index_version": tables.index_version, "aliases": len(tables.aliases),
               "thresholds": tables.thresholds.model_dump(), "groups": groups, "cases": cases}
    text = json.dumps(payload, ensure_ascii=False)
    path.write_text(text)
    return text


def embed_in_guide(guide: Path, json_text: str) -> bool:
    if not guide.exists():
        return False
    safe = json_text.replace("</", "<\\/")
    updated, count = GUIDE_DATA.subn(lambda match: match.group(1) + safe + match.group(2), guide.read_text())
    if count:
        guide.write_text(updated)
    return count > 0


def main() -> None:
    tables = build_tables(load_sources(DATA_DIR))
    cases = build_cases(Tracer(tables))
    write_markdown(cases, tables, DOCS_DIR / "examples.md")
    embedded = embed_in_guide(GUIDE, write_json(cases, tables, DOCS_DIR / "examples.json"))
    print(json.dumps({"cases": len(cases), "verdicts": Counter(str(c["verdict"]) for c in cases), "guide_updated": embedded}))


if __name__ == "__main__":
    main()
