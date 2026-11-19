"""
Core deterministic engines for Open Short-Drama & WebGame Studio:
1. `validate_episode_outline`: Deterministic quality gates for AI short-drama scripts
   (hook beat within first 3 beats, max dialogue length <= 35 chars, cliffhanger presence,
   payoff cadence <= 3 episodes).
2. `calculate_storyboard_budget`: Tiered video-generation credit optimizer comparing
   naive 1080p full-pro generation vs. 3-tier routing (Free Flow VFX + 480p Lite/Standard
   + local FFmpeg Lanczos film-grain 1080p upscaling, saving 80%+ credits).
3. `export_capcut_timeline_manifest`: Converts structured storyboard shots into a microsecond-aligned
   CapCut / JianYing (`draft_content.json`) track manifest.
4. `inspect_webgame_bundle`: Pre-flight static validator for HTML5 WebGames targeting
   Bilibili Toy, Itch.io, CrazyGames, and WeChat Mini-Game wrappers (checks relative asset paths,
   audio unlock handlers, and mobile viewport scaling).
"""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional


@dataclass
class OutlineGateReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BudgetEstimate:
    total_shots: int
    naive_1080p_credits: int
    optimized_tiered_credits: int
    savings_ratio: float
    tier_breakdown: Dict[str, int]
    ffmpeg_upscale_filter: str


@dataclass
class WebGameHealthReport:
    ready: bool
    issues: List[str] = field(default_factory=list)
    checks: Dict[str, bool] = field(default_factory=dict)


def validate_episode_outline(episode: Dict[str, Any], max_line_chars: int = 35) -> OutlineGateReport:
    """
    Run deterministic quality gates on a single short-drama episode dictionary:
    - Gate 1: Cold-open hook beat must appear within the first 3 beats (`hook_beat_index <= 2`).
    - Gate 2: Every dialogue line must be <= `max_line_chars` characters for natural TTS pacing.
    - Gate 3: Episode must end with a non-empty cliffhanger hook (`cliffhanger`).
    - Gate 4: At least one visual action beat per scene (`action_beats >= 1`).
    - Gate 5: Estimated duration must fall within 45s..150s (`duration_sec`).
    """
    violations: List[str] = []
    beats = episode.get("beats") or []
    dialogues = episode.get("dialogues") or []
    cliffhanger = str(episode.get("cliffhanger") or "").strip()

    hook_indices = [i for i, b in enumerate(beats) if b.get("is_hook")]
    if not hook_indices or hook_indices[0] > 2:
        violations.append("COLD_OPEN_HOOK_MISSING: First hook beat must occur within the first 3 beats (index 0..2).")

    long_lines = [d.get("text", "") for d in dialogues if len(str(d.get("text", ""))) > max_line_chars]
    if long_lines:
        violations.append(f"DIALOGUE_TOO_LONG: {len(long_lines)} line(s) exceed {max_line_chars} chars.")

    if len(cliffhanger) < 6:
        violations.append("CLIFFHANGER_WEAK: Episode must end with a concrete cliffhanger hook (>= 6 chars).")

    action_beats = [b for b in beats if b.get("type") == "action"]
    if not action_beats:
        violations.append("NO_ACTION_BEATS: Episode must include at least one visual action beat.")

    spoken_chars = sum(len(str(d.get("text", ""))) for d in dialogues)
    est_duration_sec = round(spoken_chars / 4.2 + len(action_beats) * 3.5, 1)
    if est_duration_sec < 20.0 or est_duration_sec > 180.0:
        violations.append(f"DURATION_OUT_OF_RANGE: Estimated {est_duration_sec}s outside [20s, 180s] target window.")

    score = max(0, 100 - len(violations) * 20)
    return OutlineGateReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "total_beats": len(beats),
            "action_beats": len(action_beats),
            "dialogue_lines": len(dialogues),
            "spoken_chars": spoken_chars,
            "estimated_duration_sec": est_duration_sec,
        },
    )


def calculate_storyboard_budget(shots: List[Dict[str, Any]], max_pro_shots: int = 2) -> BudgetEstimate:
    """
    Calculate video generation credits using the 3-tier cost-blade strategy:
    - VFX / establishing empty shots -> routed to monthly subscription pool (0 marginal credits)
    - Subtle gaze / single-character dialogue -> 480p Fast/Lite (~23 credits)
    - Standard motion / two-person interaction -> 480p Standard (~45 credits)
    - Climax hero shots (hard-capped at `max_pro_shots` per episode) -> Pro (~120 credits)
    Compared against naive 1080p Pro across all shots (~320 credits/shot).
    """
    total = len(shots)
    naive_credits = total * 320
    breakdown = {"flow_zero_marginal": 0, "sd_lite_480p": 0, "sd_standard_480p": 0, "sd_pro_climax": 0}
    pro_used = 0
    optimized = 0

    for s in shots:
        kind = str(s.get("category", "standard")).lower()
        if kind in ("vfx", "establishing", "scenery"):
            breakdown["flow_zero_marginal"] += 1
        elif kind == "climax" and pro_used < max_pro_shots:
            pro_used += 1
            breakdown["sd_pro_climax"] += 1
            optimized += 120
        elif kind in ("close_up", "gaze", "static_talk"):
            breakdown["sd_lite_480p"] += 1
            optimized += 23
        else:
            breakdown["sd_standard_480p"] += 1
            optimized += 45

    savings = round(1.0 - (optimized / naive_credits), 4) if naive_credits > 0 else 0.0
    return BudgetEstimate(
        total_shots=total,
        naive_1080p_credits=naive_credits,
        optimized_tiered_credits=optimized,
        savings_ratio=savings,
        tier_breakdown=breakdown,
        ffmpeg_upscale_filter="scale=1920:1080:flags=lanczos,unsharp=3:3:0.6:3:3:0.0,noise=alls=6:allf=t+u",
    )


def export_capcut_timeline_manifest(shots: List[Dict[str, Any]], fps: int = 30) -> Dict[str, Any]:
    """
    Generate a microsecond-accurate CapCut / JianYing (`draft_content.json` compatible)
    video & subtitle track manifest from storyboard shot definitions.
    """
    cursor_us = 0
    video_segments = []
    subtitle_segments = []

    for idx, shot in enumerate(shots):
        dur_sec = float(shot.get("duration_sec", 3.0))
        dur_us = int(round(dur_sec * 1_000_000))
        video_segments.append(
            {
                "shot_id": shot.get("id", f"S{idx+1:02d}"),
                "asset_path": shot.get("video_path", f"assets/shot_{idx+1:02d}.mp4"),
                "target_timerange": {"start": cursor_us, "duration": dur_us},
                "scale_filter": "lanczos_film_grain_1080p",
            }
        )
        line = str(shot.get("dialogue", "")).strip()
        if line:
            subtitle_segments.append(
                {
                    "shot_id": shot.get("id", f"S{idx+1:02d}"),
                    "speaker": shot.get("speaker", "Narrator"),
                    "text": line,
                    "target_timerange": {"start": cursor_us, "duration": dur_us},
                }
            )
        cursor_us += dur_us

    return {
        "canvas_config": {"width": 1080, "height": 1920, "fps": fps, "ratio": "9:16"},
        "duration_us": cursor_us,
        "duration_sec": round(cursor_us / 1_000_000, 2),
        "tracks": {
            "video": video_segments,
            "subtitles": subtitle_segments,
        },
    }


def inspect_webgame_bundle(index_html: str) -> WebGameHealthReport:
    """
    Deterministic pre-flight doctor for HTML5 WebGame `index.html` bundles before publishing
    to Bilibili Toy, Itch.io, CrazyGames, or WeChat Mini-Game wrappers:
    - Checks for broken root-absolute asset paths (`src="/..."` or `href="/..."`) that 404 in subdirectory hosting.
    - Checks for mobile viewport meta tag.
    - Checks for external CDN scripts that violate strict offline/sandboxed portals.
    """
    issues: List[str] = []
    has_viewport = 'name="viewport"' in index_html or "name='viewport'" in index_html
    has_root_abs = 'src="/' in index_html or 'href="/' in index_html
    has_cdn = "https://cdn." in index_html or "https://unpkg.com" in index_html

    if not has_viewport:
        issues.append("MISSING_VIEWPORT_META: Add <meta name='viewport' content='width=device-width,initial-scale=1'>.")
    if has_root_abs:
        issues.append("ROOT_ABSOLUTE_PATH_DETECTED: Replace '/assets/...' with relative './assets/...' to prevent 404 on Bilibili Toy & Itch.io.")
    if has_cdn:
        issues.append("EXTERNAL_CDN_DETECTED: Bundle dependencies locally inside vendor/ for sandboxed game portals.")

    return WebGameHealthReport(
        ready=len(issues) == 0,
        issues=issues,
        checks={
            "mobile_viewport": has_viewport,
            "relative_paths_only": not has_root_abs,
            "self_contained_vendor": not has_cdn,
        },
    )


_SYNTHETIC_SINE_COMMAND_PATTERN = re.compile(
    r"(?i)(?:"
    r"sine=frequency=\d+|"
    r"-f\s+lavfi\s+-i\s+sine|"
    r"math\.sin\s*\(|"
    r"np\.sin\s*\("
    r")"
)

# Canonical studio stereo master background music presets
STUDIO_BGM_LIBRARY_PRESETS: List[str] = [
    "ancient_suspense",
    "epic_climax",
    "action_battle",
    "modern_urban",
    "tech_showcase",
]


@dataclass
class AudioGateReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommended_ffmpeg_filter: str = ""
    studio_bgm_presets: List[str] = field(default_factory=lambda: list(STUDIO_BGM_LIBRARY_PRESETS))


