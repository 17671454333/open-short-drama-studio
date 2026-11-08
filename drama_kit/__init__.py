"""
open-short-drama-studio (drama_kit)
-----------------------------------
Deterministic quality gates, storyboard & CapCut timeline planner, Seedance/Flow
credit budget optimizer, HTML5 WebGame pre-flight doctor, studio stereo audio/BGM
quality gate & six-segment storyboard prompt standardizer for AI Short-Drama & Game Studios.
"""

__version__ = "0.4.0"

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
from .storyboard_prompt import (
    standardize_shot_prompt,
    ShotPromptReport,
    DEFAULT_NEGATIVE_PROMPT,
    MODEL_STYLE_PRESETS,
)

__all__ = [
    "__version__",
    "validate_episode_outline",
    "calculate_storyboard_budget",
    "export_capcut_timeline_manifest",
    "inspect_webgame_bundle",
    "inspect_audio_track_quality",
    "standardize_shot_prompt",
    "OutlineGateReport",
    "BudgetEstimate",
    "WebGameHealthReport",
    "AudioGateReport",
    "ShotPromptReport",
    "STUDIO_BGM_LIBRARY_PRESETS",
    "DEFAULT_NEGATIVE_PROMPT",
    "MODEL_STYLE_PRESETS",
]
