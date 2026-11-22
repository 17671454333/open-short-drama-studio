"""CLI entrypoint for open-short-drama-studio (`python -m drama_kit`)."""
import argparse
import json
from .gates import (
    validate_episode_outline,
    calculate_storyboard_budget,
    export_capcut_timeline_manifest,
    inspect_webgame_bundle,
    inspect_webgame_archive_manifest,
    inspect_audio_track_quality,
    inspect_caption_safe_zone,
    inspect_social_cover_card,
    inspect_character_anchor_pack,
    inspect_master_video_delivery,
    inspect_multishot_segment_cuts,
    inspect_tts_subtitle_alignment,
    inspect_scene_staging_plan,
    inspect_scene_prop_bible,
    inspect_series_paywall_pacing,
    inspect_game_release_readiness,
    inspect_interactive_branch_graph,
    inspect_native_shell_package,
    inspect_localization_dubbing_pack,
)
from .storyboard_prompt import (
    standardize_shot_prompt,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Open Short-Drama & WebGame Studio CLI (Lite)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="Run end-to-end deterministic short-drama, prompt standardizer, audio gate & budget optimization demo")

    args = parser.parse_args()
    if args.cmd == "demo":
        sample_ep = {
            "beats": [
                {"type": "action", "is_hook": True, "desc": "Golden scale shatters in heavy rain"},
                {"type": "dialogue", "desc": "Confrontation at palace gate"},
            ],
            "dialogues": [
                {"speaker": "Lin", "text": "三十年河东，今日这把剑归我了！"},
                {"speaker": "Elder", "text": "你竟敢毁掉护宗大阵？"},
            ],
            "cliffhanger": "天幕裂开，万丈炎龙自云端俯冲而下！",
        }
        gate = validate_episode_outline(sample_ep)
        shots = [
            {"id": "S01", "category": "vfx", "duration_sec": 3.5, "dialogue": ""},
            {"id": "S02", "category": "climax", "duration_sec": 4.0, "speaker": "Lin", "dialogue": "三十年河东，今日这把剑归我了！"},
            {"id": "S03", "category": "close_up", "duration_sec": 3.0, "speaker": "Elder", "dialogue": "你竟敢毁掉护宗大阵？"},
            {"id": "S04", "category": "standard", "duration_sec": 3.5, "dialogue": ""},
        ]
        budget = calculate_storyboard_budget(shots)
        timeline = export_capcut_timeline_manifest(shots)
        sample_audio = {
            "has_audio": True,
            "channels": 2,
            "top5_sine_ratio": 0.08,
            "bgm_track": "ancient_suspense.wav",
            "has_speech": True,
            "speech_denoised": True,
            "sidechain_ducking": True,
        }
        audio_report = inspect_audio_track_quality(sample_audio)

        sample_shot_spec = {
            "shot_type": "Low-angle dramatic slow dolly in",
            "subject_anchor": "Young swordsman Lin wearing battle-torn obsidian armor with silver phoenix embroidery",
            "action_beat": "gripping ancient rune sword with right hand, eyes burning with determined wrath",
            "environment_lighting": "ruined cliff fortress under stormy dusk sky, lightning illuminating flying ash and rain",
            "cinematic_style": "shot on 35mm anamorphic lens, shallow depth of field, photorealistic 8k, moody teal and gold color grade",
        }
        prompt_report = standardize_shot_prompt(sample_shot_spec, model_target="minimax_h3")

        sample_captions = [
            {"text": "三十年河东，今日这把剑归我了！", "y_ratio": 0.75, "x_right_ratio": 0.65},
            {"text": "你竟敢毁掉护宗大阵？", "y_ratio": 0.75, "x_right_ratio": 0.55},
        ]
        safe_zone_report = inspect_caption_safe_zone(
            sample_captions,
            platform="weixin_channels",
            title="【星途漫剧】第一集：剑破苍穹惊变",
        )

        sample_cover = {
            "width": 1080,
            "height": 1440,
            "title": "剑破苍穹：逆天崛起",
            "title_y_ratio": 0.28,
            "has_ai_disclaimer": True,
        }
        cover_report = inspect_social_cover_card(
            sample_cover,
            platform="xiaohongshu",
            ratio_type="3:4",
        )

        sample_characters = [
            {
                "id": "Lin",
                "tier": "lead",
                "anchor_hash": "sha256:lin_v2",
                "clean_background": True,
                "views": {
                    "frontal_full": {},
                    "closeup": {"source_anchor_hash": "sha256:lin_v2"},
                    "side_90": {"source_anchor_hash": "sha256:lin_v2"},
                    "back": {"source_anchor_hash": "sha256:lin_v2"},
                },
            },
            {
                "id": "Elder",
                "tier": "supporting",
                "anchor_hash": "sha256:elder_v1",
                "clean_background": True,
                "views": {
                    "frontal_full": {},
                    "closeup": {"source_anchor_hash": "sha256:elder_v1"},
                },
            },
        ]
        anchor_report = inspect_character_anchor_pack(sample_characters, referenced_speakers=["Lin", "Elder"])
        master_report = inspect_master_video_delivery(
            {
                "pix_fmt": "yuv420p",
                "faststart_moov": True,
                "is_vfr": False,
                "fps": 30.0,
                "integrated_lufs": -14.1,
                "true_peak_dbtp": -1.5,
                "video_duration_sec": 14.0,
                "audio_duration_sec": 14.02,
                "leading_black_sec": 0.0,
            }
        )
        segment_report = inspect_multishot_segment_cuts(
            {
                "cuts": [
                    {
                        "start_sec": 0.0,
                        "duration_sec": 3.5,
                        "keyframe_ref": "Picture_1_Lin_Master",
                        "picture_refs": ["Picture_1_Lin_Master", "Picture_2_Cliff_Scene"],
                        "dialogue": "",
                    },
                    {
                        "start_sec": 3.5,
                        "duration_sec": 4.5,
                        "keyframe_ref": "Picture_3_Lin_Closeup",
                        "picture_refs": ["Picture_1_Lin_Master", "Picture_3_Lin_Closeup"],
                        "dialogue": "三十年河东，今日这把剑归我了！",
                    },
                    {
                        "start_sec": 8.0,
                        "duration_sec": 4.0,
                        "keyframe_ref": "Picture_4_Elder_Reaction",
                        "picture_refs": ["Picture_4_Elder_Reaction"],
                        "dialogue": "你竟敢毁掉护宗大阵？",
                    },
                ]
            }
        )

        archive_report = inspect_webgame_archive_manifest(
            {
                "files": [
                    {"path": "index.html", "size_bytes": 18_432},
                    {"path": "assets/hero.png", "size_bytes": 420_000},
                    {"path": "audio/bgm_loop.ogg", "size_bytes": 1_250_000},
                    {"path": "vendor/phaser.min.js", "size_bytes": 980_000},
                ],
                "referenced_assets": ["./assets/hero.png", "./audio/bgm_loop.ogg", "./vendor/phaser.min.js"],
                "requires_threads": False,
            },
            portal="bilibili_toy",
        )

        subtitle_align_report = inspect_tts_subtitle_alignment(
            {
                "has_burned_in_subtitles": False,
                "cues": [
                    {
                        "start_sec": 3.50,
                        "end_sec": 7.80,
                        "tts_start_sec": 3.52,
                        "tts_end_sec": 7.76,
                        "text": "三十年河东，今日这把剑归我了！",
                    },
                    {
                        "start_sec": 8.00,
                        "end_sec": 11.60,
                        "tts_start_sec": 8.04,
                        "tts_end_sec": 11.55,
                        "text": "你竟敢毁掉护宗大阵？",
                    },
                ],
            }
        )

        staging_report = inspect_scene_staging_plan(
            {
                "anchors": [
                    {"id": "altar_sword_pedestal", "x": 0.50, "y": 0.48},
                    {"id": "fortress_pillared_gate", "x": 0.50, "y": 0.24},
                ],
                "placements": [
                    {
                        "character": "Lin",
                        "anchor_id": "altar_sword_pedestal",
                        "side": "south",
                        "posture": "standing",
                        "facing": "north",
                    },
                    {
                        "character": "Elder",
                        "anchor_id": "fortress_pillared_gate",
                        "side": "south",
                        "posture": "standing",
                        "facing": "south",
                    },
                ],
                "camera_axis_locked": True,
                "extras_count": 4,
                "extras_zone": "outer cliff stairway perimeter",
            },
            expected_characters=["Lin", "Elder"],
        )

        art_bible_report = inspect_scene_prop_bible(
            {
                "scenes": [
                    {
                        "id": "cliff_fortress",
                        "visual_anchors": [
                            "broken obsidian sword altar",
                            "twin dragon stone pillars",
                            "iron chain suspension bridge",
                            "jagged basalt cliff edge",
                        ],
                        "empty_plate_prompt": "Wide architectural establishing shot of ruined cliffside obsidian fortress, twin dragon stone pillars, broken sword altar, uninhabited, no people, cinematic 8k",
                        "lighting_variants": {
                            "stormy_dusk": "dark storm clouds, lightning rim light, wet basalt reflections",
                            "blood_moon": "crimson moonlight through fog, cold cyan shadows",
                        },
                    }
                ],
                "props": [
                    {
                        "id": "ancient_rune_sword",
                        "prompt": "Ancient obsidian broadsword etched with glowing silver phoenix runes, no hands, unheld, isolated on pure white background, studio product lighting",
                        "scale_cm": 118.0,
                        "state_variants": {
                            "intact": "blade gleaming with unbroken silver rune circuit",
                            "shattered": "cracked obsidian blade with fractured glowing shards",
                        },
                    }
                ],
            },
            required_scene_usages=[{"scene_id": "cliff_fortress", "lighting": "stormy_dusk"}],
            required_prop_usages=[{"prop_id": "ancient_rune_sword", "state": "intact"}],
        )

        series_pacing_report = inspect_series_paywall_pacing(
            {
                "target_episode_sec": 90.0,
                "paywall_episode": 6,
                "lead_characters": ["Lin", "Elder"],
                "primary_scenes": ["cliff_fortress", "imperial_study", "sect_arena"],
                "episodes": [
                    {"ep": 1, "has_payoff": True, "cliffhanger_grade": 8.5, "duration_sec": 88.0},
                    {"ep": 2, "has_payoff": False, "cliffhanger_grade": 7.5, "duration_sec": 92.0},
                    {"ep": 3, "has_payoff": True, "cliffhanger_grade": 8.0, "duration_sec": 85.0},
                    {"ep": 4, "has_payoff": False, "cliffhanger_grade": 7.2, "duration_sec": 90.0},
                    {"ep": 5, "has_payoff": True, "cliffhanger_grade": 8.4, "duration_sec": 94.0},
                    {"ep": 6, "has_payoff": False, "cliffhanger_grade": 9.2, "duration_sec": 96.0, "is_paywall": True},
                ],
            }
        )

        game_readiness_report = inspect_game_release_readiness(
            {
                "subpackages_total_mb": 14.5,
                "cold_start_ms": 1450,
                "max_texture_px": 2048,
                "peak_draw_calls": 82,
                "has_audio": True,
                "audio_gesture_unlocked": True,
                "storage_keys": ["sword_sect:save_v1", "sword_sect:audio_prefs"],
                "scripts": ["js/bundle.min.js", "js/runtime.js"],
                "has_debug_overlay": False,
                "has_health_gaming_notice": True,
            },
            target="wechat_minigame",
        )

        interactive_branch_report = inspect_interactive_branch_graph(
            {
                "entry_node": "N01_Cliff_Confrontation",
                "nodes": [
                    {
                        "id": "N01_Cliff_Confrontation",
                        "timer_sec": 8.0,
                        "preload_targets": ["N02_Draw_Sword", "N03_Seal_Array"],
                        "choices": [
                            {"label": "拔剑强破护宗大阵", "target": "N02_Draw_Sword", "is_default": True},
                            {"label": "催动玄冰印反客为主", "target": "N03_Seal_Array"},
                        ],
                    },
                    {
                        "id": "N02_Draw_Sword",
                        "is_ending": True,
                    },
                    {
                        "id": "N03_Seal_Array",
                        "is_ending": True,
                    },
                ],
            }
        )

        native_shell_report = inspect_native_shell_package(
            {
                "app_id": "studio.xingtu.sword_sect_fmv",
                "signed": True,
                "debuggable": False,
                "keystore_type": "release",
                "devtools_enabled": False,
                "target_sdk": 35,
                "abis": ["arm64-v8a"],
                "permissions": ["INTERNET", "VIBRATE"],
                "icon_px": 512,
                "package_mb": 128.5,
            },
            platform="android_apk",
        )

        localization_report = inspect_localization_dubbing_pack(
            {
                "font_locales": ["en-US", "es-ES"],
                "glossary": {"林玄": "Lin Xuan", "护宗大阵": "Guardian Array"},
                "entries": [
                    {
                        "id": "D01",
                        "source": "林玄，这把剑归你了！",
                        "target": "Lin Xuan, this blade is yours now!",
                        "slot_duration_sec": 2.8,
                    },
                    {
                        "id": "UI01",
                        "source": "第 {ep} 集：击破护宗大阵",
                        "target": "Ep {ep}: Shatter the Guardian Array",
                        "slot_duration_sec": 0.0,
                    },
                ],
            },
            target_locale="en-US",
        )

        print(
            json.dumps(
                {
                    "outline_gate": gate.__dict__,
                    "budget_optimizer": budget.__dict__,
                    "capcut_timeline_summary": {
                        "duration_sec": timeline["duration_sec"],
                        "video_clips": len(timeline["tracks"]["video"]),
                        "subtitles": len(timeline["tracks"]["subtitles"]),
                    },
                    "audio_gate": {
                        "passed": audio_report.passed,
                        "score": audio_report.score,
                        "violations": audio_report.violations,
                        "metrics": audio_report.metrics,
                    },
                    "storyboard_prompt_standardizer": {
                        "passed": prompt_report.passed,
                        "score": prompt_report.score,
                        "violations": prompt_report.violations,
                        "model_target": prompt_report.model_target,
                        "prompt_en": prompt_report.prompt_en,
                        "prompt_zh": prompt_report.prompt_zh,
                    },
                    "caption_safe_zone_gate": {
                        "passed": safe_zone_report.passed,
                        "score": safe_zone_report.score,
                        "violations": safe_zone_report.violations,
                        "platform": safe_zone_report.platform,
                        "metrics": safe_zone_report.metrics,
                    },
                    "social_cover_gate": {
                        "passed": cover_report.passed,
                        "score": cover_report.score,
                        "violations": cover_report.violations,
                        "platform": cover_report.platform,
                        "metrics": cover_report.metrics,
                    },
                    "character_anchor_gate": {
                        "passed": anchor_report.passed,
                        "score": anchor_report.score,
                        "violations": anchor_report.violations,
                        "metrics": anchor_report.metrics,
                    },
                    "master_delivery_gate": {
                        "passed": master_report.passed,
                        "score": master_report.score,
                        "violations": master_report.violations,
                        "metrics": master_report.metrics,
                    },
                    "multishot_segment_gate": {
                        "passed": segment_report.passed,
                        "score": segment_report.score,
                        "violations": segment_report.violations,
                        "metrics": segment_report.metrics,
                        "alignment_header": segment_report.alignment_header,
                    },
                    "webgame_archive_gate": {
                        "passed": archive_report.passed,
                        "score": archive_report.score,
                        "portal": archive_report.portal,
                        "violations": archive_report.violations,
                        "metrics": archive_report.metrics,
                    },
                    "tts_subtitle_alignment_gate": {
                        "passed": subtitle_align_report.passed,
                        "score": subtitle_align_report.score,
                        "violations": subtitle_align_report.violations,
                        "metrics": subtitle_align_report.metrics,
                    },
                    "scene_staging_gate": {
                        "passed": staging_report.passed,
                        "score": staging_report.score,
                        "violations": staging_report.violations,
                        "metrics": staging_report.metrics,
                        "opening_blocking_line": staging_report.opening_blocking_line,
                    },
                    "scene_prop_bible_gate": {
                        "passed": art_bible_report.passed,
                        "score": art_bible_report.score,
                        "violations": art_bible_report.violations,
                        "metrics": art_bible_report.metrics,
                    },
                    "series_paywall_pacing_gate": {
                        "passed": series_pacing_report.passed,
                        "score": series_pacing_report.score,
                        "violations": series_pacing_report.violations,
                        "metrics": series_pacing_report.metrics,
                    },
                    "game_release_readiness_gate": {
                        "passed": game_readiness_report.passed,
                        "score": game_readiness_report.score,
                        "target": game_readiness_report.target,
                        "violations": game_readiness_report.violations,
                        "metrics": game_readiness_report.metrics,
                    },
                    "interactive_branch_gate": {
                        "passed": interactive_branch_report.passed,
                        "score": interactive_branch_report.score,
                        "violations": interactive_branch_report.violations,
                        "metrics": interactive_branch_report.metrics,
                    },
                    "native_shell_package_gate": {
                        "passed": native_shell_report.passed,
                        "score": native_shell_report.score,
                        "platform": native_shell_report.platform,
                        "violations": native_shell_report.violations,
                        "metrics": native_shell_report.metrics,
                    },
                    "localization_dubbing_gate": {
                        "passed": localization_report.passed,
                        "score": localization_report.score,
                        "locale": localization_report.locale,
                        "violations": localization_report.violations,
                        "metrics": localization_report.metrics,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