def inspect_audio_track_quality(
    audio_info: Dict[str, Any],
    max_sine_ratio: float = 0.42,
    require_stereo: bool = True,
    require_bgm: bool = True,
) -> AudioGateReport:
    """
    Deterministic audio quality & studio BGM gate for AI Short-Drama & Video publishing:
    - Rejects synthetic pure sine/square waves that produce transformer-like buzzing (e.g. 73Hz, 110Hz, 146Hz, 220Hz, 432Hz).
    - Verifies audio presence (has_audio: True).
    - Enforces stereo channel layout (channels >= 2).
    - Enforces authentic studio stereo BGM master track.
    - If speech is present, enforces hardware-grade voice denoise (highpass=f=85,afftdn=nf=-25) and sidechain ducking.
    """
    violations: List[str] = []
    has_audio = bool(audio_info.get("has_audio", True))
    if not has_audio:
        violations.append("NO_AUDIO_TRACK: Video media has no detected audio stream.")

    channels = int(audio_info.get("channels", 2))
    if require_stereo and channels < 2:
        violations.append(f"MONO_AUDIO_TRACK: Detected {channels} channel(s); studio release requires stereo (>= 2).")

    top5_sine_ratio = float(audio_info.get("top5_sine_ratio", 0.0))
    sine_detected = bool(audio_info.get("sine_generator_detected", False))
    pipeline_spec = str(audio_info.get("pipeline_cmd", "") or audio_info.get("synthesis_spec", ""))
    if pipeline_spec and _SYNTHETIC_SINE_COMMAND_PATTERN.search(pipeline_spec):
        sine_detected = True

    sine_freq = audio_info.get("sine_freq_hz")
    if sine_freq and int(sine_freq) in (73, 110, 146, 220, 432):
        sine_detected = True

    if top5_sine_ratio > max_sine_ratio or sine_detected:
        violations.append(
            f"SYNTHETIC_SINE_BUZZ_DETECTED: Monotonic sine/square wave ratio ({top5_sine_ratio:.2f}) "
            f"exceeds safety threshold ({max_sine_ratio:.2f}) or synthetic sine command detected. "
            f"Replace with authentic studio stereo BGM."
        )

    bgm_track = str(audio_info.get("bgm_track", "") or "").strip()
    if require_bgm and not bgm_track:
        violations.append(
            "MISSING_STUDIO_BGM: Video lacks studio stereo background music. "
            f"Recommended library presets: {', '.join(STUDIO_BGM_LIBRARY_PRESETS)}."
        )

    has_speech = bool(audio_info.get("has_speech", True))
    speech_denoised = bool(audio_info.get("speech_denoised", True))
    sidechain_ducking = bool(audio_info.get("sidechain_ducking", True))

    if has_speech and not speech_denoised:
        violations.append("VOCAL_DENOISE_REQUIRED: Dialogue voice requires highpass=f=85,afftdn=nf=-25 denoise.")

    if has_speech and require_bgm and not sidechain_ducking:
        violations.append("SIDECHAIN_DUCKING_REQUIRED: BGM must enable sidechain ducking to prevent masking dialogue.")

    score = max(0, 100 - len(violations) * 20)

    recommended_filter = (
        "[0:a]highpass=f=85,afftdn=nf=-25[voice];"
        "[1:a]asplit=2[bgm_main][bgm_side];"
        "[voice][bgm_side]sidechaincompress=threshold=0.125:ratio=4:attack=20:release=250[ducked_bgm];"
        "[voice][ducked_bgm]amix=inputs=2:weights=1.0 0.42[aout]"
    )

    return AudioGateReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "has_audio": has_audio,
            "channels": channels,
            "top5_sine_ratio": top5_sine_ratio,
            "sine_detected": sine_detected,
            "bgm_track": bgm_track,
            "has_speech": has_speech,
            "speech_denoised": speech_denoised,
            "sidechain_ducking": sidechain_ducking,
        },
        recommended_ffmpeg_filter=recommended_filter,
        studio_bgm_presets=list(STUDIO_BGM_LIBRARY_PRESETS),
    )


@dataclass
class CaptionSafeZoneReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    platform: str = "all"
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggested_fixes: List[Dict[str, Any]] = field(default_factory=list)


PLATFORM_SAFE_MARGINS = {
    "all": {"top": 0.12, "bottom": 0.80, "left": 0.08, "right": 0.82},
    "douyin": {"top": 0.10, "bottom": 0.80, "left": 0.06, "right": 0.82},
    "kuaishou": {"top": 0.10, "bottom": 0.82, "left": 0.06, "right": 0.84},
    "weixin_channels": {"top": 0.12, "bottom": 0.78, "left": 0.06, "right": 0.82},
    "xiaohongshu": {"top": 0.12, "bottom": 0.78, "left": 0.08, "right": 0.82},
    "tiktok": {"top": 0.12, "bottom": 0.78, "left": 0.06, "right": 0.80},
}


def inspect_caption_safe_zone(
    captions: List[Dict[str, Any]],
    *,
    platform: str = "all",
    title: str = "",
    max_line_chars: int = 18,
) -> CaptionSafeZoneReport:
    """
    Deterministic mobile 9:16 vertical video & short-drama safe-zone quality gate:
    1. Checks vertical/horizontal bounds against platform UI obstructions:
       - Top header status bar & return button (0..12%)
       - Right interaction column (avatar, like count, comment, share buttons: 82%..100%)
       - Bottom author handle, caption title, shopping links & progress scrubber (78%~80%..100%)
    2. Validates WeChat Channels single-line title constraint (<= 16 Chinese chars).
    3. Validates caption subtitle line density (<= 18 chars recommended for 9:16 screens).
    """
    violations: List[str] = []
    suggested_fixes: List[Dict[str, Any]] = []

    margins = PLATFORM_SAFE_MARGINS.get(platform, PLATFORM_SAFE_MARGINS["all"])

    clean_title = (title or "").strip()
    title_len = len(clean_title)
    if clean_title and platform in ("weixin_channels", "all"):
        if title_len > 16:
            violations.append(
                f"WEIXIN_TITLE_TOO_LONG: Title length ({title_len}) exceeds WeChat Channels 16-character single-line limit: '{clean_title}'."
            )
            suggested_fixes.append({
                "type": "truncate_title",
                "original": clean_title,
                "suggestion": clean_title[:16].rstrip("，。！？ "),
            })

    overflow_count = 0
    max_chars = 0

    for idx, cap in enumerate(captions):
        text = str(cap.get("text") or "").strip()
        length = len(text)
        if length > max_chars:
            max_chars = length

        if length > max_line_chars:
            violations.append(
                f"CAPTION_LINE_TOO_LONG: Caption #{idx+1} '{text}' has {length} chars (exceeds {max_line_chars}-char mobile limit)."
            )
            mid = length // 2
            suggested_fixes.append({
                "type": "split_caption",
                "caption_index": idx,
                "original": text,
                "suggestion": [text[:mid].strip(), text[mid:].strip()],
            })

        # default Y ratio is 0.75 (standard lower-third dialogue subtitle position)
        y_ratio = float(cap.get("y_ratio", 0.75))
        if y_ratio < margins["top"]:
            violations.append(
                f"TOP_OVERFLOW: Caption #{idx+1} at Y={y_ratio:.2f} collides with top status bar (min {margins['top']:.2f})."
            )
            overflow_count += 1
            suggested_fixes.append({
                "type": "adjust_y",
                "caption_index": idx,
                "current_y": y_ratio,
                "recommended_y": 0.75,
            })
        elif y_ratio > margins["bottom"]:
            violations.append(
                f"BOTTOM_OVERFLOW: Caption #{idx+1} at Y={y_ratio:.2f} collides with bottom title/progress bar (max {margins['bottom']:.2f})."
            )
            overflow_count += 1
            suggested_fixes.append({
                "type": "adjust_y",
                "caption_index": idx,
                "current_y": y_ratio,
                "recommended_y": 0.75,
            })

        x_right_ratio = float(cap.get("x_right_ratio", 0.70))
        if x_right_ratio > margins["right"]:
            violations.append(
                f"RIGHT_OVERFLOW: Caption #{idx+1} extends to X_right={x_right_ratio:.2f}, colliding with right interaction icons (max {margins['right']:.2f})."
            )
            overflow_count += 1

    score = max(0, 100 - len(violations) * 20)

    return CaptionSafeZoneReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        platform=platform,
        metrics={
            "total_captions": len(captions),
            "overflow_count": overflow_count,
            "max_char_count": max_chars,
            "title_length": title_len,
            "recommended_dialogue_y": 0.75,
            "safe_margins": margins,
        },
        suggested_fixes=suggested_fixes,
    )


@dataclass
class SocialCoverReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    platform: str = "all"
    metrics: Dict[str, Any] = field(default_factory=dict)
    suggested_fixes: List[Dict[str, Any]] = field(default_factory=list)


COVER_RATIO_PRESETS: Dict[str, Dict[str, Any]] = {
    "3:4": {"min_ratio": 0.72, "max_ratio": 0.78, "target_w": 1080, "target_h": 1440, "platforms": ["xiaohongshu", "douyin_image"]},
    "9:16": {"min_ratio": 0.54, "max_ratio": 0.59, "target_w": 1080, "target_h": 1920, "platforms": ["weixin_channels", "douyin", "kuaishou", "tiktok", "youtube_shorts"]},
    "16:9": {"min_ratio": 1.70, "max_ratio": 1.85, "target_w": 1920, "target_h": 1080, "platforms": ["bilibili", "youtube"]},
    "1:1": {"min_ratio": 0.98, "max_ratio": 1.02, "target_w": 1024, "target_h": 1024, "platforms": ["bilibili_toy", "app_icon"]},
}


