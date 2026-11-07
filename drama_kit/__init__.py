"""
open-short-drama-studio (drama_kit)
-----------------------------------
Deterministic quality gates, storyboard & CapCut timeline planner, Seedance/Flow
credit budget optimizer, HTML5 WebGame pre-flight doctor & studio stereo audio/BGM
quality gate for AI Short-Drama & Game Studios.
"""

__version__ = "0.3.0"

from .gates import (
    validate_episode_outline,
    calculate_storyboard_budget,
    export_capcut_timeline_manifest,
    inspect_webgame_bundle,
    inspect_audio_track_quality,
    OutlineGateReport,
    BudgetEstimate,
    WebGameHealthReport,
    AudioGateReport,
    STUDIO_BGM_LIBRARY_PRESETS,
)

__all__ = [
    "__version__",
    "validate_episode_outline",
    "calculate_storyboard_budget",
    "export_capcut_timeline_manifest",
    "inspect_webgame_bundle",
    "inspect_audio_track_quality",
    "OutlineGateReport",
    "BudgetEstimate",
    "WebGameHealthReport",
    "AudioGateReport",
    "STUDIO_BGM_LIBRARY_PRESETS",
]
