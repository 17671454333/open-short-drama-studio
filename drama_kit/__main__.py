"""CLI entrypoint for open-short-drama-studio (`python -m drama_kit`)."""
import argparse
import json
from .gates import (
    validate_episode_outline,
    calculate_storyboard_budget,
    export_capcut_timeline_manifest,
    inspect_webgame_bundle,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Open Short-Drama & WebGame Studio CLI (Lite)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="Run end-to-end deterministic short-drama & budget optimization demo")

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
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