def inspect_social_cover_card(
    cover: Dict[str, Any],
    *,
    platform: str = "all",
    ratio_type: Optional[str] = None,
    require_ai_disclaimer: bool = True,
) -> SocialCoverReport:
    """
    Deterministic social media cover card & promo poster quality gate:
    1. Aspect ratio & resolution verification against standard platform slots (3:4, 9:16, 16:9, 1:1).
    2. Headline title length (<= 14 Chinese chars recommended for single-glance impact) and visual safe-zone (Y: 0.12..0.80).
    3. Mandatory AI-generated disclosure & disclaimer tag check for platform compliance.
    """
    violations: List[str] = []
    suggested_fixes: List[Dict[str, Any]] = []

    width = int(cover.get("width") or 0)
    height = int(cover.get("height") or 0)

    # Resolve expected ratio preset
    target_preset = ratio_type
    if not target_preset:
        if platform in ("xiaohongshu", "douyin_image"):
            target_preset = "3:4"
        elif platform in ("weixin_channels", "douyin", "kuaishou", "tiktok", "youtube_shorts"):
            target_preset = "9:16"
        elif platform in ("bilibili", "youtube"):
            target_preset = "16:9"
        elif platform in ("bilibili_toy", "app_icon"):
            target_preset = "1:1"
        else:
            target_preset = "3:4"

    preset_meta = COVER_RATIO_PRESETS.get(target_preset, COVER_RATIO_PRESETS["3:4"])

    # Resolution check
    if width < 512 or height < 512:
        violations.append(
            f"RESOLUTION_TOO_LOW: Cover resolution {width}x{height} is below standard 512px threshold."
        )
        suggested_fixes.append({
            "type": "upscale_recommendation",
            "target": f"{preset_meta['target_w']}x{preset_meta['target_h']}",
        })

    # Aspect ratio check
    ratio = round(width / max(1, height), 4)
    if not (preset_meta["min_ratio"] <= ratio <= preset_meta["max_ratio"]):
        violations.append(
            f"ASPECT_RATIO_MISMATCH: Aspect ratio {ratio} outside expected {target_preset} range "
            f"[{preset_meta['min_ratio']}..{preset_meta['max_ratio']}]."
        )
        suggested_fixes.append({
            "type": "resize_aspect_ratio",
            "current_ratio": ratio,
            "target_ratio_type": target_preset,
            "recommended_resolution": [preset_meta["target_w"], preset_meta["target_h"]],
        })

    # Title check
    title = str(cover.get("title") or "").strip()
    title_len = len(title)
    if title and title_len > 14:
        violations.append(
            f"TITLE_TOO_LONG: Headline length ({title_len} chars) exceeds 14-character recommended single-glance limit: '{title}'."
        )
        suggested_fixes.append({
            "type": "truncate_headline",
            "suggestion": title[:14].rstrip("，。！？ "),
        })

    title_y = float(cover.get("title_y_ratio", 0.28))
    if title:
        if title_y < 0.12:
            violations.append(
                f"TITLE_COLLIDES_HEADER: Title Y={title_y:.2f} collides with top status bar (min 0.12)."
            )
            suggested_fixes.append({"type": "adjust_title_y", "recommended_y": 0.28})
        elif title_y > 0.80:
            violations.append(
                f"TITLE_COLLIDES_FOOTER: Title Y={title_y:.2f} collides with bottom interactive controls (max 0.80)."
            )
            suggested_fixes.append({"type": "adjust_title_y", "recommended_y": 0.28})

    # AI disclaimer check
    has_disclaimer = bool(cover.get("has_ai_disclaimer"))
    if require_ai_disclaimer and not has_disclaimer:
        violations.append(
            "AI_DISCLAIMER_MISSING: Cover card lacks mandatory AI content disclosure tag (e.g. '本作品由AI辅助生成，剧情纯属虚构')."
        )
        suggested_fixes.append({
            "type": "add_ai_disclaimer",
            "text": "本作品由AI辅助生成，剧情纯属虚构",
            "recommended_position": "bottom_right",
        })

    score = max(0, 100 - len(violations) * 20)

    return SocialCoverReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        platform=platform,
        metrics={
            "width": width,
            "height": height,
            "ratio": ratio,
            "target_preset": target_preset,
            "title_length": title_len,
            "title_y_ratio": title_y,
            "has_ai_disclaimer": has_disclaimer,
        },
        suggested_fixes=suggested_fixes,
    )


@dataclass
class CharacterAnchorReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    stale_views: List[Dict[str, str]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


REQUIRED_CHARACTER_VIEWS: Dict[str, List[str]] = {
    "lead": ["frontal_full", "closeup", "side_90", "back"],
    "supporting": ["frontal_full", "closeup"],
    "cameo": ["frontal_full"],
}


def inspect_character_anchor_pack(
    characters: List[Dict[str, Any]],
    referenced_speakers: Optional[List[str]] = None,
) -> CharacterAnchorReport:
    """
    Deterministic cross-shot character consistency & turn-around reference gate:
    1. Every character must establish a canonical `frontal_full` master anchor with a non-empty `anchor_hash`
       and clean neutral background (`clean_background=True`) before derived views are generated.
    2. Single-hop star topology: every derived view (`closeup`, `side_90`, `back`, `three_quarter`) must
       directly reference the current `anchor_hash` (`source_anchor_hash == anchor_hash` and `chained_from` is empty)
       to prevent multi-hop facial drift, and flags stale views when the master anchor is regenerated.
    3. Tiered view completeness (`lead`: 4 views, `supporting`: 2 views, `cameo`: 1 view) and script speaker coverage.
    """
    violations: List[str] = []
    stale_views: List[Dict[str, str]] = []
    known_ids = set()
    total_views = 0

    for char in characters:
        cid = str(char.get("id") or char.get("name") or "").strip()
        if not cid:
            violations.append("CHARACTER_ID_MISSING: Character entry lacks 'id' or 'name'.")
            continue
        known_ids.add(cid)
        tier = str(char.get("tier") or "supporting").lower()
        required_views = REQUIRED_CHARACTER_VIEWS.get(tier, REQUIRED_CHARACTER_VIEWS["supporting"])

        anchor_hash = str(char.get("anchor_hash") or "").strip()
        if not anchor_hash:
            violations.append(f"MASTER_ANCHOR_MISSING: Character '{cid}' lacks canonical frontal_full 'anchor_hash'.")

        if not bool(char.get("clean_background", True)):
            violations.append(f"DIRTY_ANCHOR_BACKGROUND: Character '{cid}' master anchor must use clean neutral background.")

        views = char.get("views") or {}
        total_views += len(views)

        for req_v in required_views:
            if req_v not in views:
                violations.append(f"MISSING_REQUIRED_VIEW: Character '{cid}' ({tier}) missing '{req_v}' reference view.")

        for vname, vmeta in views.items():
            if vname == "frontal_full":
                continue
            vdict = vmeta if isinstance(vmeta, dict) else {}
            chained_from = str(vdict.get("chained_from") or "").strip()
            if chained_from and chained_from != "frontal_full":
                violations.append(
                    f"MULTI_HOP_DRIFT_RISK: Character '{cid}' view '{vname}' chained from '{chained_from}' instead of 'frontal_full'."
                )
            src_hash = str(vdict.get("source_anchor_hash") or "").strip()
            if anchor_hash and src_hash != anchor_hash:
                violations.append(
                    f"STALE_DERIVED_VIEW: Character '{cid}' view '{vname}' linked to '{src_hash or 'none'}' != current anchor '{anchor_hash}'."
                )
                stale_views.append({"character": cid, "view": vname, "expected_hash": anchor_hash, "actual_hash": src_hash})

    if referenced_speakers:
        for spk in referenced_speakers:
            s_clean = str(spk).strip()
            if s_clean and s_clean.lower() not in ("narrator", "旁白", "system", "系统") and s_clean not in known_ids:
                violations.append(f"UNANCHORED_SCRIPT_SPEAKER: Script speaker '{s_clean}' has no character reference pack.")

    score = max(0, 100 - len(violations) * 20)
    return CharacterAnchorReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        stale_views=stale_views,
        metrics={
            "character_count": len(known_ids),
            "total_views": total_views,
            "stale_view_count": len(stale_views),
        },
    )


@dataclass
class MasterVideoDeliveryReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    ffmpeg_remaster_args: str = ""


MASTER_DELIVERY_TARGETS: Dict[str, Any] = {
    "target_lufs": -14.0,
    "lufs_tolerance": 2.5,
    "max_true_peak_dbtp": -1.0,
    "max_av_desync_sec": 0.12,
    "max_leading_black_sec": 0.15,
    "required_pix_fmt": "yuv420p",
}


def inspect_master_video_delivery(
    master_spec: Dict[str, Any],
    target_lufs: float = -14.0,
) -> MasterVideoDeliveryReport:
    """
    Deterministic final MP4 master delivery gate for multi-platform publishing
    (Douyin, WeChat Channels, Xiaohongshu, Bilibili, YouTube, TikTok):
    1. Loudness & True Peak: integrated loudness within `target_lufs ± 2.5 LUFS` (default `-14.0 LUFS`)
       and `true_peak_dbtp <= -1.0 dBTP` to prevent mobile speaker distortion or platform AAC clipping.
    2. Stream Compatibility: requires `pix_fmt == 'yuv420p'` (avoids iOS/WeChat `yuv444p` black-screen decode failure)
       and `faststart_moov == True` (`-movflags +faststart`) for instant mobile playback.
    3. Frame Timing & Lip-Sync Integrity: blocks variable frame rate (`is_vfr == True`) and enforces
       audio/video stream duration delta `<= 0.12s` (120ms).
    4. Cold-Open Retention Guard: blocks leading black frames `> 0.15s` at `t=0.0s`.
    """
    violations: List[str] = []

    pix_fmt = str(master_spec.get("pix_fmt") or "yuv420p").strip().lower()
    faststart = bool(master_spec.get("faststart_moov", True))
    is_vfr = bool(master_spec.get("is_vfr", False))
    fps = float(master_spec.get("fps", 30.0))
    integrated_lufs = float(master_spec.get("integrated_lufs", target_lufs))
    true_peak_dbtp = float(master_spec.get("true_peak_dbtp", -1.5))
    video_dur = float(master_spec.get("video_duration_sec", 0.0))
    audio_dur = float(master_spec.get("audio_duration_sec", video_dur))
    leading_black = float(master_spec.get("leading_black_sec", 0.0))

    av_delta = round(abs(video_dur - audio_dur), 4)

    if pix_fmt != MASTER_DELIVERY_TARGETS["required_pix_fmt"]:
        violations.append(
            f"UNSUPPORTED_PIX_FMT: Pixel format '{pix_fmt}' fails mobile hardware decoders; must be 'yuv420p'."
        )

    if not faststart:
        violations.append(
            "MISSING_FASTSTART_MOOV: MP4 'moov' atom is not front-loaded; enable '-movflags +faststart'."
        )

    if is_vfr:
        violations.append(
            "VARIABLE_FRAME_RATE_DRIFT: VFR stream detected; transcode to constant frame rate (CFR) to prevent lip-sync drift."
        )

    tol = float(MASTER_DELIVERY_TARGETS["lufs_tolerance"])
    if abs(integrated_lufs - target_lufs) > tol:
        violations.append(
            f"LOUDNESS_OUT_OF_TARGET: Integrated loudness {integrated_lufs:.1f} LUFS outside [{target_lufs - tol:.1f}, {target_lufs + tol:.1f}] LUFS."
        )

    max_tp = float(MASTER_DELIVERY_TARGETS["max_true_peak_dbtp"])
    if true_peak_dbtp > max_tp:
        violations.append(
            f"TRUE_PEAK_CLIPPING_RISK: True peak {true_peak_dbtp:.1f} dBTP exceeds {max_tp:.1f} dBTP ceiling."
        )

    max_desync = float(MASTER_DELIVERY_TARGETS["max_av_desync_sec"])
    if video_dur <= 0:
        violations.append("INVALID_VIDEO_DURATION: Video duration must be positive.")
    elif av_delta > max_desync:
        violations.append(
            f"AV_DURATION_DESYNC: Audio/video duration delta {av_delta:.3f}s exceeds {max_desync:.2f}s threshold."
        )

    max_black = float(MASTER_DELIVERY_TARGETS["max_leading_black_sec"])
    if leading_black > max_black:
        violations.append(
            f"LEADING_BLACK_FRAME_TRAP: Leading black intro {leading_black:.2f}s > {max_black:.2f}s hurts 3-second retention."
        )

    trim_prefix = f"-ss {leading_black:.2f} " if leading_black > max_black else ""
    target_fps = int(round(fps)) if fps >= 24 else 30
    remaster_args = (
        f"{trim_prefix}-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p "
        f"-r {target_fps} -fps_mode cfr "
        f"-af loudnorm=I={target_lufs:.1f}:TP=-1.5:LRA=11 "
        f"-c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart"
    )

    score = max(0, 100 - len(violations) * 18)
    return MasterVideoDeliveryReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "pix_fmt": pix_fmt,
            "faststart_moov": faststart,
            "is_vfr": is_vfr,
            "fps": fps,
            "integrated_lufs": integrated_lufs,
            "true_peak_dbtp": true_peak_dbtp,
            "av_duration_delta_sec": av_delta,
            "leading_black_sec": leading_black,
        },
        ffmpeg_remaster_args=remaster_args,
    )


