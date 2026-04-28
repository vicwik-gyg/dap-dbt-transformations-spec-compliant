"""Rule registry: decorator-based rule collection."""

from __future__ import annotations

from typing import Any, Callable

from .models import RuleInfo, RuleResult

# Global registry of all rules
_RULES: dict[str, Callable] = {}
_RULE_INFO: dict[str, RuleInfo] = {}


def rule(
    name: str,
    description: str = "",
    applies_to: list[str] | None = None,
    spec_ref: str = "",
) -> Callable:
    """Decorator to register a spec-check rule."""

    def decorator(fn: Callable) -> Callable:
        _RULES[name] = fn
        _RULE_INFO[name] = RuleInfo(
            name=name,
            description=description,
            applies_to=applies_to or [],
            spec_ref=spec_ref,
        )
        return fn

    return decorator


def get_all_rules() -> dict[str, Callable]:
    return dict(_RULES)


def get_rule_info() -> dict[str, RuleInfo]:
    return dict(_RULE_INFO)


def get_rule(name: str) -> Callable | None:
    return _RULES.get(name)


def run_rule(
    rule_name: str, node: dict[str, Any], manifest: dict[str, Any]
) -> RuleResult | None:
    """Run a single rule against a node. Returns None if rule doesn't apply."""
    fn = _RULES.get(rule_name)
    if fn is None:
        return None
    info = _RULE_INFO[rule_name]

    # Check if rule applies to this node's layer
    if info.applies_to:
        layer = _get_layer(node)
        if layer and layer not in info.applies_to and "all" not in info.applies_to:
            return RuleResult(
                model=node["name"],
                rule=rule_name,
                result=RuleResult.__module__  # placeholder
            )
            # Actually return NA
            return None

    return fn(node, manifest)


def _get_layer(node: dict[str, Any]) -> str:
    """Determine model layer from fqn or path."""
    fqn = node.get("fqn", [])
    if len(fqn) >= 2:
        layer = fqn[1]
        if layer in ("staging", "intermediate", "marts", "semantic_models"):
            return layer
    path = node.get("path", "")
    for layer in ("staging", "intermediate", "marts", "semantic_models"):
        if path.startswith(f"{layer}/"):
            return layer
    return ""
