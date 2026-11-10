import unittest
from drama_kit import (
    validate_episode_outline,
    calculate_storyboard_budget,
    export_capcut_timeline_manifest,
    inspect_webgame_bundle,
    inspect_audio_track_quality,
    inspect_caption_safe_zone,
    inspect_social_cover_card,
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

if __name__ == "__main__":
    unittest.main()