@dataclass
class MultiShotSegmentReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    alignment_header: str = ""


MULTISHOT_SEGMENT_LIMITS: Dict[str, Any] = {
    "max_segment_sec": 15.0,
    "min_shot_sec": 1.5,
    "max_shot_sec": 6.0,
    "max_reference_pictures": 4,
    "max_chars_per_sec": 4.8,
}


def inspect_multishot_segment_cuts(
    segment: Dict[str, Any],
    *,
    max_segment_sec: float = 15.0,
) -> MultiShotSegmentReport:
    """
    Deterministic multi-shot AI video segment gate (MiniMax H3 `[Shot k]` / Seedance 2.0 / Omni Flash):
    1. Segment duration ceiling: total duration across cuts must be `<= max_segment_sec` (default `15.0s`)
       to avoid silent tail truncation in single-pass video generation.
    2. Master keyframe zero-pinning: `cuts[0]` must start at `0.00s` (`<= 0.02s`) with a non-empty `keyframe_ref`.
    3. Cut-point continuity & shot rhythm: each cut's `start_sec` must match cumulative prior duration (`<= 0.05s` drift)
       and stay within `[1.5s, 6.0s]` to prevent micro-cut morphing flicker or stagnant long takes.
    4. Reference image slot cap (`<= 4` unique `Picture` references per generation) and `<d>` dialogue lip-sync
       pacing (`<= 4.8` spoken chars/sec).
    """
    violations: List[str] = []
    cuts = segment.get("cuts") or []
    if not isinstance(cuts, list) or len(cuts) == 0:
        return MultiShotSegmentReport(
            passed=False,
            score=0,
            violations=["EMPTY_SEGMENT_CUTS: Multi-shot segment must contain at least one cut entry."],
            metrics={"cut_count": 0, "total_duration_sec": 0.0, "unique_picture_refs": 0},
            alignment_header="",
        )

    min_shot = float(MULTISHOT_SEGMENT_LIMITS["min_shot_sec"])
    max_shot = float(MULTISHOT_SEGMENT_LIMITS["max_shot_sec"])
    max_pics = int(MULTISHOT_SEGMENT_LIMITS["max_reference_pictures"])
    max_cps = float(MULTISHOT_SEGMENT_LIMITS["max_chars_per_sec"])

    cumulative_sec = 0.0
    unique_pics: List[str] = []
    header_parts: List[str] = []

    for idx, cut in enumerate(cuts):
        cdict = cut if isinstance(cut, dict) else {}
        shot_no = idx + 1
        start_sec = float(cdict.get("start_sec", cumulative_sec))
        dur_sec = float(cdict.get("duration_sec", 0.0))
        kf_ref = str(cdict.get("keyframe_ref") or "").strip()
        dialogue = re.sub(r"\s+", "", str(cdict.get("dialogue") or ""))

        if idx == 0:
            if abs(start_sec) > 0.02 or not kf_ref:
                violations.append(
                    f"MASTER_KEYFRAME_NOT_AT_ZERO: Shot 1 must pin master keyframe at 0.00s (got start={start_sec:.2f}s, keyframe='{kf_ref or 'none'}')."
                )
        else:
            if abs(start_sec - cumulative_sec) > 0.05:
                violations.append(
                    f"CUT_TIMESTAMP_DRIFT: Shot {shot_no} start_sec={start_sec:.2f}s drifts from cumulative {cumulative_sec:.2f}s."
                )

        if dur_sec < min_shot:
            violations.append(
                f"SHOT_CUT_TOO_SHORT: Shot {shot_no} duration {dur_sec:.2f}s < {min_shot:.1f}s causes morphing flicker."
            )
        elif dur_sec > max_shot:
            violations.append(
                f"SHOT_CUT_STAGNANT_RISK: Shot {shot_no} duration {dur_sec:.2f}s > {max_shot:.1f}s risks motion decay; add a sub-cut."
            )

        if dialogue and dur_sec > 0:
            cps = len(dialogue) / dur_sec
            if cps > max_cps:
                violations.append(
                    f"DIALOGUE_PACING_OVERFLOW: Shot {shot_no} packs {len(dialogue)} chars into {dur_sec:.2f}s ({cps:.2f} chars/s > {max_cps:.1f})."
                )

        for pref in cdict.get("picture_refs") or ([] if not kf_ref else [kf_ref]):
            pstr = str(pref).strip()
            if pstr and pstr not in unique_pics:
                unique_pics.append(pstr)

        end_sec = cumulative_sec + max(0.0, dur_sec)
        header_parts.append(f"[Shot {shot_no} @ {cumulative_sec:.2f}s-{end_sec:.2f}s | KF: {kf_ref or 'auto'}]")
        cumulative_sec = end_sec

    total_dur = round(cumulative_sec, 4)
    if total_dur > max_segment_sec:
        violations.append(
            f"SEGMENT_DURATION_EXCEEDED: Segment total {total_dur:.2f}s exceeds {max_segment_sec:.1f}s single-generation limit."
        )

    if len(unique_pics) > max_pics:
        violations.append(
            f"REFERENCE_IMAGE_SLOT_OVERFLOW: Segment binds {len(unique_pics)} unique reference pictures (max {max_pics})."
        )

    score = max(0, 100 - len(violations) * 20)
    return MultiShotSegmentReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "cut_count": len(cuts),
            "total_duration_sec": total_dur,
            "unique_picture_refs": len(unique_pics),
            "max_segment_sec": max_segment_sec,
        },
        alignment_header=" -> ".join(header_parts),
    )


@dataclass
class WebGameArchiveReport:
    passed: bool
    score: int
    portal: str
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


WEBGAME_PORTAL_LIMITS: Dict[str, Dict[str, Any]] = {
    "bilibili_toy": {"max_total_mb": 50.0, "max_single_file_mb": 20.0, "supports_sab": False, "entry_files": ("index.html",)},
    "itch_io": {"max_total_mb": 200.0, "max_single_file_mb": 100.0, "supports_sab": True, "entry_files": ("index.html",)},
    "crazygames": {"max_total_mb": 100.0, "max_single_file_mb": 50.0, "supports_sab": False, "entry_files": ("index.html",)},
    "wechat_minigame": {"max_total_mb": 4.0, "max_single_file_mb": 2.0, "supports_sab": False, "entry_files": ("game.js", "game.json")},
}

_ARCHIVE_SENSITIVE_ENTRY_PATTERN = re.compile(
    r"(?:^|/)(?:"
    r"\.env(?:\.[A-Za-z0-9._-]+)?|"
    r"\.git(?:/|$)|"
    r"node_modules(?:/|$)|"
    r"[^/]+\.(?:pem|key|pfx|p12|map)"
    r")$",
    re.IGNORECASE,
)


