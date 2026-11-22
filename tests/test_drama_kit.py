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
    inspect_tts_subtitle_alignment,
    inspect_scene_staging_plan,
    inspect_scene_prop_bible,
    inspect_series_paywall_pacing,
    inspect_game_release_readiness,
    inspect_interactive_branch_graph,
    inspect_native_shell_package,
    inspect_localization_dubbing_pack,
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

    def test_inspect_tts_subtitle_alignment_passes_clean_synced_cues(self):
        rep = inspect_tts_subtitle_alignment(
            {
                "has_burned_in_subtitles": False,
                "cues": [
                    {
                        "start_sec": 1.00,
                        "end_sec": 3.80,
                        "tts_start_sec": 1.05,
                        "tts_end_sec": 3.72,
                        "text": "三十年河东，今日这把剑归我了！",
                    },
                    {
                        "start_sec": 4.00,
                        "end_sec": 6.50,
                        "tts_start_sec": 4.02,
                        "tts_end_sec": 6.46,
                        "text": "你竟敢毁掉护宗大阵？",
                    },
                ],
            }
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertEqual(len(rep.cleaned_cues), 2)

    def test_inspect_tts_subtitle_alignment_catches_burned_overlap_flash_drift_and_punct(self):
        rep = inspect_tts_subtitle_alignment(
            {
                "has_burned_in_subtitles": True,
                "crop_or_inpaint_applied": False,
                "cues": [
                    {
                        "start_sec": 0.00,
                        "end_sec": 0.25,
                        "tts_start_sec": 0.00,
                        "tts_end_sec": 0.90,
                        "text": "短短零点二秒塞入超多字且末尾带句号。",
                    },
                    {
                        "start_sec": 0.15,
                        "end_sec": 2.00,
                        "tts_start_sec": 0.20,
                        "tts_end_sec": 1.98,
                        "text": "正常第二句",
                    },
                ],
            }
        )
        self.assertFalse(rep.passed)
        self.assertEqual(rep.score, 0)
        self.assertTrue(any("BURNED_IN_SUBTITLE_CONFLICT" in v for v in rep.violations))
        self.assertTrue(any("SUBTITLE_FLASH_TOO_BRIEF" in v for v in rep.violations))
        self.assertTrue(any("TTS_AUDIO_SYNC_DRIFT" in v for v in rep.violations))
        self.assertTrue(any("TRAILING_PUNCTUATION_CLUTTER" in v for v in rep.violations))
        self.assertTrue(any("SUBTITLE_CPS_OVERLOAD" in v for v in rep.violations))
        self.assertTrue(any("SUBTITLE_CUE_OVERLAP" in v for v in rep.violations))
        self.assertEqual(rep.cleaned_cues[0]["text"], "短短零点二秒塞入超多字且末尾带句号")
        self.assertGreaterEqual(rep.cleaned_cues[1]["start_sec"], 0.25)

    def test_inspect_scene_staging_plan_passes_clean_blocking(self):
        rep = inspect_scene_staging_plan(
            {
                "anchors": [
                    {"id": "jade_tea_table", "x": 0.50, "y": 0.52},
                    {"id": "palace_pillar", "x": 0.28, "y": 0.30},
                ],
                "placements": [
                    {
                        "character": "Lin",
                        "anchor_id": "jade_tea_table",
                        "side": "south",
                        "posture": "seated",
                        "facing": "north",
                    },
                    {
                        "character": "Elder",
                        "anchor_id": "jade_tea_table",
                        "side": "north",
                        "posture": "standing",
                        "facing": "south",
                    },
                ],
                "camera_axis_locked": True,
                "extras_count": 3,
                "extras_zone": "rear courtyard colonnade",
            },
            expected_characters=["Lin", "Elder"],
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertIn("Opening blocking: Lin seated at south side of jade_tea_table facing north", rep.opening_blocking_line)
        self.assertIn("(extras: 3 in rear courtyard colonnade).", rep.opening_blocking_line)

    def test_inspect_scene_staging_plan_catches_collision_axis_crowding_and_cast_mismatch(self):
        rep = inspect_scene_staging_plan(
            {
                "anchors": [
                    {"id": "throne_desk", "x": 0.50, "y": 0.50},
                    {"id": "side_brazier", "x": 0.53, "y": 0.50},
                    {"id": "edge_window", "x": 0.99, "y": 0.02},
                ],
                "placements": [
                    {
                        "character": "Lin",
                        "anchor_id": "throne_desk",
                        "side": "south",
                        "posture": "standing",
                        "facing": "north",
                    },
                    {
                        "character": "GhostExtra",
                        "anchor_id": "throne_desk",
                        "side": "south",
                        "posture": "standing",
                        "facing": "north",
                    },
                    {
                        "character": "Guard",
                        "anchor_id": "side_brazier",
                        "side": "south",
                        "posture": "kneeling",
                        "facing": "west",
                    },
                ],
                "camera_axis_locked": False,
                "extras_count": 6,
                "extras_zone": "",
            },
            expected_characters=["Lin", "Elder", "Guard"],
        )
        self.assertFalse(rep.passed)
        self.assertTrue(any("ANCHOR_OUT_OF_BOUNDS" in v for v in rep.violations))
        self.assertTrue(any("SAME_SIDE_COLLISION" in v for v in rep.violations))
        self.assertTrue(any("PROXIMITY_CROWDING_RISK" in v for v in rep.violations))
        self.assertTrue(any("MISSING_SCRIPT_CHARACTER" in v for v in rep.violations))
        self.assertTrue(any("UNDECLARED_BLOCKING_CHARACTER" in v for v in rep.violations))
        self.assertTrue(any("CAMERA_AXIS_CROSSING_RISK" in v for v in rep.violations))
        self.assertTrue(any("EXTRAS_ZONE_UNSPECIFIED" in v for v in rep.violations))

    def test_inspect_scene_prop_bible_passes_clean_empty_plate_and_isolated_prop(self):
        rep = inspect_scene_prop_bible(
            {
                "scenes": [
                    {
                        "id": "imperial_study",
                        "visual_anchors": [
                            "carved rosewood desk",
                            "bronze crane incense burner",
                            "lattice moon window",
                            "hanging calligraphy scroll",
                        ],
                        "empty_plate_prompt": "Interior architectural wide shot of classical imperial study, bronze incense burner, rosewood desk, uninhabited, no people, 8k photorealistic",
                        "lighting_variants": {
                            "candle_night": "warm flickering candlelight with deep indigo window shadows",
                            "morning_mist": "soft diffused cool daylight through paper lattice",
                        },
                    }
                ],
                "props": [
                    {
                        "id": "tiger_tally_seal",
                        "prompt": "Ancient split bronze tiger tally military seal with patina, no hands, unheld, isolated on pure white background",
                        "scale_cm": 9.5,
                        "state_variants": {
                            "left_half": "single left half of split bronze tiger seal",
                            "reunited": "interlocked full bronze tiger tally glowing gold",
                        },
                    }
                ],
            },
            required_scene_usages=[{"scene_id": "imperial_study", "lighting": "candle_night"}],
            required_prop_usages=[{"prop_id": "tiger_tally_seal", "state": "left_half"}],
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertEqual(rep.metrics["scene_count"], 1)
        self.assertEqual(rep.metrics["prop_count"], 1)

    def test_inspect_scene_prop_bible_catches_actor_hand_scale_and_variant_traps(self):
        rep = inspect_scene_prop_bible(
            {
                "scenes": [
                    {
                        "id": "market_street",
                        "visual_anchors": ["red lantern"],
                        "empty_plate_prompt": "Busy ancient street with crowd of villagers and guards walking",
                        "lighting_variants": {"day": "bright sunlight"},
                    }
                ],
                "props": [
                    {
                        "id": "jade_pendant",
                        "prompt": "Close-up of warrior hand holding glowing green jade pendant over dark stone table",
                        "scale_cm": 0.0,
                        "state_variants": ["intact"],
                    }
                ],
            },
            required_scene_usages=[
                {"scene_id": "market_street", "lighting": "midnight_rain"},
                {"scene_id": "missing_palace", "lighting": "day"},
            ],
            required_prop_usages=[
                {"prop_id": "jade_pendant", "state": "cracked"},
                {"prop_id": "missing_dagger", "state": "bloodied"},
            ],
        )
        self.assertFalse(rep.passed)
        self.assertEqual(rep.score, 0)
        self.assertTrue(any("SCENE_ANCHOR_BUDGET_OUT_OF_RANGE" in v for v in rep.violations))
        self.assertTrue(any("SCENE_EMPTY_PLATE_ACTOR_CONTAMINATION" in v for v in rep.violations))
        self.assertTrue(any("PROP_HAND_CONTAMINATION" in v for v in rep.violations))
        self.assertTrue(any("PROP_NON_ISOLATED_BACKGROUND" in v for v in rep.violations))
        self.assertTrue(any("PROP_SCALE_REFERENCE_INVALID" in v for v in rep.violations))
        self.assertTrue(any("MISSING_SCENE_LIGHTING_VARIANT" in v for v in rep.violations))
        self.assertTrue(any("UNDECLARED_SCRIPT_SCENE" in v for v in rep.violations))
        self.assertTrue(any("MISSING_PROP_STATE_VARIANT" in v for v in rep.violations))
        self.assertTrue(any("UNDECLARED_SCRIPT_PROP" in v for v in rep.violations))

    def test_inspect_series_paywall_pacing_passes_well_paced_arc(self):
        rep = inspect_series_paywall_pacing(
            {
                "target_episode_sec": 90.0,
                "paywall_episode": 6,
                "lead_characters": ["Lin", "Su", "Elder"],
                "primary_scenes": ["cliff_fortress", "imperial_study", "jade_pavilion"],
                "episodes": [
                    {"ep": 1, "payoff_score": 8.5, "cliffhanger_grade": 8.5, "duration_sec": 86.0},
                    {"ep": 2, "has_payoff": False, "cliffhanger_grade": 7.5, "duration_sec": 90.0},
                    {"ep": 3, "has_payoff": True, "cliffhanger_grade": 8.2, "duration_sec": 95.0},
                    {"ep": 4, "has_payoff": False, "cliffhanger_grade": 7.2, "duration_sec": 88.0},
                    {"ep": 5, "has_payoff": True, "cliffhanger_grade": 8.6, "duration_sec": 92.0},
                    {"ep": 6, "has_payoff": False, "cliffhanger_grade": 9.4, "duration_sec": 98.0, "is_paywall": True},
                ],
            }
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertEqual(rep.metrics["episode_count"], 6)
        self.assertEqual(rep.metrics["payoff_count"], 3)
        self.assertEqual(rep.metrics["max_payoff_gap"], 1)

    def test_inspect_series_paywall_pacing_catches_drought_paywall_duration_and_budget_traps(self):
        rep = inspect_series_paywall_pacing(
            {
                "target_episode_sec": 90.0,
                "lead_characters": ["Lin", "Su", "Elder", "Prince"],
                "primary_scenes": ["s1", "s2", "s3", "s4", "s5", "s6"],
                "episodes": [
                    {"ep": 1, "has_payoff": False, "cliffhanger_grade": 6.0, "duration_sec": 42.0},
                    {"ep": 2, "has_payoff": False, "cliffhanger_grade": 5.5, "duration_sec": 88.0},
                    {"ep": 3, "has_payoff": False, "cliffhanger_grade": 6.0, "duration_sec": 90.0},
                    {"ep": 4, "has_payoff": False, "cliffhanger_grade": 5.0, "duration_sec": 90.0},
                    {
                        "ep": 5,
                        "has_payoff": True,
                        "cliffhanger_grade": 6.5,
                        "duration_sec": 90.0,
                        "is_paywall": True,
                        "premature_resolution": True,
                    },
                ],
            }
        )
        self.assertFalse(rep.passed)
        self.assertEqual(rep.score, 0)
        self.assertTrue(any("GOLDEN_OPENING_PAYOFF_MISSING" in v for v in rep.violations))
        self.assertTrue(any("PAYOFF_DROUGHT_GAP_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("EPISODE_DURATION_OUT_OF_CORRIDOR" in v for v in rep.violations))
        self.assertTrue(any("PAYWALL_EPISODE_WEAK_HOOK" in v for v in rep.violations))
        self.assertTrue(any("PAYWALL_PREMATURE_RESOLUTION" in v for v in rep.violations))
        self.assertTrue(any("PAYWALL_MISSING_PRE_ESCALATION" in v for v in rep.violations))
        self.assertTrue(any("LEAD_CAST_BUDGET_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("MAIN_LOCATION_BUDGET_EXCEEDED" in v for v in rep.violations))

    def test_inspect_game_release_readiness_passes_compliant_wechat_and_itch_builds(self):
        rep_wx = inspect_game_release_readiness(
            {
                "subpackages_total_mb": 18.2,
                "cold_start_ms": 1650,
                "max_texture_px": 2048,
                "peak_draw_calls": 95,
                "has_audio": True,
                "audio_gesture_unlocked": True,
                "storage_keys": ["blade_chronicle:slot_1", "blade_chronicle:settings"],
                "scripts": ["js/game.min.js"],
                "has_debug_overlay": False,
                "has_health_gaming_notice": True,
            },
            target="wechat_minigame",
        )
        self.assertTrue(rep_wx.passed)
        self.assertEqual(rep_wx.score, 100)
        self.assertEqual(rep_wx.violations, [])
        self.assertTrue(rep_wx.metrics["requires_cn_notice"])

        rep_itch = inspect_game_release_readiness(
            {
                "subpackages_total_mb": 64.0,
                "cold_start_ms": 2100,
                "max_texture_px": 2048,
                "peak_draw_calls": 110,
                "has_audio": True,
                "audio_gesture_unlocked": True,
                "storage_keys": ["cyber_noir:save_v2"],
                "scripts": ["dist/index.js"],
            },
            target="itch_io",
        )
        self.assertTrue(rep_itch.passed)
        self.assertEqual(rep_itch.score, 100)
        self.assertFalse(rep_itch.metrics["requires_cn_notice"])

    def test_inspect_game_release_readiness_catches_gpu_audio_save_debug_and_compliance_traps(self):
        rep = inspect_game_release_readiness(
            {
                "subpackages_total_mb": 42.5,
                "cold_start_ms": 4800,
                "max_texture_px": 4096,
                "peak_draw_calls": 260,
                "has_audio": True,
                "audio_gesture_unlocked": False,
                "storage_keys": ["save", "ab:slot"],
                "scripts": ["vendor/vconsole.min.js", "js/main.js"],
                "has_debug_overlay": True,
                "has_health_gaming_notice": False,
            },
            target="wechat_minigame",
        )
        self.assertFalse(rep.passed)
        self.assertEqual(rep.score, 0)
        self.assertTrue(any("SUBPACKAGE_BUDGET_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("COLD_START_LATENCY_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("TEXTURE_DIMENSION_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("DRAW_CALL_BUDGET_EXCEEDED" in v for v in rep.violations))
        self.assertTrue(any("WEBAUDIO_GESTURE_UNLOCK_MISSING" in v for v in rep.violations))
        self.assertTrue(any("UNSCOPED_STORAGE_KEY_COLLISION" in v for v in rep.violations))
        self.assertTrue(any("DEBUG_CONSOLE_LEAKED" in v for v in rep.violations))
        self.assertTrue(any("CN_HEALTH_GAMING_NOTICE_MISSING" in v for v in rep.violations))

    def test_inspect_interactive_branch_graph_passes_clean_diamond_dag(self):
        rep = inspect_interactive_branch_graph(
            {
                "entry_node": "N01_Intro",
                "nodes": [
                    {
                        "id": "N01_Intro",
                        "timer_sec": 7.5,
                        "preload_targets": ["N02_Stealth", "N03_Duel"],
                        "choices": [
                            {"label": "潜入藏经阁", "target": "N02_Stealth", "is_default": True},
                            {"label": "正面迎战长老", "target": "N03_Duel"},
                        ],
                    },
                    {
                        "id": "N02_Stealth",
                        "preload_targets": ["N04_True_End", "N05_Bad_End"],
                        "choices": [
                            {"label": "开启禁制石匣", "target": "N04_True_End"},
                            {"label": "原路撤离", "target": "N05_Bad_End"},
                        ],
                    },
                    {
                        "id": "N03_Duel",
                        "auto_advance": True,
                        "preload_targets": ["N04_True_End"],
                        "choices": [
                            {"label": "剑意觉醒", "target": "N04_True_End"},
                        ],
                    },
                    {"id": "N04_True_End", "is_ending": True},
                    {"id": "N05_Bad_End", "is_ending": True},
                ],
            }
        )
        self.assertTrue(rep.passed)
        self.assertEqual(rep.score, 100)
        self.assertEqual(rep.violations, [])
        self.assertEqual(rep.metrics["node_count"], 5)
        self.assertEqual(rep.metrics["reachable_count"], 5)
        self.assertEqual(rep.metrics["ending_count"], 2)
        self.assertEqual(rep.metrics["orphan_count"], 0)
        self.assertEqual(rep.metrics["trap_node_count"], 0)

    def test_inspect_interactive_branch_graph_catches_orphan_trap_dangling_timer_and_preload(self):
        rep = inspect_interactive_branch_graph(
            {
                "entry_node": "N01_Start",
                "nodes": [
                    {
                        "id": "N01_Start",
                        "timer_sec": 2.0,
                        "preload_targets": ["N02_Loop_A"],
                        "choices": [
                            {"label": "坠入幻境", "target": "N02_Loop_A"},
                            {"label": "破阵突围", "target": "N04_End"},
                            {"label": "未知断崖", "target": "N99_Missing"},
                        ],
                    },
                    {
                        "id": "N02_Loop_A",
                        "preload_targets": ["N03_Loop_B"],
                        "choices": [
                            {"label": "向左走", "target": "N03_Loop_B"},
                            {"label": "原地徘徊", "target": "N02_Loop_A"},
                        ],
                    },
                    {
                        "id": "N03_Loop_B",
                        "preload_targets": ["N02_Loop_A"],
                        "choices": [
                            {"label": "向右走", "target": "N02_Loop_A"},
                        ],
                    },
                    {
                        "id": "N04_End",
                        "is_ending": True,
                    },
                    {
                        "id": "N05_Orphan_DeadEnd",
                        "is_ending": False,
                        "choices": [],
                    },
                ],
            }
        )
        self.assertFalse(rep.passed)
        self.assertEqual(rep.score, 0)
        self.assertTrue(any("DANGLING_CHOICE_TARGET" in v for v in rep.violations))
        self.assertTrue(any("DECISION_TIMER_OUT_OF_RANGE" in v for v in rep.violations))
        self.assertTrue(any("MISSING_TIMEOUT_DEFAULT_CHOICE" in v for v in rep.violations))
        self.assertTrue(any("NEXT_BRANCH_PRELOAD_MISSING" in v for v in rep.violations))
        self.assertTrue(any("CHOICE_COUNT_OUT_OF_RANGE" in v for v in rep.violations))
        self.assertTrue(any("NON_TERMINAL_DEAD_END" in v for v in rep.violations))
        self.assertTrue(any("UNREACHABLE_ORPHAN_NODE" in v for v in rep.violations))
        self.assertTrue(any("INFINITE_TRAP_WITHOUT_ENDING" in v for v in rep.violations))

    def test_inspect_native_shell_package_passes_compliant_apk_and_windows_exe(self):
        rep_apk = inspect_native_shell_package(
            {
                "app_id": "studio.xingtu.blade_chronicle",
                "signed": True,
                "debuggable": False,
                "keystore_type": "release",
                "devtools_enabled": False,
                "target_sdk": 35,
                "abis": ["arm64-v8a", "armeabi-v7a"],
                "permissions": ["android.permission.INTERNET", "VIBRATE"],
                "icon_px": 512,
                "package_mb": 142.0,
            },
            platform="android_apk",
        )
        self.assertTrue(rep_apk.passed)
        self.assertEqual(rep_apk.score, 100)
        self.assertEqual(rep_apk.violations, [])
        self.assertTrue(rep_apk.metrics["has_arm64"])

        rep_exe = inspect_native_shell_package(
            {
                "app_id": "studio.xingtu.blade_chronicle_pc",
                "signed": True,
                "debuggable": False,
                "keystore_type": "authenticode",
                "devtools_enabled": False,
                "pck_embedded": True,
                "dpi_awareness": "per_monitor_v2",
                "icon_px": 1024,
                "package_mb": 680.0,
            },
            platform="windows_exe",
        )
        self.assertTrue(rep_exe.passed)
        self.assertEqual(rep_exe.score, 100)
        self.assertEqual(rep_exe.violations, [])
        self.assertTrue(rep_exe.metrics["archive_sealed"])

    def test_inspect_native_shell_package_catches_signing_sdk_abi_perm_and_dpi_traps(self):
        rep_bad_apk = inspect_native_shell_package(
            {
                "app_id": "com.example.mygame",
                "signed": False,
                "debuggable": True,
                "keystore_type": "debug",
                "devtools_enabled": True,
                "target_sdk": 31,
                "abis": ["armeabi-v7a"],
                "permissions": ["android.permission.READ_CONTACTS", "READ_SMS"],
                "icon_px": 192,
                "package_mb": 620.0,
            },
            platform="android_apk",
        )
        self.assertFalse(rep_bad_apk.passed)
        self.assertEqual(rep_bad_apk.score, 0)
        self.assertTrue(any("PLACEHOLDER_APP_ID_REJECTED" in v for v in rep_bad_apk.violations))
        self.assertTrue(any("DEBUG_OR_UNSIGNED_RELEASE" in v for v in rep_bad_apk.violations))
        self.assertTrue(any("DEVTOOLS_EXPOSED_IN_RELEASE" in v for v in rep_bad_apk.violations))
        self.assertTrue(any("ANDROID_TARGET_SDK_OUTDATED" in v for v in rep_bad_apk.violations))
        self.assertTrue(any("MISSING_ARM64_ABI" in v for v in rep_bad_apk.violations))
        self.assertTrue(any("EXCESSIVE_DANGEROUS_PERMISSION" in v for v in rep_bad_apk.violations))
        self.assertTrue(any("APP_ICON_RESOLUTION_TOO_LOW" in v for v in rep_bad_apk.violations))
        self.assertTrue(any("NATIVE_PACKAGE_SIZE_EXCEEDED" in v for v in rep_bad_apk.violations))

        rep_bad_exe = inspect_native_shell_package(
            {
                "app_id": "BadAppId",
                "signed": True,
                "debuggable": False,
                "asar_packed": False,
                "pck_embedded": False,
                "dpi_awareness": "unaware",
                "icon_px": 512,
                "package_mb": 120.0,
            },
            platform="windows_exe",
        )
        self.assertFalse(rep_bad_exe.passed)
        self.assertTrue(any("INVALID_REVERSE_DOMAIN_APP_ID" in v for v in rep_bad_exe.violations))
        self.assertTrue(any("UNPACKAGED_RAW_SOURCE_EXPOSED" in v for v in rep_bad_exe.violations))
        self.assertTrue(any("WINDOWS_DPI_AWARENESS_MISSING" in v for v in rep_bad_exe.violations))

    def test_inspect_localization_dubbing_pack_passes_clean_en_and_rtl_ar(self):
        rep_en = inspect_localization_dubbing_pack(
            {
                "font_locales": ["en-US", "es-ES"],
                "glossary": {"林玄": "Lin Xuan", "护宗大阵": "Guardian Array"},
                "entries": [
                    {
                        "id": "D01",
                        "source": "林玄，守住护宗大阵！",
                        "target": "Lin Xuan, hold the Guardian Array!",
                        "slot_duration_sec": 2.6,
                    },
                    {
                        "id": "UI01",
                        "source": "剩余灵石：{count}",
                        "target": "Spirit Stones: {count}",
                    },
                ],
            },
            target_locale="en-US",
        )
        self.assertTrue(rep_en.passed)
        self.assertEqual(rep_en.score, 100)
        self.assertEqual(rep_en.violations, [])

        rep_ar = inspect_localization_dubbing_pack(
            {
                "font_locales": ["ar-SA"],
                "rtl_layout_enabled": True,
                "entries": [
                    {
                        "id": "D01",
                        "source": "立刻撤退！",
                        "target": "انسحبوا على الفور!",
                        "slot_duration_sec": 2.0,
                    }
                ],
            },
            target_locale="ar-SA",
        )
        self.assertTrue(rep_ar.passed)
        self.assertTrue(rep_ar.metrics["requires_rtl"])

    def test_inspect_localization_dubbing_pack_catches_cjk_placeholder_glossary_overflow_pace_and_rtl(self):
        rep_bad = inspect_localization_dubbing_pack(
            {
                "font_locales": ["en-US"],
                "rtl_layout_enabled": False,
                "glossary": {"林玄": "Lin Xuan"},
                "entries": [
                    {
                        "id": "D01",
                        "source": "林玄获得了 {item}！",
                        "target": "Master Xuan got 未翻译道具 TODO_TRANSLATE right now in this extremely overlong single vertical subtitle line!",
                        "slot_duration_sec": 1.5,
                    }
                ],
            },
            target_locale="ar-SA",
        )
        self.assertFalse(rep_bad.passed)
        self.assertEqual(rep_bad.score, 0)
        self.assertTrue(any("FONT_LOCALE_COVERAGE_MISSING" in v for v in rep_bad.violations))
        self.assertTrue(any("RTL_BIDI_LAYOUT_DISABLED" in v for v in rep_bad.violations))
        self.assertTrue(any("UNTRANSLATED_CJK_LEAK" in v for v in rep_bad.violations))
        self.assertTrue(any("RAW_MT_MARKER_LEAK" in v for v in rep_bad.violations))
        self.assertTrue(any("PLACEHOLDER_TOKEN_MISMATCH" in v for v in rep_bad.violations))
        self.assertTrue(any("GLOSSARY_TERM_DRIFT" in v for v in rep_bad.violations))
        self.assertTrue(any("TRANSLATION_EXPANSION_OVERFLOW" in v for v in rep_bad.violations))
        self.assertTrue(any("LOCALIZED_DUB_PACE_EXCEEDED" in v for v in rep_bad.violations))


if __name__ == "__main__":
    unittest.main()
