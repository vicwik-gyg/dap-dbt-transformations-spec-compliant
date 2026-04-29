"""Human-readable table formatter."""

from __future__ import annotations

from ..models import Result, RuleResult


def format_human(results: list[RuleResult]) -> str:
    """Format results as a human-readable table."""
    if not results:
        return "No results to display."

    # Group by model for summary
    lines = []

    # Header
    lines.append(
        f"{'MODEL':<44} {'RULE':<32} {'RESULT':<10} FINDING"
    )
    lines.append("-" * 120)

    # Sort: DEVIATES first, then SUPPRESSED, then PASS, then NA
    priority = {Result.DEVIATES: 0, Result.SUPPRESSED: 1, Result.PASS: 2, Result.NA: 3}
    sorted_results = sorted(
        results, key=lambda r: (priority.get(r.result, 4), r.model, r.rule)
    )

    for r in sorted_results:
        if r.result == Result.NA:
            continue  # Skip NA in human output for readability
        finding = r.finding[:60] if r.finding else "-"
        lines.append(
            f"{r.model:<44} {r.rule:<32} {r.result.value:<10} {finding}"
        )

    # Summary
    pass_count = sum(1 for r in results if r.result == Result.PASS)
    dev_count = sum(1 for r in results if r.result == Result.DEVIATES)
    na_count = sum(1 for r in results if r.result == Result.NA)
    sup_count = sum(1 for r in results if r.result == Result.SUPPRESSED)

    lines.append("")
    lines.append(f"Summary: {pass_count} PASS / {dev_count} DEVIATES / {na_count} NA / {sup_count} SUPPRESSED")

    return "\n".join(lines)
