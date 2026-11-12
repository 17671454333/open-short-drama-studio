"""
open-short-drama-studio (drama_kit)
-----------------------------------
Deterministic quality gates, storyboard & CapCut timeline planner, Seedance/Flow
credit budget optimizer, HTML5 WebGame pre-flight doctor, studio stereo audio/BGM
quality gate, vertical video caption safe-zone inspector & six-segment storyboard
prompt standardizer for AI Short-Drama & Game Studios.
"""

__version__ = "0.8.0"

from .gates import (
    validate_episode_outline,
    calculate_storyboard_budget,
    export_capcut_timeline_manifest,
    inspect_webgame_bundle,
    inspect_audio_track_quality,
    inspect_caption_safe_zone,
    inspect_social_cover_card,
    inspect_character_anchor_pack,
    inspect_master_video_delivery,
    OutlineGateReport,
    BudgetEstimate,
    WebGameHealthReport,
    AudioGateReport,
    CaptionSafeZoneReport,
    SocialCoverReport,
    CharacterAnchorReport,
    MasterVideoDeliveryReport,
    STUDIO_BGM_LIBRARY_PRESETS,
    PLATFORM_SAFE_MARGINS,
    COVER_RATIO_PRESETS,
    REQUIRED_CHARACTER_VIEWS,
    MASTER_DELIVERY_TARGETS,
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
    "inspect_caption_safe_zone",
    "inspect_social_cover_card",
    "inspect_character_anchor_pack",
    "inspect_master_video_delivery",
    "standardize_shot_prompt",
    "OutlineGateReport",
    "BudgetEstimate",
    "WebGameHealthReport",
    "AudioGateReport",
    "CaptionSafeZoneReport",
    "SocialCoverReport",
    "CharacterAnchorReport",
    "MasterVideoDeliveryReport",
    "STUDIO_BGM_LIBRARY_PRESETS",
    "PLATFORM_SAFE_MARGINS",
    "COVER_RATIO_PRESETS",
    "REQUIRED_CHARACTER_VIEWS",
    "MASTER_DELIVERY_TARGETS",
    "DEFAULT_NEGATIVE_PROMPT",
    "MODEL_STYLE_PRESETS",
]