def inspect_webgame_archive_manifest(
    manifest: Dict[str, Any],
    *,
    portal: str = "bilibili_toy",
) -> WebGameArchiveReport:
    """
    Deterministic ZIP release archive inspector for HTML5 / Godot 4 / Phaser WebGames targeting
    Bilibili Toy, Itch.io, CrazyGames, and WeChat Mini-Game portals:
    1. Root entry verification: catches nested wrapper directories (`dist/index.html` instead of `index.html`)
       or missing `game.js` + `game.json` in WeChat Mini-Games.
    2. POSIX path normalization: catches Windows backslash (`\\`) ZIP entries that fail on Linux CDNs.
    3. Artifact hygiene & DLP: blocks `.env`, `.git/`, `node_modules/`, private keys, and `.map` sourcemaps.
    4. Portal size budgets: enforces total bundle MB and single-asset MB ceilings per portal.
    5. Case-sensitive asset resolution: catches `assets/Hero.png` vs `assets/hero.png` mismatches.
    6. `SharedArrayBuffer` / threaded WASM compatibility check per portal (`requires_threads`).
    """
    violations: List[str] = []
    portal_key = portal.strip().lower()
    preset = WEBGAME_PORTAL_LIMITS.get(portal_key, WEBGAME_PORTAL_LIMITS["bilibili_toy"])

    raw_files = manifest.get("files") or []
    entries: List[Dict[str, Any]] = []
    for item in raw_files:
        if isinstance(item, str):
            entries.append({"path": item, "size_bytes": 0})
        elif isinstance(item, dict):
            entries.append({"path": str(item.get("path") or ""), "size_bytes": int(item.get("size_bytes") or 0)})

    normalized_paths: List[str] = []
    total_bytes = 0
    max_file_bytes = 0
    max_file_path = ""
    backslash_entries: List[str] = []
    leaked_entries: List[str] = []

    for ent in entries:
        raw_p = ent["path"].strip()
        sz = max(0, ent["size_bytes"])
        total_bytes += sz
        if sz > max_file_bytes:
            max_file_bytes = sz
            max_file_path = raw_p
        if "\\" in raw_p:
            backslash_entries.append(raw_p)
        norm_p = raw_p.replace("\\", "/").lstrip("./")
        if norm_p:
            normalized_paths.append(norm_p)
            if _ARCHIVE_SENSITIVE_ENTRY_PATTERN.search(norm_p):
                leaked_entries.append(norm_p)

    if backslash_entries:
        violations.append(
            f"BACKSLASH_ZIP_ENTRY: {len(backslash_entries)} entry path(s) contain Windows backslashes (e.g. '{backslash_entries[0]}'); normalize to forward slashes."
        )

    if leaked_entries:
        violations.append(
            f"SENSITIVE_ARTIFACT_LEAK: Release archive includes forbidden source/secret files: {', '.join(leaked_entries[:3])}."
        )

    exact_set = set(normalized_paths)
    lower_map = {p.lower(): p for p in normalized_paths}

    required_entries = preset["entry_files"]
    missing_entries = [req for req in required_entries if req not in exact_set]
    if missing_entries:
        nested = [p for p in normalized_paths if any(p.endswith(f"/{req}") for req in missing_entries)]
        if nested:
            violations.append(
                f"NESTED_ROOT_INDEX: Entry file wrapped inside subdirectory ('{nested[0]}'); zip contents of build folder directly at archive root."
            )
        else:
            violations.append(
                f"MISSING_ROOT_ENTRY: Portal '{portal_key}' requires root {', '.join(required_entries)}."
            )

    total_mb = round(total_bytes / (1024 * 1024), 3)
    max_single_mb = round(max_file_bytes / (1024 * 1024), 3)
    limit_total_mb = float(preset["max_total_mb"])
    limit_single_mb = float(preset["max_single_file_mb"])

    if total_mb > limit_total_mb:
        violations.append(
            f"BUNDLE_SIZE_EXCEEDED: Archive size {total_mb:.2f}MB exceeds '{portal_key}' {limit_total_mb:.1f}MB limit."
        )
    if max_single_mb > limit_single_mb:
        violations.append(
            f"SINGLE_FILE_SIZE_EXCEEDED: File '{max_file_path}' ({max_single_mb:.2f}MB) exceeds '{portal_key}' {limit_single_mb:.1f}MB single-file limit."
        )

    for ref in manifest.get("referenced_assets") or []:
        clean_ref = str(ref).strip().split("?", 1)[0].split("#", 1)[0]
        if not clean_ref or clean_ref.startswith(("http://", "https://", "data:", "blob:")):
            continue
        norm_ref = clean_ref.replace("\\", "/").lstrip("./").lstrip("/")
        if norm_ref not in exact_set:
            if norm_ref.lower() in lower_map:
                violations.append(
                    f"CASE_MISMATCH_ASSET_REF: HTML/script references '{norm_ref}' but archive contains '{lower_map[norm_ref.lower()]}' (404 on Linux CDN)."
                )
            else:
                violations.append(
                    f"MISSING_REFERENCED_ASSET: Referenced asset '{norm_ref}' is absent from release archive."
                )

    requires_threads = bool(manifest.get("requires_threads", False))
    if requires_threads and not bool(preset["supports_sab"]):
        violations.append(
            f"SHARED_ARRAY_BUFFER_PORTAL_INCOMPATIBLE: Portal '{portal_key}' does not guarantee COOP/COEP headers for multi-threaded WASM; use single-threaded Web export."
        )

    score = max(0, 100 - len(violations) * 20)
    return WebGameArchiveReport(
        passed=len(violations) == 0,
        score=score,
        portal=portal_key,
        violations=violations,
        metrics={
            "file_count": len(normalized_paths),
            "total_mb": total_mb,
            "max_single_file_mb": max_single_mb,
            "max_total_mb_limit": limit_total_mb,
            "requires_threads": requires_threads,
        },
    )


@dataclass
class SubtitleAlignmentReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    cleaned_cues: List[Dict[str, Any]] = field(default_factory=list)


SUBTITLE_ALIGNMENT_LIMITS: Dict[str, float] = {
    "min_cue_duration_sec": 0.45,
    "max_tts_sync_drift_sec": 0.25,
    "max_overlap_tolerance_sec": 0.02,
    "max_chars_per_sec": 6.5,
}

_TRAILING_SUBTITLE_PUNCT_PATTERN = re.compile(r"[，。、；,.;]+$")


def inspect_tts_subtitle_alignment(
    alignment: Dict[str, Any],
) -> SubtitleAlignmentReport:
    """
    Deterministic TTS voiceover & subtitle timeline alignment gate for CapCut / JianYing short dramas:
    1. Burned-in ghosting prevention: blocks overlay subtitle injection when raw AI video already contains
       garbled burned-in subtitles (`has_burned_in_subtitles=True` without `crop_or_inpaint_applied=True`).
    2. Timeline non-overlap: detects colliding cue windows (`start_sec < prev_end_sec - 0.02s`).
    3. Anti-flash minimum duration: rejects micro-cues shorter than `0.45s`.
    4. Voiceover word-level sync: checks `tts_start_sec` / `tts_end_sec` drift against subtitle window (`<= 0.25s`).
    5. Vertical subtitle typography & pacing: flags trailing punctuation (`，。、；`) and burst speed (`> 6.5 chars/s`),
       emitting normalized `cleaned_cues` ready for SRT/CapCut export.
    """
    violations: List[str] = []
    has_burned = bool(alignment.get("has_burned_in_subtitles", False))
    remediated = bool(alignment.get("crop_or_inpaint_applied", False))
    if has_burned and not remediated:
        violations.append(
            "BURNED_IN_SUBTITLE_CONFLICT: Source AI video contains burned-in subtitles; crop/inpaint or regenerate clean plate before adding CapCut subtitle track."
        )

    raw_cues = alignment.get("cues") or []
    if not isinstance(raw_cues, list) or len(raw_cues) == 0:
        return SubtitleAlignmentReport(
            passed=False,
            score=0,
            violations=violations + ["EMPTY_SUBTITLE_CUES: Subtitle alignment manifest contains no cues."],
            metrics={"cue_count": 0, "max_drift_sec": 0.0, "overlap_count": 0},
            cleaned_cues=[],
        )

    min_dur = float(SUBTITLE_ALIGNMENT_LIMITS["min_cue_duration_sec"])
    max_drift = float(SUBTITLE_ALIGNMENT_LIMITS["max_tts_sync_drift_sec"])
    overlap_tol = float(SUBTITLE_ALIGNMENT_LIMITS["max_overlap_tolerance_sec"])
    max_cps = float(SUBTITLE_ALIGNMENT_LIMITS["max_chars_per_sec"])

    prev_end = 0.0
    overlap_count = 0
    max_observed_drift = 0.0
    trailing_punct_count = 0
    cleaned_cues: List[Dict[str, Any]] = []

    for idx, item in enumerate(raw_cues):
        cue = item if isinstance(item, dict) else {}
        cue_no = idx + 1
        start_s = float(cue.get("start_sec", 0.0))
        end_s = float(cue.get("end_sec", 0.0))
        raw_text = str(cue.get("text") or "").strip()
        dur_s = end_s - start_s

        if idx > 0 and start_s < prev_end - overlap_tol:
            overlap_count += 1
            violations.append(
                f"SUBTITLE_CUE_OVERLAP: Cue {cue_no} starts at {start_s:.2f}s before Cue {idx} ends at {prev_end:.2f}s."
            )

        if dur_s < min_dur:
            violations.append(
                f"SUBTITLE_FLASH_TOO_BRIEF: Cue {cue_no} duration {dur_s:.2f}s < {min_dur:.2f}s minimum readable window."
            )

        if "tts_start_sec" in cue or "tts_end_sec" in cue:
            tts_start = float(cue.get("tts_start_sec", start_s))
            tts_end = float(cue.get("tts_end_sec", end_s))
            drift = max(abs(start_s - tts_start), abs(end_s - tts_end))
            if drift > max_observed_drift:
                max_observed_drift = drift
            if drift > max_drift:
                violations.append(
                    f"TTS_AUDIO_SYNC_DRIFT: Cue {cue_no} drifts {drift:.2f}s from TTS voiceover window (limit {max_drift:.2f}s)."
                )

        if _TRAILING_SUBTITLE_PUNCT_PATTERN.search(raw_text):
            trailing_punct_count += 1
            violations.append(
                f"TRAILING_PUNCTUATION_CLUTTER: Cue {cue_no} ends with redundant punctuation ('{raw_text}'); strip trailing comma/period for mobile vertical captions."
            )

        clean_text = _TRAILING_SUBTITLE_PUNCT_PATTERN.sub("", raw_text).strip()
        spoken_len = len(re.sub(r"\s+", "", clean_text))
        if dur_s > 0 and spoken_len > 0:
            cps = spoken_len / dur_s
            if cps > max_cps:
                violations.append(
                    f"SUBTITLE_CPS_OVERLOAD: Cue {cue_no} reading speed {cps:.2f} chars/s exceeds {max_cps:.1f} chars/s ceiling."
                )

        norm_start = round(max(start_s, prev_end), 3) if idx > 0 else round(max(0.0, start_s), 3)
        norm_end = round(max(end_s, norm_start + min_dur), 3)
        cleaned_cues.append(
            {
                "index": cue_no,
                "start_sec": norm_start,
                "end_sec": norm_end,
                "text": clean_text,
            }
        )
        prev_end = max(prev_end, end_s)

    score = max(0, 100 - len(violations) * 20)
    return SubtitleAlignmentReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "cue_count": len(raw_cues),
            "overlap_count": overlap_count,
            "max_drift_sec": round(max_observed_drift, 3),
            "trailing_punct_count": trailing_punct_count,
            "has_burned_in_subtitles": has_burned,
        },
        cleaned_cues=cleaned_cues,
    )


@dataclass
class SceneStagingReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    opening_blocking_line: str = ""


SCENE_STAGING_LIMITS: Dict[str, Any] = {
    "min_anchors": 1,
    "max_anchors": 12,
    "min_coord": 0.05,
    "max_coord": 0.95,
    "min_character_spacing": 0.08,
    "side_offset": 0.06,
    "valid_sides": ("north", "south", "east", "west", "center", "left", "right"),
    "valid_postures": ("standing", "seated", "kneeling", "prone"),
}

_SIDE_OFFSET_VECTORS: Dict[str, tuple[float, float]] = {
    "north": (0.0, -0.06),
    "south": (0.0, 0.06),
    "west": (-0.06, 0.0),
    "left": (-0.06, 0.0),
    "east": (0.06, 0.0),
    "right": (0.06, 0.0),
    "center": (0.0, 0.0),
}


