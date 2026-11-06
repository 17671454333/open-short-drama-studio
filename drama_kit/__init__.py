"""
open-short-drama-studio (drama_kit)
-----------------------------------
Deterministic quality gates, storyboard & CapCut timeline planner, Seedance/Flow
credit budget optimizer, and HTML5 WebGame pre-flight doctor for AI Short-Drama & Game Studios.
"""

__version__ = "0.2.0"

from .gates import (
    validate_episode_outline,
    calculate_storyboard_budget,
    export_capcut_timeline_manifest,
    inspect_webgame_bundle,
    OutlineGateReport,
    BudgetEstimate,
    WebGameHealthReport,
)

__all__ = [
    "__version__",
    "validate_episode_outline",
    "calculate_storyboard_budget",
    "export_capcut_timeline_manifest",
    "inspect_webgame_bundle",
    "OutlineGateReport",
    "BudgetEstimate",
    "WebGameHealthReport",
]
