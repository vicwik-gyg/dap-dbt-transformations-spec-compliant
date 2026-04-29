"""Core data models for spec-check results."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Result(Enum):
    PASS = "PASS"
    DEVIATES = "DEVIATES"
    NA = "NA"
    SUPPRESSED = "SUPPRESSED"


@dataclass
class RuleResult:
    model: str
    rule: str
    result: Result
    finding: str = ""
    spec_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "rule": self.rule,
            "result": self.result.value,
            "finding": self.finding,
            "spec_ref": self.spec_ref,
        }


@dataclass
class RuleInfo:
    name: str
    description: str
    applies_to: list[str] = field(default_factory=list)
    spec_ref: str = ""