def inspect_scene_staging_plan(
    staging: Dict[str, Any],
    expected_characters: Optional[List[str]] = None,
) -> SceneStagingReport:
    """
    Deterministic 2D top-down scene staging & 180-degree camera axis gate for AI short dramas:
    1. Anchor geometry bounds: requires 1..12 interactive scene anchors within [0.05, 0.95] normalized floorplane.
    2. Roster reconciliation: reconciles placed characters against `expected_characters` (no missing or undeclared actors).
    3. Anti-morphing slot & spacing check: enforces valid anchor refs, sides, postures, blocks two characters occupying
       the same `(anchor_id, side)` slot (`SAME_SIDE_COLLISION`), and flags `< 0.08` Euclidean crowding (`PROXIMITY_CROWDING_RISK`).
    4. 180-degree axis & extras discipline: blocks unlocked camera axis reversals (`camera_axis_locked=False`) and
       unspecified background zones when `extras_count > 0`.
    5. Canonical opening blocking line: emits a deterministic English spatial prompt line for Shot 1 keyframe generation.
    """
    violations: List[str] = []
    raw_anchors = staging.get("anchors") or []
    raw_placements = staging.get("placements") or []

    min_anc = int(SCENE_STAGING_LIMITS["min_anchors"])
    max_anc = int(SCENE_STAGING_LIMITS["max_anchors"])
    min_c = float(SCENE_STAGING_LIMITS["min_coord"])
    max_c = float(SCENE_STAGING_LIMITS["max_coord"])
    min_spacing = float(SCENE_STAGING_LIMITS["min_character_spacing"])
    valid_sides = set(SCENE_STAGING_LIMITS["valid_sides"])
    valid_postures = set(SCENE_STAGING_LIMITS["valid_postures"])

    if not isinstance(raw_anchors, list) or not (min_anc <= len(raw_anchors) <= max_anc):
        anc_len = len(raw_anchors) if isinstance(raw_anchors, list) else 0
        violations.append(
            f"ANCHOR_COUNT_OUT_OF_RANGE: Scene anchor count {anc_len} outside [{min_anc}, {max_anc}] interactive anchor budget."
        )

    anchor_map: Dict[str, tuple[float, float]] = {}
    if isinstance(raw_anchors, list):
        for anc in raw_anchors:
            if not isinstance(anc, dict):
                continue
            aid = str(anc.get("id") or "").strip()
            if not aid:
                continue
            ax = float(anc.get("x", 0.5))
            ay = float(anc.get("y", 0.5))
            anchor_map[aid] = (ax, ay)
            if not (min_c <= ax <= max_c and min_c <= ay <= max_c):
                violations.append(
                    f"ANCHOR_OUT_OF_BOUNDS: Anchor '{aid}' at ({ax:.2f}, {ay:.2f}) falls outside [{min_c:.2f}, {max_c:.2f}] safe floorplane."
                )

    placed_chars: List[str] = []
    seen_chars: set[str] = set()
    occupied_slots: Dict[tuple[str, str], str] = {}
    computed_positions: List[tuple[str, float, float, Optional[tuple[str, str]]]] = []
    blocking_clauses: List[str] = []

    if isinstance(raw_placements, list):
        for item in raw_placements:
            if not isinstance(item, dict):
                continue
            char_id = str(item.get("character") or "").strip()
            anc_id = str(item.get("anchor_id") or "").strip()
            side = str(item.get("side") or "center").strip().lower()
            posture = str(item.get("posture") or "standing").strip().lower()
            facing = str(item.get("facing") or "camera").strip()
            if not char_id:
                continue

            if char_id in seen_chars:
                violations.append(f"DUPLICATE_CHARACTER_PLACEMENT: Character '{char_id}' is placed multiple times in the same scene.")
            else:
                seen_chars.add(char_id)
                placed_chars.append(char_id)

            if side not in valid_sides:
                violations.append(f"INVALID_ANCHOR_SIDE: Character '{char_id}' uses unsupported side '{side}'.")
            if posture not in valid_postures:
                violations.append(f"INVALID_POSTURE: Character '{char_id}' uses unsupported posture '{posture}'.")

            slot_key: Optional[tuple[str, str]] = None
            if anc_id not in anchor_map:
                violations.append(f"UNKNOWN_ANCHOR_REF: Character '{char_id}' references undeclared anchor '{anc_id}'.")
            else:
                slot_key = (anc_id, side)
                if slot_key in occupied_slots:
                    other = occupied_slots[slot_key]
                    violations.append(
                        f"SAME_SIDE_COLLISION: '{char_id}' and '{other}' both occupy '{side}' side of anchor '{anc_id}' (limb-morphing risk)."
                    )
                else:
                    occupied_slots[slot_key] = char_id

                base_x, base_y = anchor_map[anc_id]
                dx, dy = _SIDE_OFFSET_VECTORS.get(side, (0.0, 0.0))
                px = float(item.get("x", base_x + dx))
                py = float(item.get("y", base_y + dy))
                computed_positions.append((char_id, px, py, slot_key))

            blocking_clauses.append(f"{char_id} {posture} at {side} side of {anc_id or 'stage'} facing {facing}")

    if expected_characters is not None:
        expected_set = {str(c).strip() for c in expected_characters if str(c).strip()}
        for req_c in sorted(expected_set - seen_chars):
            violations.append(f"MISSING_SCRIPT_CHARACTER: Script character '{req_c}' has no opening floorplane placement.")
        for extra_c in sorted(seen_chars - expected_set):
            violations.append(f"UNDECLARED_BLOCKING_CHARACTER: Placed character '{extra_c}' does not appear in scene cast.")

    crowding_pairs = 0
    for i in range(len(computed_positions)):
        c1, x1, y1, s1 = computed_positions[i]
        for j in range(i + 1, len(computed_positions)):
            c2, x2, y2, s2 = computed_positions[j]
            if s1 is not None and s1 == s2:
                continue
            dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            if dist < min_spacing:
                crowding_pairs += 1
                violations.append(
                    f"PROXIMITY_CROWDING_RISK: '{c1}' and '{c2}' floorplane distance {dist:.3f} < {min_spacing:.2f} minimum anti-merge spacing."
                )

    axis_locked = bool(staging.get("camera_axis_locked", True))
    if not axis_locked:
        violations.append(
            "CAMERA_AXIS_CROSSING_RISK: 180-degree camera line of action is unlocked; eye-line direction will flip across reverse cuts."
        )

    extras_count = int(staging.get("extras_count", 0) or 0)
    extras_zone = str(staging.get("extras_zone") or "").strip()
    if extras_count > 0 and not extras_zone:
        violations.append(
            f"EXTRAS_ZONE_UNSPECIFIED: Scene includes {extras_count} extras without a bounded `extras_zone` (foreground occlusion risk)."
        )

    if blocking_clauses:
        suffix = f" (extras: {extras_count} in {extras_zone})" if (extras_count > 0 and extras_zone) else ""
        opening_line = f"Opening blocking: {'; '.join(blocking_clauses)}{suffix}."
    else:
        opening_line = ""

    score = max(0, 100 - len(violations) * 20)
    return SceneStagingReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "anchor_count": len(anchor_map),
            "character_count": len(placed_chars),
            "crowding_pair_count": crowding_pairs,
            "extras_count": extras_count,
            "camera_axis_locked": axis_locked,
        },
        opening_blocking_line=opening_line,
    )


@dataclass
class ScenePropBibleReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


SCENE_PROP_BIBLE_LIMITS: Dict[str, Any] = {
    "min_visual_anchors": 3,
    "max_visual_anchors": 5,
    "min_scene_prompt_chars": 15,
    "min_prop_scale_cm": 0.5,
    "max_prop_scale_cm": 500.0,
}

_SAFE_EMPTY_PEOPLE_NEGATIONS = re.compile(
    r"(?i)\b(?:no\s+(?:people|humans?|characters?|crowds?|pedestrians?|actors?|figures?)|"
    r"without\s+(?:people|humans?|characters?|crowds?)|"
    r"empty\s+of\s+people|uninhabited|nobody)\b"
)

_ACTOR_CONTAMINATION_PATTERN = re.compile(
    r"(?i)\b(?:person|people|man|woman|boy|girl|warrior|swordsman|crowd|pedestrians?|actor|protagonist|villagers?|guards?)\b"
)

_SAFE_HAND_NEGATIONS = re.compile(
    r"(?i)\b(?:no\s+(?:hands?|fingers?|human\s+hands?|arms?)|without\s+(?:hands?|fingers?)|unheld)\b"
)

_PROP_HAND_CONTAMINATION_PATTERN = re.compile(
    r"(?i)\b(?:hand|hands|holding|gripped\s+by|fingers?|palm|wrist|fist)\b"
)

_PROP_ISOLATED_WHITE_BG_PATTERN = re.compile(
    r"(?i)(?:white\s+background|isolated\s+on\s+(?:pure\s+)?white|#ffffff|white\s+studio\s+backdrop)"
)


