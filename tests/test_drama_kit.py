import unittest
from drama_kit import (
    validate_episode_outline,
    calculate_storyboard_budget,
    export_capcut_timeline_manifest,
    inspect_webgame_bundle,
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


if __name__ == "__main__":
    unittest.main()
