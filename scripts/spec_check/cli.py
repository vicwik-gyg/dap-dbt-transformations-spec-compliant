"""CLI entrypoint for shadow-spec-check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .formatters import format_human, format_json, format_markdown, format_matrix
from .manifest import get_layer, get_model_nodes, is_rule_suppressed, load_manifest
from .models import Result, RuleResult
from .registry import get_all_rules, get_rule_info

# Import rules to register them
from . import rules as _rules  # noqa: F401


def run_checks(
    manifest: dict,
    model_filter: str | None = None,
    rule_filter: str | None = None,
    layer_filter: str | None = None,
) -> list[RuleResult]:
    """Run all applicable rules against all matching models."""
    nodes = get_model_nodes(manifest)
    all_rules = get_all_rules()
    rule_infos = get_rule_info()
    results: list[RuleResult] = []

    # Apply filters
    if model_filter:
        nodes = [n for n in nodes if n["name"] == model_filter]
        if not nodes:
            print(f"Error: model '{model_filter}' not found in manifest", file=sys.stderr)
            sys.exit(2)

    if layer_filter:
        nodes = [n for n in nodes if get_layer(n) == layer_filter]

    rules_to_run = list(all_rules.keys())
    if rule_filter:
        rules_to_run = [r for r in rules_to_run if r == rule_filter or r.startswith(rule_filter + ".")]
        if not rules_to_run:
            print(f"Error: rule '{rule_filter}' not found", file=sys.stderr)
            sys.exit(2)

    for node in nodes:
        node_layer = get_layer(node)
        for rule_name in rules_to_run:
            info = rule_infos[rule_name]
            # Check applicability
            if info.applies_to and "all" not in info.applies_to:
                if node_layer not in info.applies_to:
                    results.append(
                        RuleResult(
                            model=node["name"],
                            rule=rule_name,
                            result=Result.NA,
                        )
                    )
                    continue

            # Check model-level suppression
            suppressed, justification = is_rule_suppressed(node, rule_name)
            if suppressed:
                reason = justification or "no justification provided"
                results.append(
                    RuleResult(
                        model=node["name"],
                        rule=rule_name,
                        result=Result.SUPPRESSED,
                        finding=f"Suppressed: {reason}",
                    )
                )
                continue

            fn = all_rules[rule_name]
            try:
                result = fn(node, manifest)
                if result is not None:
                    results.append(result)
            except Exception as e:
                results.append(
                    RuleResult(
                        model=node["name"],
                        rule=rule_name,
                        result=Result.DEVIATES,
                        finding=f"Rule error: {e}",
                    )
                )

    return results


def cmd_model(args: argparse.Namespace) -> int:
    """Check a single model."""
    manifest = load_manifest(args.manifest)
    results = run_checks(
        manifest, model_filter=args.model_name, rule_filter=args.rule
    )
    print(_format_results(results, args.format))
    return _exit_code(results)


def cmd_all(args: argparse.Namespace) -> int:
    """Check all models."""
    manifest = load_manifest(args.manifest)
    results = run_checks(
        manifest, rule_filter=args.rule, layer_filter=args.layer
    )
    print(_format_results(results, args.format))
    return _exit_code(results)


def cmd_rules(args: argparse.Namespace) -> int:
    """List all available rules."""
    infos = get_rule_info()
    print(f"{'RULE':<40} {'APPLIES TO':<24} DESCRIPTION")
    print("-" * 100)
    for name in sorted(infos.keys()):
        info = infos[name]
        applies = ", ".join(info.applies_to) if info.applies_to else "all"
        print(f"{name:<40} {applies:<24} {info.description}")
    return 0


def _format_results(results: list[RuleResult], fmt: str) -> str:
    """Route to the correct formatter."""
    if fmt == "json":
        return format_json(results)
    elif fmt == "markdown":
        return format_markdown(results)
    elif fmt == "matrix":
        return format_matrix(results)
    else:
        return format_human(results)


def _exit_code(results: list[RuleResult]) -> int:
    """Determine exit code from results."""
    if any(r.result == Result.DEVIATES for r in results):
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="shadow-spec-check",
        description="Deterministic dbt spec compliance checker",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to manifest.json (default: target/manifest.json)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # model subcommand
    model_parser = subparsers.add_parser("model", help="Check a single model")
    model_parser.add_argument("model_name", help="Model name to check")
    model_parser.add_argument("--format", choices=["human", "json", "markdown", "matrix"], default="human")
    model_parser.add_argument("--rule", help="Filter to a specific rule")
    model_parser.set_defaults(func=cmd_model)

    # all subcommand
    all_parser = subparsers.add_parser("all", help="Check all models")
    all_parser.add_argument("--format", choices=["human", "json", "markdown", "matrix"], default="human")
    all_parser.add_argument("--rule", help="Filter to a specific rule")
    all_parser.add_argument("--layer", choices=["staging", "intermediate", "marts", "semantic_models"])
    all_parser.set_defaults(func=cmd_all)

    # rules subcommand
    rules_parser = subparsers.add_parser("rules", help="List available rules")
    rules_parser.set_defaults(func=cmd_rules)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(2)

    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