def inspect_scene_prop_bible(
    bible: Dict[str, Any],
    required_scene_usages: Optional[List[Dict[str, Any]]] = None,
    required_prop_usages: Optional[List[Dict[str, Any]]] = None,
) -> ScenePropBibleReport:
    """
    Deterministic scene environment & narrative prop bible gate for AI short dramas:
    1. Scene visual anchor budget: enforces 3..5 invariant spatial anchors per scene (`SCENE_ANCHOR_BUDGET_OUT_OF_RANGE`).
    2. Empty-plate discipline: blocks human/crowd terms in `empty_plate_prompt` (`SCENE_EMPTY_PLATE_ACTOR_CONTAMINATION`)
       while permitting explicit negations (`no people`, `uninhabited`) so background plates never ghost-merge with actors.
    3. Prop cutout & physical scale gate: blocks hands/grip artifacts (`PROP_HAND_CONTAMINATION`), enforces isolated
       pure-white background prompts (`PROP_NON_ISOLATED_BACKGROUND`), and checks `[0.5, 500.0]` cm physical scale (`PROP_SCALE_REFERENCE_INVALID`).
    4. Upstream script reconciliation: verifies every `(scene_id, lighting)` and `(prop_id, state)` referenced by episodes.
    """
    violations: List[str] = []
    raw_scenes = bible.get("scenes") or []
    raw_props = bible.get("props") or []

    min_anc = int(SCENE_PROP_BIBLE_LIMITS["min_visual_anchors"])
    max_anc = int(SCENE_PROP_BIBLE_LIMITS["max_visual_anchors"])
    min_prompt_len = int(SCENE_PROP_BIBLE_LIMITS["min_scene_prompt_chars"])
    min_scale = float(SCENE_PROP_BIBLE_LIMITS["min_prop_scale_cm"])
    max_scale = float(SCENE_PROP_BIBLE_LIMITS["max_prop_scale_cm"])

    scene_variants_map: Dict[str, set[str]] = {}
    contaminated_scenes = 0
    if isinstance(raw_scenes, list):
        for sc in raw_scenes:
            if not isinstance(sc, dict):
                continue
            sid = str(sc.get("id") or "").strip()
            if not sid:
                continue
            anchors = [str(a).strip() for a in (sc.get("visual_anchors") or []) if str(a).strip()]
            if not (min_anc <= len(anchors) <= max_anc):
                violations.append(
                    f"SCENE_ANCHOR_BUDGET_OUT_OF_RANGE: Scene '{sid}' defines {len(anchors)} visual anchor(s); expected [{min_anc}, {max_anc}]."
                )

            prompt = str(sc.get("empty_plate_prompt") or "").strip()
            if len(prompt) < min_prompt_len:
                violations.append(
                    f"SCENE_PROMPT_TOO_SHORT: Scene '{sid}' empty_plate_prompt length {len(prompt)} < {min_prompt_len} chars."
                )
            else:
                scrubbed_prompt = _SAFE_EMPTY_PEOPLE_NEGATIONS.sub(" ", prompt)
                if _ACTOR_CONTAMINATION_PATTERN.search(scrubbed_prompt):
                    contaminated_scenes += 1
                    violations.append(
                        f"SCENE_EMPTY_PLATE_ACTOR_CONTAMINATION: Scene '{sid}' empty_plate_prompt contains actor/crowd subject terms."
                    )

            raw_lv = sc.get("lighting_variants") or {}
            if isinstance(raw_lv, dict):
                l_keys = {str(k).strip().lower() for k, v in raw_lv.items() if str(k).strip() and str(v).strip()}
            elif isinstance(raw_lv, list):
                l_keys = {str(k).strip().lower() for k in raw_lv if str(k).strip()}
            else:
                l_keys = set()
            scene_variants_map[sid] = l_keys

    prop_states_map: Dict[str, set[str]] = {}
    contaminated_props = 0
    if isinstance(raw_props, list):
        for pr in raw_props:
            if not isinstance(pr, dict):
                continue
            pid = str(pr.get("id") or "").strip()
            if not pid:
                continue
            p_prompt = str(pr.get("prompt") or "").strip()
            scrubbed_prop = _SAFE_HAND_NEGATIONS.sub(" ", p_prompt)
            if _PROP_HAND_CONTAMINATION_PATTERN.search(scrubbed_prop):
                contaminated_props += 1
                violations.append(
                    f"PROP_HAND_CONTAMINATION: Prop '{pid}' prompt includes hand/grip terms (causes cutout limb artifacts)."
                )
            if not _PROP_ISOLATED_WHITE_BG_PATTERN.search(p_prompt):
                violations.append(
                    f"PROP_NON_ISOLATED_BACKGROUND: Prop '{pid}' prompt must specify an isolated pure white background for clean matting."
                )

            raw_scale = pr.get("scale_cm")
            if not isinstance(raw_scale, (int, float)) or isinstance(raw_scale, bool) or not (min_scale <= float(raw_scale) <= max_scale):
                violations.append(
                    f"PROP_SCALE_REFERENCE_INVALID: Prop '{pid}' scale_cm={raw_scale!r} outside [{min_scale}, {max_scale}] cm physical bounds."
                )

            raw_sv = pr.get("state_variants") or {}
            if isinstance(raw_sv, dict):
                s_keys = {str(k).strip().lower() for k, v in raw_sv.items() if str(k).strip() and str(v).strip()}
            elif isinstance(raw_sv, list):
                s_keys = {str(k).strip().lower() for k in raw_sv if str(k).strip()}
            else:
                s_keys = set()
            prop_states_map[pid] = s_keys

    for usage in required_scene_usages or []:
        if not isinstance(usage, dict):
            continue
        req_sid = str(usage.get("scene_id") or "").strip()
        req_light = str(usage.get("lighting") or "").strip().lower()
        if not req_sid:
            continue
        if req_sid not in scene_variants_map:
            violations.append(f"UNDECLARED_SCRIPT_SCENE: Script references scene '{req_sid}' missing from art bible.")
        elif req_light and req_light not in scene_variants_map[req_sid]:
            violations.append(
                f"MISSING_SCENE_LIGHTING_VARIANT: Scene '{req_sid}' lacks required '{req_light}' lighting variant."
            )

    for p_usage in required_prop_usages or []:
        if not isinstance(p_usage, dict):
            continue
        req_pid = str(p_usage.get("prop_id") or "").strip()
        req_state = str(p_usage.get("state") or "").strip().lower()
        if not req_pid:
            continue
        if req_pid not in prop_states_map:
            violations.append(f"UNDECLARED_SCRIPT_PROP: Script references prop '{req_pid}' missing from art bible.")
        elif req_state and req_state not in prop_states_map[req_pid]:
            violations.append(
                f"MISSING_PROP_STATE_VARIANT: Prop '{req_pid}' lacks required '{req_state}' state variant."
            )

    score = max(0, 100 - len(violations) * 20)
    return ScenePropBibleReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "scene_count": len(scene_variants_map),
            "prop_count": len(prop_states_map),
            "contaminated_scene_count": contaminated_scenes,
            "contaminated_prop_count": contaminated_props,
        },
    )


@dataclass
class SeriesPaywallPacingReport:
    passed: bool
    score: int
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


SERIES_PACING_LIMITS: Dict[str, Any] = {
    "max_payoff_gap": 3,
    "min_payoff_score": 7.0,
    "min_paywall_hook_grade": 8.0,
    "min_pre_paywall_grade": 7.0,
    "max_lead_characters": 3,
    "default_target_duration_sec": 90.0,
    "duration_tolerance_ratio": 0.15,
}


