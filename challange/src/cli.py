import argparse
import csv
import json
import resource
import sys
from datetime import UTC, datetime
from pathlib import Path

from src.build import build_tables, load_snapshot, validate, write_snapshot
from src.constants import DATA_DIR
from src.eval import evaluate
from src.models import AliasRow, Filters, Hints, load_sources
from src.normalize import normalize
from src.resolver import Resolver, snapshot_path

OK, FAILED = 0, 1
BYTES_PER_MB = 1024 * 1024
KB_PER_MB = 1024
ALIAS_FIELDS = ("alias", "entity_id", "strength", "source", "actor", "added_at", "reason", "evidence_url")


def rss_mb() -> float:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(peak / (BYTES_PER_MB if sys.platform == "darwin" else KB_PER_MB), 1)


def cmd_build(args: argparse.Namespace) -> int:
    sources = load_sources(args.data_dir)
    tables = build_tables(sources)
    errors = validate(sources, tables)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return FAILED
    write_snapshot(tables, args.out)
    report = {"index_version": tables.index_version, "entities": len(tables.entities),
              "aliases": len(tables.aliases), "rss_mb": rss_mb(), "path": str(args.out)}
    print(json.dumps(report))
    return OK


def cmd_validate(args: argparse.Namespace) -> int:
    sources = load_sources(args.data_dir)
    errors = validate(sources, build_tables(sources))
    print("\n".join(errors) if errors else f"ok: {len(sources.entities)} entities")
    return FAILED if errors else OK


def cmd_eval(args: argparse.Namespace) -> int:
    sources = load_sources(args.data_dir)
    report = evaluate(sources, build_tables(sources))
    print(json.dumps(report, indent=2))
    return OK if report["gate_passed"] else FAILED


def load_resolver(path: Path, data_dir: Path) -> Resolver:
    if not path.exists():
        write_snapshot(build_tables(load_sources(data_dir)), path)
    return Resolver(load_snapshot(path))


def cmd_resolve(args: argparse.Namespace) -> int:
    resolver = load_resolver(args.snapshot, args.data_dir)
    hints = Hints(vendor=args.hint_vendor, category=args.hint_category)
    filters = Filters(vendors=tuple(args.filter_vendor), categories=tuple(args.filter_category))
    print(resolver.resolve(args.name, hints=hints, filters=filters).model_dump_json(indent=2))
    return OK


def cmd_add_alias(args: argparse.Namespace) -> int:
    sources = load_sources(args.data_dir)
    if args.entity_id not in {entity.id for entity in sources.entities}:
        print(f"unknown entity {args.entity_id}", file=sys.stderr)
        return FAILED
    key = (normalize(args.alias), args.entity_id)
    if key in {(normalize(row.alias), row.entity_id) for row in sources.aliases}:
        print("unchanged")
        return OK
    _append_alias(args)
    print("added")
    return OK


def _append_alias(args: argparse.Namespace) -> None:
    row = AliasRow(alias=args.alias, entity_id=args.entity_id, strength=args.strength, source="cli",
                   actor=args.actor, added_at=datetime.now(UTC), reason=args.reason, evidence_url=args.evidence_url)
    values = row.model_dump(mode="json")
    with (args.data_dir / "aliases.csv").open("a", newline="") as handle:
        csv.writer(handle).writerow([values[name] or "" for name in ALIAS_FIELDS])


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="idx", description="Technology entity resolver")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="build the snapshot (Flow A)")
    build.add_argument("--out", type=Path, default=snapshot_path())
    validate_cmd = sub.add_parser("validate", help="check source-file invariants")
    resolve_cmd = sub.add_parser("resolve", help="resolve one name (Flow B)")
    _resolve_args(resolve_cmd)
    eval_cmd = sub.add_parser("eval", help="gold-set metrics, sweep and reliability (D-38)")
    add = sub.add_parser("add-alias", help="idempotent alias upsert with provenance (D-36)")
    _add_alias_args(add)
    for command, handler in ((build, cmd_build), (validate_cmd, cmd_validate), (resolve_cmd, cmd_resolve), (eval_cmd, cmd_eval),
                             (add, cmd_add_alias)):
        _common(command)
        command.set_defaults(handler=handler)
    return parser


def _resolve_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("name")
    parser.add_argument("--snapshot", type=Path, default=snapshot_path())
    parser.add_argument("--hint-vendor")
    parser.add_argument("--hint-category")
    parser.add_argument("--filter-vendor", action="append", default=[])
    parser.add_argument("--filter-category", action="append", default=[])


def _add_alias_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("entity_id")
    parser.add_argument("alias")
    parser.add_argument("--strength", default="strong", choices=["strong", "weak"])
    parser.add_argument("--actor", default="cli")
    parser.add_argument("--reason", default="")
    parser.add_argument("--evidence-url", default="")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    sys.exit(main())
