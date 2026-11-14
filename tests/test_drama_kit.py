import unittest
from drama_kit import (
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
    standardize_shot_prompt,
    STUDIO_BGM_LIBRARY_PRESETS,
    DEFAULT_NEGATIVE_PROMPT,
    PLATFORM_SAFE_MARGINS,
)


class TestOpenShortDramaStudio(unittest.TestCase):
    def test_validate_episode_outline_passes_valid_episode(self):
        ep = {
            "beats": [
                {"type": "action", "is_hook": True, "desc": "Cold open sword clash"},
                {"type": "action", "is_hook": False, "desc": "Token revealed"},
            ] * 4,
            "dialogues": [
                {"speaker": "Hero", "text": "这枚令牌，你还认得吗？"},
                {"speaker": "Villain", "text": "不可能，当年你明明已经坠入深渊！"},
            ] * 3,
            "cliffhanger": "血色大阵骤然亮起，殿门轰然封死！",
        }
        report = validate_episode_outline(ep)
        self.assertTrue(report.passed)
        self.assertEqual(report.score, 100)
        self.assertEqual(report.violations, [])

    def test_validate_episode_outline_catches_missing_hook_and_long_dialogue(self):
        ep = {
            "beats": [{"type": "dialogue", "is_hook": False}],
            "dialogues": [{"speaker": "A", "text": "这句台词故意写得非常非常长超过三十五个字导致配音节奏严重拖沓无法通过短剧质检门禁"}],
            "cliffhanger": "完",
        }
        report = validate_episode_outline(ep)
        self.assertFalse(report.passed)
        self.assertGreaterEqual(len(report.violations), 3)

    def test_storyboard_budget_optimizer_saves_over_75_percent(self):
        shots = [
            {"id": "S1", "category": "vfx"},
            {"id": "S2", "category": "establishing"},
            {"id": "S3", "category": "close_up"},
            {"id": "S4", "category": "close_up"},
            {"id": "S5", "category": "standard"},
            {"id": "S6", "category": "climax"},
            {"id": "S7", "category": "climax"},
            {"id": "S8", "category": "climax"},  # 3rd climax downgraded by Layer-0 cap
        ]
        est = calculate_storyboard_budget(shots, max_pro_shots=2)
        self.assertEqual(est.total_shots, 8)
        self.assertEqual(est.tier_breakdown["sd_pro_climax"], 2)
        self.assertGreater(est.savings_ratio, 0.80)
        self.assertIn("lanczos", est.ffmpeg_upscale_filter)

    def test_export_capcut_timeline_manifest_microsecond_alignment(self):
        shots = [
            {"id": "S01", "duration_sec": 2.5, "speaker": "Hero", "dialogue": "来了！"},
            {"id": "S02", "duration_sec": 3.5, "dialogue": ""},
        ]
        manifest = export_capcut_timeline_manifest(shots)
        self.assertEqual(manifest["duration_us"], 6_000_000)
        self.assertEqual(len(manifest["tracks"]["video"]), 2)
        self.assertEqual(len(manifest["tracks"]["subtitles"]), 1)
        self.assertEqual(manifest["tracks"]["video"][1]["target_timerange"]["start"], 2_500_000)

    def test_inspect_webgame_bundle_catches_root_paths_and_cdn(self):
        bad_html = '<html><head></head><body><script src="https://unpkg.com/three.js"></script><img src="/assets/hero.png"></body></html>'
        rep = inspect_webgame_bundle(bad_html)
        self.assertFalse(rep.ready)
        self.assertEqual(len(rep.issues), 3)

        good_html = '<html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head><body><script src="./vendor/three.min.js"></script><img src="./assets/hero.png"></body></html>'
        rep_ok = inspect_webgame_bundle(good_html)
        self.assertTrue(rep_ok.ready)

    def test_inspect_audio_track_quality_passes_clean_stereo_with_bgm(self):
        audio_spec = {
            "has_audio": True,
            "channels": 2,
            "top5_sine_ratio": 0.05,
            "bgm_track": "ancient_suspense.wav",
            "has_speech": True,
            "speech_denoised": True,
            "sidechain_ducking": True,
        }
        rep = inspect_audio_track_quality(audio_spec)
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertIn("highpass=f=85", rep.recommended_ffmpeg_filter)
        self.assertIn("sidechaincompress", rep.recommended_ffmpeg_filter)
        self.assertIn("ancient_suspense", rep.studio_bgm_presets)

    def test_inspect_audio_track_quality_catches_synthetic_sine_buzzer(self):
        # Test ratio threshold breach
        bad_spec_ratio = {
            "has_audio": True,
            "channels": 2,
            "top5_sine_ratio": 0.58,
            "bgm_track": "epic_climax.wav",
        }
        rep1 = inspect_audio_track_quality(bad_spec_ratio)
        self.assertFalse(rep1.passed)
        self.assertTrue(any("SYNTHETIC_SINE_BUZZ_DETECTED" in v for v in rep1.violations))

        # Test command signature detection (e.g. sine=frequency=...)
        bad_spec_cmd = {
            "has_audio": True,
            "channels": 2,
            "pipeline_cmd": "ffmpeg -f lavfi -i sine=frequency=110:duration=60 -c:a aac out.aac",
            "bgm_track": "epic_climax.wav",
        }
        rep2 = inspect_audio_track_quality(bad_spec_cmd)
        self.assertFalse(rep2.passed)
        self.assertTrue(any("SYNTHETIC_SINE_BUZZ_DETECTED" in v for v in rep2.violations))

    def test_inspect_audio_track_quality_catches_mono_and_missing_bgm(self):
        bad_spec = {
            "has_audio": True,
            "channels": 1,
            "top5_sine_ratio": 0.02,
            "bgm_track": "",
            "has_speech": True,
            "speech_denoised": False,
            "sidechain_ducking": False,
        }
        rep = inspect_audio_track_quality(bad_spec)
        self.assertFalse(rep.passed)
        self.assertTrue(any("MONO_AUDIO_TRACK" in v for v in rep.violations))
        self.assertTrue(any("MISSING_STUDIO_BGM" in v for v in rep.violations))
        self.assertTrue(any("VOCAL_DENOISE_REQUIRED" in v for v in rep.violations))
        self.assertTrue(any("SIDECHAIN_DUCKING_REQUIRED" in v for v in rep.violations))

    def test_standardize_shot_prompt_passes_full_six_segments(self):
        spec = {
            "shot_type": "Close-up, fast tracking zoom",
            "subject_anchor": "Swordsman Lin in black cloak with scarred cheek",
            "action_beat": "eyes widening with fierce resolution",
            "environment_lighting": "rain-slick stone steps lit by flickering torchlight",
            "cinematic_style": "shot on 50mm prime, filmic grain, cold cyan grade",
            "negative_exclusions": "lowres, cartoon, distorted limbs",
        }
        rep = standardize_shot_prompt(spec, model_target="minimax_h3")
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertIn("Swordsman Lin", rep.prompt_en)
        self.assertIn("natural fluid movement", rep.prompt_en)
        self.assertIn("【主体锚点】", rep.prompt_zh)
        self.assertEqual(rep.negative_prompt, "lowres, cartoon, distorted limbs")

    def test_standardize_shot_prompt_catches_missing_segments_and_deducts_score(self):
        spec = {
            "shot_type": "",
            "subject_anchor": "",
        }
        rep = standardize_shot_prompt(spec, model_target="generic")
        self.assertFalse(rep.passed)
        self.assertLess(rep.score, 80)
        self.assertTrue(any("MISSING_SHOT_TYPE" in v for v in rep.violations))
        self.assertTrue(any("MISSING_SUBJECT_ANCHOR" in v for v in rep.violations))

    def test_standardize_shot_prompt_handles_raw_string_and_model_presets(self):
        raw_text = "Lin facing the demon beast in thunderstorm"
        rep_mj = standardize_shot_prompt(raw_text, model_target="midjourney")
        self.assertFalse(rep_mj.passed)
        self.assertIn("RAW_STRING_INPUT", rep_mj.violations[0])
        self.assertIn("--ar 16:9", rep_mj.prompt_en)
        self.assertEqual(rep_mj.negative_prompt, DEFAULT_NEGATIVE_PROMPT)



    def test_inspect_caption_safe_zone_passes_clean_captions_and_title(self):
        captions = [
            {"text": "三十年河东，今日这把剑归我了！", "y_ratio": 0.75, "x_right_ratio": 0.65},
            {"text": "你竟敢毁掉护宗大阵？", "y_ratio": 0.75, "x_right_ratio": 0.55},
        ]
        rep = inspect_caption_safe_zone(
            captions,
            platform="weixin_channels",
            title="【星途漫剧】第一集：剑破苍穹惊变",
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertEqual(rep.metrics["total_captions"], 2)
        self.assertEqual(rep.metrics["overflow_count"], 0)

    def test_inspect_caption_safe_zone_detects_overflows_and_generates_fixes(self):
        captions = [
            # Too long line (> 18 chars)
            {"text": "这句短剧对白故意写得极其漫长远远超过了单行十八个汉字的移动端显示极限", "y_ratio": 0.75, "x_right_ratio": 0.70},
            # Top overflow (status bar collision)
            {"text": "顶部状态栏警告字样", "y_ratio": 0.05, "x_right_ratio": 0.60},
            # Bottom overflow (progress scrubber collision)
            {"text": "底部进度条遮挡字样", "y_ratio": 0.92, "x_right_ratio": 0.60},
            # Right overflow (action buttons collision)
            {"text": "右侧点赞栏撞击", "y_ratio": 0.75, "x_right_ratio": 0.95},
        ]
        rep = inspect_caption_safe_zone(
            captions,
            platform="weixin_channels",
            title="【星途漫剧超长大标题】第三百二十四章：云端之巅神魔大战谁与争锋",
        )
        self.assertFalse(rep.passed)
        self.assertLessEqual(rep.score, 20)
        self.assertTrue(any("WEIXIN_TITLE_TOO_LONG" in v for v in rep.violations))
        self.assertTrue(any("CAPTION_LINE_TOO_LONG" in v for v in rep.violations))
        self.assertTrue(any("TOP_OVERFLOW" in v for v in rep.violations))
        self.assertTrue(any("BOTTOM_OVERFLOW" in v for v in rep.violations))
        self.assertTrue(any("RIGHT_OVERFLOW" in v for v in rep.violations))

        # Check fix suggestions
        fix_types = [f["type"] for f in rep.suggested_fixes]
        self.assertIn("truncate_title", fix_types)
        self.assertIn("split_caption", fix_types)
        self.assertIn("adjust_y", fix_types)

    def test_inspect_caption_safe_zone_platform_specific_margins(self):
        rep_dy = inspect_caption_safe_zone([], platform="douyin")
        self.assertEqual(rep_dy.metrics["safe_margins"]["bottom"], 0.80)

        rep_ks = inspect_caption_safe_zone([], platform="kuaishou")
        self.assertEqual(rep_ks.metrics["safe_margins"]["bottom"], 0.82)

    def test_inspect_social_cover_card_passes_valid_cover(self):
        cover = {
            "width": 1080,
            "height": 1440,
            "title": "剑破苍穹：逆天崛起",
            "title_y_ratio": 0.28,
            "has_ai_disclaimer": True,
        }
        rep = inspect_social_cover_card(cover, platform="xiaohongshu", ratio_type="3:4")
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertEqual(rep.metrics["ratio"], 0.75)

    def test_inspect_social_cover_card_detects_violations_and_fixes(self):
        cover = {
            "width": 400,
            "height": 400,
            "title": "这是一段非常冗长甚至超过了十四个汉字的短剧主标题",
            "title_y_ratio": 0.05,
            "has_ai_disclaimer": False,
        }
        rep = inspect_social_cover_card(cover, platform="xiaohongshu", ratio_type="3:4")
        self.assertFalse(rep.passed)
        self.assertTrue(any("RESOLUTION_TOO_LOW" in v for v in rep.violations))
        self.assertTrue(any("ASPECT_RATIO_MISMATCH" in v for v in rep.violations))
        self.assertTrue(any("TITLE_TOO_LONG" in v for v in rep.violations))
        self.assertTrue(any("TITLE_COLLIDES_HEADER" in v for v in rep.violations))
        self.assertTrue(any("AI_DISCLAIMER_MISSING" in v for v in rep.violations))

        fix_types = [f["type"] for f in rep.suggested_fixes]
        self.assertIn("upscale_recommendation", fix_types)
        self.assertIn("resize_aspect_ratio", fix_types)
        self.assertIn("truncate_headline", fix_types)
        self.assertIn("adjust_title_y", fix_types)
        self.assertIn("add_ai_disclaimer", fix_types)

    def test_inspect_social_cover_card_presets_and_platforms(self):
        rep_bili = inspect_social_cover_card(
            {"width": 1920, "height": 1080, "has_ai_disclaimer": True},
            platform="bilibili",
        )
        self.assertTrue(rep_bili.passed)
        self.assertEqual(rep_bili.metrics["target_preset"], "16:9")

        rep_toy = inspect_social_cover_card(
            {"width": 1024, "height": 1024, "has_ai_disclaimer": True},
            platform="bilibili_toy",
        )
        self.assertTrue(rep_toy.passed)
        self.assertEqual(rep_toy.metrics["target_preset"], "1:1")

        rep_vert = inspect_social_cover_card(
            {"width": 1080, "height": 1920, "has_ai_disclaimer": True},
            platform="weixin_channels",
        )
        self.assertTrue(rep_vert.passed)
        self.assertEqual(rep_vert.metrics["target_preset"], "9:16")

    def test_inspect_character_anchor_pack_passes_valid_star_topology(self):
        chars = [
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
        rep = inspect_character_anchor_pack(chars, referenced_speakers=["Lin", "Elder", "Narrator"])
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.stale_views, [])

    def test_inspect_character_anchor_pack_catches_stale_multihop_and_missing_speaker(self):
        chars = [
            {
                "id": "Lin",
                "tier": "lead",
                "anchor_hash": "sha256:lin_v3",
                "clean_background": False,
                "views": {
                    "frontal_full": {},
                    "closeup": {"source_anchor_hash": "sha256:lin_v2"},
                    "side_90": {"source_anchor_hash": "sha256:lin_v3", "chained_from": "closeup"},
                },
            }
        ]
        rep = inspect_character_anchor_pack(chars, referenced_speakers=["Lin", "MysteryBoss"])
        self.assertFalse(rep.passed)
        self.assertTrue(any("DIRTY_ANCHOR_BACKGROUND" in v for v in rep.violations))
        self.assertTrue(any("MISSING_REQUIRED_VIEW" in v for v in rep.violations))
        self.assertTrue(any("STALE_DERIVED_VIEW" in v for v in rep.violations))
        self.assertTrue(any("MULTI_HOP_DRIFT_RISK" in v for v in rep.violations))
        self.assertTrue(any("UNANCHORED_SCRIPT_SPEAKER" in v for v in rep.violations))
        self.assertEqual(len(rep.stale_views), 1)
        self.assertEqual(rep.stale_views[0]["view"], "closeup")

    def test_inspect_master_video_delivery_passes_clean_master(self):
        rep = inspect_master_video_delivery(
            {
                "pix_fmt": "yuv420p",
                "faststart_moov": True,
                "is_vfr": False,
                "fps": 30.0,
                "integrated_lufs": -14.2,
                "true_peak_dbtp": -1.5,
                "video_duration_sec": 62.5,
                "audio_duration_sec": 62.54,
                "leading_black_sec": 0.05,
            }
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertIn("+faststart", rep.ffmpeg_remaster_args)
        self.assertIn("loudnorm=I=-14.0", rep.ffmpeg_remaster_args)

    def test_inspect_master_video_delivery_catches_all_stream_and_loudness_traps(self):
        rep = inspect_master_video_delivery(
            {
                "pix_fmt": "yuv444p",
                "faststart_moov": False,
                "is_vfr": True,
                "fps": 24.0,
                "integrated_lufs": -21.0,
                "true_peak_dbtp": -0.2,
                "video_duration_sec": 45.0,
                "audio_duration_sec": 44.5,
                "leading_black_sec": 0.60,
            }
        )
        self.assertFalse(rep.passed)
        self.assertEqual(rep.score, 0)
        self.assertTrue(any("UNSUPPORTED_PIX_FMT" in v for v in rep.violations))
        self.assertTrue(any("MISSING_FASTSTART_MOOV" in v for v in rep.violations))
        self.assertTrue(any("VARIABLE_FRAME_RATE_DRIFT" in v for v in rep.violations))
        self.assertTrue(any("LOUDNESS_OUT_OF_TARGET" in v for v in rep.violations))
        self.assertTrue(any("TRUE_PEAK_CLIPPING_RISK" in v for v in rep.violations))
        self.assertTrue(any("AV_DURATION_DESYNC" in v for v in rep.violations))
        self.assertTrue(any("LEADING_BLACK_FRAME_TRAP" in v for v in rep.violations))
        self.assertIn("-ss 0.60", rep.ffmpeg_remaster_args)
        self.assertIn("-pix_fmt yuv420p", rep.ffmpeg_remaster_args)

    def test_inspect_multishot_segment_cuts_passes_aligned_h3_segment(self):
        rep = inspect_multishot_segment_cuts(
            {
                "cuts": [
                    {
                        "start_sec": 0.0,
                        "duration_sec": 3.5,
                        "keyframe_ref": "Pic1_Master",
                        "picture_refs": ["Pic1_Master", "Pic2_Env"],
                        "dialogue": "",
                    },
                    {
                        "start_sec": 3.5,
                        "duration_sec": 4.5,
                        "keyframe_ref": "Pic3_SubCut",
                        "picture_refs": ["Pic1_Master", "Pic3_SubCut"],
                        "dialogue": "三十年河东，今日这把剑归我了！",
                    },
                    {
                        "start_sec": 8.0,
                        "duration_sec": 4.0,
                        "keyframe_ref": "Pic4_Reaction",
                        "picture_refs": ["Pic4_Reaction"],
                        "dialogue": "你竟敢毁掉护宗大阵？",
                    },
                ]
            }
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertEqual(rep.metrics["total_duration_sec"], 12.0)
        self.assertEqual(rep.metrics["unique_picture_refs"], 4)
        self.assertIn("[Shot 1 @ 0.00s-3.50s | KF: Pic1_Master]", rep.alignment_header)

    def test_inspect_multishot_segment_cuts_catches_drift_overflow_and_lip_sync_overload(self):
        rep = inspect_multishot_segment_cuts(
            {
                "cuts": [
                    {
                        "start_sec": 0.5,
                        "duration_sec": 1.0,
                        "keyframe_ref": "",
                        "picture_refs": ["P1", "P2"],
                        "dialogue": "短短一秒塞入十几字台词必然嘴型崩坏",
                    },
                    {
                        "start_sec": 2.0,
                        "duration_sec": 7.5,
                        "keyframe_ref": "P3",
                        "picture_refs": ["P3", "P4", "P5"],
                        "dialogue": "",
                    },
                    {
                        "start_sec": 8.5,
                        "duration_sec": 7.0,
                        "keyframe_ref": "P6",
                        "picture_refs": ["P6"],
                        "dialogue": "",
                    },
                ]
            }
        )
        self.assertFalse(rep.passed)
        self.assertTrue(any("MASTER_KEYFRAME_NOT_AT_ZERO" in v for v in rep.violations))
        self.assertTrue(any("SHOT_CUT_TOO_SHORT" in v for v in rep.violations))
        self.assertTrue(any("DIALOGUE_PACING_OVERFLOW" in v for v in rep.violations))
        self.assertTrue(any("CUT_TIMESTAMP_DRIFT" in v for v in rep.violations))
        self.assertTrue(any("SHOT_CUT_STAGNANT_RISK" in v for v in rep.violations))
        self.assertTrue(any("SEGMENT_DURATION_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("REFERENCE_IMAGE_SLOT_OVERFLOW" in v for v in rep.violations))

    def test_inspect_webgame_archive_manifest_passes_clean_portal_zip(self):
        rep = inspect_webgame_archive_manifest(
            {
                "files": [
                    {"path": "index.html", "size_bytes": 16_384},
                    {"path": "assets/hero.png", "size_bytes": 512_000},
                    {"path": "audio/bgm_master.ogg", "size_bytes": 1_048_576},
                ],
                "referenced_assets": ["./assets/hero.png", "./audio/bgm_master.ogg"],
                "requires_threads": False,
            },
            portal="bilibili_toy",
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])

    def test_inspect_webgame_archive_manifest_catches_nested_leaks_case_and_sab_traps(self):
        rep = inspect_webgame_archive_manifest(
            {
                "files": [
                    {"path": "dist/index.html", "size_bytes": 20_000},
                    {"path": "assets\\hero.png", "size_bytes": 25 * 1024 * 1024},
                    {"path": "assets/bgm.ogg", "size_bytes": 30 * 1024 * 1024},
                    {"path": ".env.production", "size_bytes": 256},
                    {"path": "bundle.js.map", "size_bytes": 102_400},
                ],
                "referenced_assets": ["./assets/Hero.png", "./assets/missing_sfx.wav"],
                "requires_threads": True,
            },
            portal="bilibili_toy",
        )
        self.assertFalse(rep.passed)
        self.assertEqual(rep.score, 0)
        self.assertTrue(any("NESTED_ROOT_INDEX" in v for v in rep.violations))
        self.assertTrue(any("BACKSLASH_ZIP_ENTRY" in v for v in rep.violations))
        self.assertTrue(any("SENSITIVE_ARTIFACT_LEAK" in v for v in rep.violations))
        self.assertTrue(any("BUNDLE_SIZE_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("SINGLE_FILE_SIZE_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("CASE_MISMATCH_ASSET_REF" in v for v in rep.violations))
        self.assertTrue(any("MISSING_REFERENCED_ASSET" in v for v in rep.violations))
        self.assertTrue(any("SHARED_ARRAY_BUFFER_PORTAL_INCOMPATIBLE" in v for v in rep.violations))

    def test_inspect_webgame_archive_manifest_enforces_wechat_minigame_4mb_cap_and_entry(self):
        rep = inspect_webgame_archive_manifest(
            {
                "files": [
                    {"path": "index.html", "size_bytes": 10_000},
                    {"path": "pkg/main.wasm", "size_bytes": 5 * 1024 * 1024},
                ],
            },
            portal="wechat_minigame",
        )
        self.assertFalse(rep.passed)
        self.assertTrue(any("MISSING_ROOT_ENTRY" in v for v in rep.violations))
        self.assertTrue(any("BUNDLE_SIZE_EXCEEDED" in v for v in rep.violations))


if __name__ == "__main__":
    unittest.main()