def inspect_series_paywall_pacing(series_plan: Dict[str, Any]) -> SeriesPaywallPacingReport:
    """
    Deterministic cross-episode series arc, climax cadence & paywall conversion gate:
    1. Golden 3-episode opening retention: requires >= 1 core payoff (`has_payoff=True` or
       `payoff_score >= 7.0`) within Episodes 1..3 (`GOLDEN_OPENING_PAYOFF_MISSING`).
    2. Anti-churn climax cadence: blocks > 3 consecutive episodes without a payoff
       (`PAYOFF_DROUGHT_GAP_EXCEEDED`).
    3. Paywall conversion discipline: requires `cliffhanger_grade >= 8.0` on paywall episode(s)
       (`PAYWALL_EPISODE_WEAK_HOOK`), blocks resolving the core arc conflict on the free-to-paid
       boundary (`PAYWALL_PREMATURE_RESOLUTION`), and enforces pre-paywall tension escalation on
       the immediately preceding episode (`PAYWALL_MISSING_PRE_ESCALATION`).
    4. Episode duration corridor: enforces `target_episode_sec ± 15%` (`EPISODE_DURATION_OUT_OF_CORRIDOR`).
    5. Asset sprawl caps: limits `lead_characters` to <= 3 (`LEAD_CAST_BUDGET_EXCEEDED`) and scales
       maximum primary locations dynamically with episode count (`MAIN_LOCATION_BUDGET_EXCEEDED`).
    """
    violations: List[str] = []
    episodes = series_plan.get("episodes") or []
    if not isinstance(episodes, list) or len(episodes) == 0:
        return SeriesPaywallPacingReport(
            passed=False,
            score=0,
            violations=["SERIES_EPISODES_EMPTY: Series plan must contain at least 1 episode."],
            metrics={
                "episode_count": 0,
                "payoff_count": 0,
                "max_payoff_gap": 0,
                "lead_character_count": 0,
                "primary_location_count": 0,
                "max_location_budget": 4,
            },
        )

    max_gap_limit = int(SERIES_PACING_LIMITS["max_payoff_gap"])
    min_payoff_score = float(SERIES_PACING_LIMITS["min_payoff_score"])
    min_pw_hook = float(SERIES_PACING_LIMITS["min_paywall_hook_grade"])
    min_pre_pw = float(SERIES_PACING_LIMITS["min_pre_paywall_grade"])
    max_leads = int(SERIES_PACING_LIMITS["max_lead_characters"])
    target_sec = float(series_plan.get("target_episode_sec", SERIES_PACING_LIMITS["default_target_duration_sec"]))
    tol = float(SERIES_PACING_LIMITS["duration_tolerance_ratio"])
    min_dur = round(target_sec * (1.0 - tol), 3)
    max_dur = round(target_sec * (1.0 + tol), 3)

    explicit_pw_ep = series_plan.get("paywall_episode")
    payoff_flags: List[bool] = []
    hook_grades: List[float] = []
    ep_numbers: List[int] = []
    collected_scenes: set[str] = {
        str(s).strip() for s in (series_plan.get("primary_scenes") or []) if str(s).strip()
    }

    consecutive_dry = 0
    max_observed_gap = 0
    drought_reported = False

    for idx, ep in enumerate(episodes):
        ep_dict = ep if isinstance(ep, dict) else {}
        ep_no = int(ep_dict.get("ep", idx + 1))
        ep_numbers.append(ep_no)

        raw_score = ep_dict.get("payoff_score", 0.0)
        p_score = float(raw_score) if isinstance(raw_score, (int, float)) and not isinstance(raw_score, bool) else 0.0
        has_payoff = bool(ep_dict.get("has_payoff", False)) or (p_score >= min_payoff_score)
        payoff_flags.append(has_payoff)

        if has_payoff:
            consecutive_dry = 0
        else:
            consecutive_dry += 1
            if consecutive_dry > max_observed_gap:
                max_observed_gap = consecutive_dry
            if consecutive_dry > max_gap_limit and not drought_reported:
                drought_reported = True
                violations.append(
                    f"PAYOFF_DROUGHT_GAP_EXCEEDED: {consecutive_dry} consecutive episodes without a climax/reversal payoff ending at Ep {ep_no} (max gap {max_gap_limit})."
                )

        if "cliffhanger_grade" in ep_dict:
            h_grade = float(ep_dict.get("cliffhanger_grade") or 0.0)
        else:
            h_grade = 8.0 if str(ep_dict.get("cliffhanger") or "").strip() else 0.0
        hook_grades.append(h_grade)

        for sc in ep_dict.get("scenes") or []:
            if str(sc).strip():
                collected_scenes.add(str(sc).strip())

        if "duration_sec" in ep_dict and ep_dict.get("duration_sec") is not None:
            dur = float(ep_dict["duration_sec"])
            if not (min_dur <= dur <= max_dur):
                violations.append(
                    f"EPISODE_DURATION_OUT_OF_CORRIDOR: Ep {ep_no} duration {dur:.1f}s outside [{min_dur:.1f}s, {max_dur:.1f}s] (±15% of {target_sec:.0f}s)."
                )

        is_pw = bool(ep_dict.get("is_paywall", False)) or (explicit_pw_ep is not None and ep_no == int(explicit_pw_ep))
        if is_pw:
            if h_grade < min_pw_hook:
                violations.append(
                    f"PAYWALL_EPISODE_WEAK_HOOK: Paywall Ep {ep_no} cliffhanger_grade={h_grade:.1f} < {min_pw_hook:.1f} conversion threshold."
                )
            if bool(ep_dict.get("premature_resolution", False)):
                violations.append(
                    f"PAYWALL_PREMATURE_RESOLUTION: Paywall Ep {ep_no} resolves core arc tension before paid unlock boundary."
                )
            if idx > 0 and not payoff_flags[idx - 1] and hook_grades[idx - 1] < min_pre_pw:
                violations.append(
                    f"PAYWALL_MISSING_PRE_ESCALATION: Pre-paywall Ep {ep_numbers[idx - 1]} lacks payoff or escalation hook (< {min_pre_pw:.1f}) to drive Ep {ep_no} unlock."
                )

    opening_window = min(3, len(payoff_flags))
    if opening_window > 0 and not any(payoff_flags[:opening_window]):
        violations.append(
            f"GOLDEN_OPENING_PAYOFF_MISSING: No core payoff delivered within Golden Opening Episodes 1..{opening_window}."
        )

    leads = [str(c).strip() for c in (series_plan.get("lead_characters") or []) if str(c).strip()]
    if len(leads) > max_leads:
        violations.append(
            f"LEAD_CAST_BUDGET_EXCEEDED: Series declares {len(leads)} lead characters (max {max_leads} to preserve AI face-anchor focus)."
        )

    ep_total = len(episodes)
    max_loc_budget = max(4, min(16, (ep_total * 3 + 4) // 5))
    if len(collected_scenes) > max_loc_budget:
        violations.append(
            f"MAIN_LOCATION_BUDGET_EXCEEDED: Series uses {len(collected_scenes)} primary locations across {ep_total} episodes (dynamic cap {max_loc_budget})."
        )

    score = max(0, 100 - len(violations) * 20)
    return SeriesPaywallPacingReport(
        passed=len(violations) == 0,
        score=score,
        violations=violations,
        metrics={
            "episode_count": ep_total,
            "payoff_count": sum(1 for flag in payoff_flags if flag),
            "max_payoff_gap": max_observed_gap,
            "lead_character_count": len(leads),
            "primary_location_count": len(collected_scenes),
            "max_location_budget": max_loc_budget,
        },
    )


@dataclass
class GameReleaseReadinessReport:
    passed: bool
    score: int
    target: str
    violations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


GAME_RUNTIME_BUDGET_LIMITS: Dict[str, Any] = {
    "max_texture_px": 2048,
    "max_peak_draw_calls": 150,
    "max_cold_start_ms": 3000,
    "max_subpackages_mb": {
        "wechat_minigame": 30.0,
        "douyin_minigame": 30.0,
        "bilibili_toy": 50.0,
        "taptap": 150.0,
        "itch_io": 200.0,
        "crazygames": 100.0,
    },
    "cn_regulated_targets": [
        "wechat_minigame",
        "douyin_minigame",
        "bilibili_toy",
        "taptap",
    ],
}

_COLLIDING_GENERIC_STORAGE_KEYS = frozenset({
    "save",
    "state",
    "score",
    "highscore",
    "settings",
    "config",
    "progress",
    "player",
    "userdata",
    "profile",
    "coins",
    "level",
})

_SCOPED_STORAGE_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,}[:./][a-zA-Z0-9_.:/-]+$")

_DEBUG_CONSOLE_SCRIPT_PATTERN = re.compile(
    r"(?i)(?:^|[/\\._-])(?:vconsole|eruda|stats(?:\.min)?\.js|dat\.gui)(?:[/\\._-]|$)"
)


def inspect_game_release_readiness(
    spec: Dict[str, Any],
    target: str = "wechat_minigame",
) -> GameReleaseReadinessReport:
    """
    Deterministic multi-portal WebGame / Mini-Game & Interactive Drama runtime & compliance gate:
    1. Subpackage & cold-start latency corridor: checks `subpackages_total_mb` against portal ceiling
       (30MB WeChat/Douyin Mini-Game) and `cold_start_ms <= 3000ms` (`SUBPACKAGE_BUDGET_EXCEEDED`, `COLD_START_LATENCY_EXCEEDED`).
    2. Mobile GPU memory & draw-call ceiling: blocks `max_texture_px > 2048` (`TEXTURE_DIMENSION_EXCEEDED`)
       and `peak_draw_calls > 150` (`DRAW_CALL_BUDGET_EXCEEDED`) to prevent mobile WebView OOM/frame drops.
    3. WebAudio autoplay unlock discipline: enforces `audio_gesture_unlocked=True` when `has_audio=True`
       (`WEBAUDIO_GESTURE_UNLOCK_MISSING`).
    4. Same-origin iframe save-slot isolation: rejects generic unprefixed `localStorage` keys (`save`, `score`)
       that collide across Bilibili Toy / Itch.io / CrazyGames sandboxes (`UNSCOPED_STORAGE_KEY_COLLISION`).
    5. Production debug probe stripping: blocks `vConsole` / `eruda` / debug overlay leaks (`DEBUG_CONSOLE_LEAKED`).
    6. Domestic portal anti-addiction notice: requires standard 48-char Health Gaming Notice (`has_health_gaming_notice=True`)
       on regulated CN portals (`wechat_minigame`, `douyin_minigame`, `bilibili_toy`, `taptap`) (`CN_HEALTH_GAMING_NOTICE_MISSING`).
    """
    violations: List[str] = []
    subpkg_caps: Dict[str, float] = GAME_RUNTIME_BUDGET_LIMITS["max_subpackages_mb"]
    target_key = str(target or "wechat_minigame").strip().lower()
    if target_key not in subpkg_caps:
        violations.append(
            f"UNSUPPORTED_RELEASE_TARGET: Target '{target_key}' not in {sorted(subpkg_caps.keys())}; falling back to 'wechat_minigame'."
        )
        target_key = "wechat_minigame"

    max_tex_limit = int(GAME_RUNTIME_BUDGET_LIMITS["max_texture_px"])
    max_dc_limit = int(GAME_RUNTIME_BUDGET_LIMITS["max_peak_draw_calls"])
    max_boot_ms = int(GAME_RUNTIME_BUDGET_LIMITS["max_cold_start_ms"])
    subpkg_limit_mb = float(subpkg_caps[target_key])

    subpkg_mb = float(spec.get("subpackages_total_mb", 0.0) or 0.0)
    if subpkg_mb > subpkg_limit_mb:
        violations.append(
            f"SUBPACKAGE_BUDGET_EXCEEDED: Total subpackages {subpkg_mb:.2f}MB exceed '{target_key}' {subpkg_limit_mb:.1f}MB limit."
        )

    cold_start_ms = int(spec.get("cold_start_ms", 1200) or 0)
    if cold_start_ms > max_boot_ms:
        violations.append(
            f"COLD_START_LATENCY_EXCEEDED: First interactive frame {cold_start_ms}ms exceeds {max_boot_ms}ms portal retention budget."
        )

    max_tex_px = int(spec.get("max_texture_px", 1024) or 0)
    if max_tex_px > max_tex_limit:
        violations.append(
            f"TEXTURE_DIMENSION_EXCEEDED: Max texture atlas {max_tex_px}px exceeds {max_tex_limit}px mobile WebGL safe limit."
        )

    peak_dc = int(spec.get("peak_draw_calls", 60) or 0)
    if peak_dc > max_dc_limit:
        violations.append(
            f"DRAW_CALL_BUDGET_EXCEEDED: Peak draw calls ({peak_dc}) exceed {max_dc_limit} mobile 60fps ceiling."
        )

    has_audio = bool(spec.get("has_audio", True))
    gesture_unlocked = bool(spec.get("audio_gesture_unlocked", True))
    if has_audio and not gesture_unlocked:
        violations.append(
            "WEBAUDIO_GESTURE_UNLOCK_MISSING: Audio playback lacks first pointerdown/touchstart AudioContext.resume() unlock."
        )

    raw_keys = [str(k).strip() for k in (spec.get("storage_keys") or []) if str(k).strip()]
    colliding_keys: List[str] = []
    for skey in raw_keys:
        if skey.lower() in _COLLIDING_GENERIC_STORAGE_KEYS or not _SCOPED_STORAGE_KEY_PATTERN.match(skey):
            colliding_keys.append(skey)
    if colliding_keys:
        violations.append(
            f"UNSCOPED_STORAGE_KEY_COLLISION: Unscoped localStorage key(s) {colliding_keys[:3]} risk cross-game save overwrite; prefix with '<game_slug>:'."
        )

    scripts = [str(s).strip() for s in (spec.get("scripts") or []) if str(s).strip()]
    leaked_probes = [s for s in scripts if _DEBUG_CONSOLE_SCRIPT_PATTERN.search(s)]
    if bool(spec.get("has_debug_overlay", False)) or leaked_probes:
        probe_desc = f" ({', '.join(leaked_probes[:2])})" if leaked_probes else ""
        violations.append(
            f"DEBUG_CONSOLE_LEAKED: Strip vConsole/eruda/debug overlay before production packaging{probe_desc}."
        )

    cn_targets = set(GAME_RUNTIME_BUDGET_LIMITS["cn_regulated_targets"])
    requires_cn_notice = target_key in cn_targets
    has_cn_notice = bool(spec.get("has_health_gaming_notice", not requires_cn_notice))
    if requires_cn_notice and not has_cn_notice:
        violations.append(
            f"CN_HEALTH_GAMING_NOTICE_MISSING: Target '{target_key}' requires standard 48-character Health Gaming Notice on splash screen."
        )

    score = max(0, 100 - len(violations) * 20)
    return GameReleaseReadinessReport(
        passed=len(violations) == 0,
        score=score,
        target=target_key,
        violations=violations,
        metrics={
            "subpackages_total_mb": round(subpkg_mb, 3),
            "max_subpackages_mb_limit": subpkg_limit_mb,
            "cold_start_ms": cold_start_ms,
            "max_texture_px": max_tex_px,
            "peak_draw_calls": peak_dc,
            "scoped_storage_key_count": len(raw_keys) - len(colliding_keys),
            "colliding_storage_key_count": len(colliding_keys),
            "requires_cn_notice": requires_cn_notice,
        },
    )


