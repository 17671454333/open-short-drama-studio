"""CLI entrypoint for open-short-drama-studio (`python -m drama_kit`)."""
import argparse
import json
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
    inspect_multishot_segment_cuts,
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
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
