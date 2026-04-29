"""Matrix formatter: model x rule grid view."""

from __future__ import annotations

from ..models import Result, RuleResult


def format_matrix(results: list[RuleResult]) -> str:
    """Format results as a model-vs-rule matrix table."""
    if not results:
        return "No results to display."

    # Build lookup
    lookup: dict[tuple[str, str], RuleResult] = {}
    for r in results:
        lookup[(r.model, r.rule)] = r

    rules = sorted(set(r.rule for r in results))
    models = sorted(set(r.model for r in results))

    # Shorten rule names for display
    rule_short = [r.split(".")[-1][:12] for r in rules]

    lines = []
    # Header
    model_col_width = max(len(m) for m in models) + 2
    header = f"{'MODEL':<{model_col_width}}" + "".join(
        f"{rs:<14}" for rs in rule_short
    )
    lines.append(header)
    lines.append("-" * len(header))

    for model in models:
        cells = []
        for rule_name in rules:
            r = lookup.get((model, rule_name))
            if r is None or r.result == Result.NA:
                cells.append(f"{'-':<14}")
            elif r.result == Result.PASS:
                cells.append(f"{'PASS':<14}")
            elif r.result == Result.SUPPRESSED:
                cells.append(f"{'SUPPRESSED':<14}")
            else:
                cells.append(f"{'DEVIATES':<14}")

        lines.append(f"{model:<{model_col_width}}" + "".join(cells))

    return "\n".join(lines)
