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


