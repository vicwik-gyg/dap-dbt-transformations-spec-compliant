"""JSON formatter."""

from __future__ import annotations

import json

from ..models import RuleResult


def format_json(results: list[RuleResult]) -> str:
    """Format results as JSON array."""
    return json.dumps([r.to_dict() for r in results], indent=2)
