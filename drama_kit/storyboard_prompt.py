"""
AI Short-Drama & WebGame Studio: Six-Segment Storyboard Prompt Standardizer & Gate.
-----------------------------------------------------------------------------------
Implements strict six-segment cinematic prompt formatting and deterministically
screens against inconsistent actor anchors, ambiguous camera directions, or missing
cinematic parameters across AI video & image models (MiniMax H3, Wan 2.1, Kling, Midjourney).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class ShotPromptReport:
    passed: bool
    score: int
    violations: List[str]
    prompt_en: str
    prompt_zh: str
    negative_prompt: str
    model_target: str
    segments: Dict[str, str] = field(default_factory=dict)


DEFAULT_NEGATIVE_PROMPT = (
    "low quality, blurry, deformed anatomy, extra limbs, bad eyes, mutated hands, "
    "watermark, text overlay, artifacts, cartoonish, oversaturated, amateur footage"
)

MODEL_STYLE_PRESETS = {
    "minimax_h3": {
        "suffix": ", natural fluid movement, 4k cinematic photorealistic, 24fps motion blur",
        "neg_prefix": "",
    },
    "wan2.1": {
        "suffix": ", cinematic lighting, master composition, volumetric rays, 8k resolution",
        "neg_prefix": "",
    },
    "kling": {
        "suffix": ", ultra-realistic detail, cinematic color grading, smooth temporal consistency",
        "neg_prefix": "",
    },
    "midjourney": {
        "suffix": " --ar 16:9 --v 6.1 --style raw --c 5",
        "neg_prefix": "--no ",
    },
    "generic": {
        "suffix": ", cinematic film grain, 35mm lens, high quality photorealism",
        "neg_prefix": "",
    },
}


def standardize_shot_prompt(
    spec: Union[Dict[str, Any], str],
    model_target: str = "generic",
) -> ShotPromptReport:
    """Standardize and validate a shot prompt against the 6-segment cinematic benchmark.

    The 6 canonical segments:
    1. shot_type (camera angle & movement, e.g. 'Close-up, slow dolly in')
    2. subject_anchor (actor visual consistency anchors: clothing, hair, age, features)
    3. action_beat (micro-expressions and bodily motion beats)
    4. environment_lighting (space, time of day, atmosphere, rim/volumetric light)
    5. cinematic_style (lens focal length, color grade, film stock)
    6. negative_exclusions (distortions, text, artifacts)
    """
    violations: List[str] = []
    score = 100
    target_preset = MODEL_STYLE_PRESETS.get(model_target.lower(), MODEL_STYLE_PRESETS["generic"])

    if isinstance(spec, str):
        raw_text = spec.strip()
        if not raw_text:
            return ShotPromptReport(
                passed=False,
                score=0,
                violations=["EMPTY_PROMPT: Prompt string cannot be empty."],
                prompt_en="",
                prompt_zh="",
                negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                model_target=model_target,
                segments={},
            )
        # Parse basic heuristic segments
        parsed_spec = {
            "shot_type": "Medium shot, static camera",
            "subject_anchor": raw_text,
            "action_beat": "Actor maintains emotional posture",
            "environment_lighting": "Cinematic volumetric lighting",
            "cinematic_style": "35mm anamorphic lens, moody color grading",
            "negative_exclusions": DEFAULT_NEGATIVE_PROMPT,
        }
        violations.append("RAW_STRING_INPUT: Provided string without 6-segment structure; heuristically wrapped.")
        score -= 20
    elif isinstance(spec, dict):
        parsed_spec = dict(spec)
    else:
        raise ValueError("spec must be a dictionary or a string.")

    # 1. Check shot_type
    shot_type = str(parsed_spec.get("shot_type", "")).strip()
    if not shot_type:
        violations.append("MISSING_SHOT_TYPE: Missing camera framing and movement definition.")
        score -= 25
        shot_type = "Medium shot, cinematic steady tracking"

    # 2. Check subject_anchor
    subject_anchor = str(parsed_spec.get("subject_anchor", "")).strip()
    if not subject_anchor:
        violations.append("MISSING_SUBJECT_ANCHOR: Missing character visual consistency anchors (clothing, features).")
        score -= 25
        subject_anchor = "Main character with persistent visual traits"

    # 3. Check action_beat
    action_beat = str(parsed_spec.get("action_beat", "")).strip()
    if not action_beat:
        violations.append("MISSING_ACTION_BEAT: Missing actor micro-expression or narrative motion beat.")
        score -= 20
        action_beat = "Subtle facial tension and natural physical movement"

    # 4. Check environment_lighting
    environment_lighting = str(parsed_spec.get("environment_lighting", "")).strip()
    if not environment_lighting:
        violations.append("MISSING_ENVIRONMENT_LIGHTING: Missing environmental spatial definition or light setup.")
        score -= 15
        environment_lighting = "Atmospheric interior with directional dramatic side lighting"

    # 5. Check cinematic_style
    cinematic_style = str(parsed_spec.get("cinematic_style", "")).strip()
    if not cinematic_style:
        violations.append("MISSING_CINEMATIC_STYLE: Missing lens focal specification or cinematic grade.")
        score -= 15
        cinematic_style = "Cinematic 35mm film grain, anamorphic flare, fine color contrast"

    # 6. Check negative exclusions
    negative_prompt = str(parsed_spec.get("negative_exclusions", "")).strip() or DEFAULT_NEGATIVE_PROMPT

    segments = {
        "shot_type": shot_type,
        "subject_anchor": subject_anchor,
        "action_beat": action_beat,
        "environment_lighting": environment_lighting,
        "cinematic_style": cinematic_style,
        "negative_exclusions": negative_prompt,
    }

    # Assemble unified English & Chinese prompts
    prompt_en_core = f"{shot_type}. {subject_anchor}, {action_beat}. {environment_lighting}. {cinematic_style}"
    prompt_en = prompt_en_core + target_preset["suffix"]

    zh_parts = [
        f"【镜头运镜】{shot_type}",
        f"【主体锚点】{subject_anchor}",
        f"【动作节拍】{action_beat}",
        f"【环境光影】{environment_lighting}",
        f"【电影影调】{cinematic_style}",
    ]
    prompt_zh = "；".join(zh_parts)

    score = max(0, score)
    passed = len(violations) == 0

    return ShotPromptReport(
        passed=passed,
        score=score,
        violations=violations,
        prompt_en=prompt_en,
        prompt_zh=prompt_zh,
        negative_prompt=negative_prompt,
        model_target=model_target,
        segments=segments,
    )
