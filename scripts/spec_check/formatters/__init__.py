"""Output formatters for spec-check results."""

from .human import format_human
from .json_fmt import format_json
from .markdown import format_markdown
from .matrix import format_matrix

__all__ = ["format_human", "format_json", "format_markdown", "format_matrix"]
