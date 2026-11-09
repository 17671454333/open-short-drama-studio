# 🎬 Open Short-Drama & WebGame Studio (`open-short-drama-studio`)

**English** · [简体中文](README.zh-CN.md)

[![CI](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg)](pyproject.toml)

**Deterministic Quality Gates, Six-Segment Storyboard Prompt Standardizer, 85%-Credit-Saving Video Budget Optimizer, CapCut/JianYing Timeline Manifest Generator, HTML5 WebGame Pre-Flight Doctor & Studio BGM Audio Quality Gate for AI Creators.**

---

## ✨ Why `open-short-drama-studio`?

Most AI video & short-drama scripts fail before generation even starts: weak cold-open hooks, bloated 60-character dialogue lines that ruin TTS pacing, burning 100% of credits on 1080p Pro models for static talking heads, annoying synthetic sine-wave buzzer artifacts, unstructured chaotic prompts that morph character faces, and manual timeline dragging in CapCut/JianYing.

`open-short-drama-studio` provides **100% deterministic, zero-dependency Python engines** to validate scripts, structure 6-segment cinematic prompts, slash video generation costs by **80%+**, enforce studio audio standards, and generate microsecond-aligned CapCut track manifests.

### Core Modules (`drama_kit`)

1. **🎯 14-Point Episode Outline & Script Gate (`validate_episode_outline`)**:
   - Enforces **Cold-Open Hook within the first 3 beats** (`index 0..2`).
   - Enforces **$\le 35$ characters per dialogue line** for natural TTS lip-sync.
   - Verifies concrete episode cliffhangers and visual action beat density.
2. **🎨 Six-Segment Storyboard Prompt Standardizer (`standardize_shot_prompt`)**:
   - Standardizes raw scene descriptions into canonical 6-segment cinematic prompts: `[Shot Size & Movement] + [Subject Visual Anchor] + [Action & Micro-expression Beat] + [Environment & Lighting] + [Cinematic Style & Lens] + [Negative Exclusions]`.
   - Supports targeted presets for **MiniMax H3, Wan 2.1, Kling, and Midjourney**.
3. **💰 3-Tier Video Credit Blade Optimizer (`calculate_storyboard_budget`)**:
   - Routes VFX/empty scenery shots to monthly unlimited pools (`0` marginal credits), static gaze/dialogue to `480p Lite`, standard movement to `480p Standard`, and hard-caps expensive `Pro` models to $\le 2$ climax hero shots per episode.
   - Pairs `480p` cloud output with a deterministic **FFmpeg Lanczos + Unsharp + Dynamic Film-Grain (`noise=alls=6:allf=t+u`)** 1080p upscaling filter, cutting credit costs by **80%~86%**.
4. **✂️ CapCut / JianYing Microsecond Track Manifest (`export_capcut_timeline_manifest`)**:
   - Converts storyboard shots and speaker lines into microsecond-aligned (`1,000,000 us = 1s`) 9:16 vertical video & subtitle tracks ready for draft injection.
5. **🎮 HTML5 WebGame Portal Doctor (`inspect_webgame_bundle`)**:
   - Static pre-flight checker for AI-generated HTML5/Three.js games targeting **Bilibili Toy, Itch.io, CrazyGames, and WeChat Mini-Games** (blocks root-absolute `/assets/...` 404 traps, external CDN leaks, and missing mobile viewport tags).
6. **🎵 Studio Stereo Audio & Anti-Buzzer BGM Quality Gate (`inspect_audio_track_quality`)**:
   - Rejects synthetic pure sine/square-wave buzzer noise (73Hz, 110Hz, 146Hz, 220Hz, 432Hz) with monotonic ratios $> 0.42$.
   - Enforces stereo channel layouts and studio background music master tracks (`ancient_suspense`, `epic_climax`, `action_battle`, `modern_urban`, `tech_showcase`).
   - Generates production-grade vocal denoise (`highpass=f=85,afftdn=nf=-25`) and sidechain ducking filter chain to keep dialogues crystal clear over BGM.
7. **📱 Mobile 9:16 Caption & Title Safe-Zone Inspector (`inspect_caption_safe_zone`)**:
   - Enforces platform UI obstacle avoidance for vertical video across **Douyin, Kuaishou, WeChat Channels, Xiaohongshu, and TikTok** (top status bar `0..12%`, bottom title/progress scrubber `78%~80%..100%`, and right action buttons `82%..100%`).
   - Validates WeChat Channels 16-character single-line title constraint and subtitle line density ($\le 18$ characters) with automated title truncation and caption-splitting repair suggestions.

---

## 🚀 Quick Start (Zero Dependencies)

```bash
git clone https://github.com/17671454333/open-short-drama-studio.git
cd open-short-drama-studio
python -m drama_kit demo
python -m unittest discover -s tests -v
```

---

## 💎 Pro Edition & Commercial Workflow (Open-Core Comparison)

`open-short-drama-studio` follows an **Open-Core** model. The deterministic validation, prompt standardization, budget planning, and timeline calculation core is 100% free and MIT-licensed. For studios and full-time creators seeking end-to-end automation:

| Feature / Module | Community Core (This Repo · MIT) | Studio Pro Edition (Commercial / Sponsors) |
| :--- | :---: | :---: |
| **Deterministic Script & Hook Quality Gates** | ✅ Included | ✅ Included + Multi-Episode Arc Matrix |
| **6-Segment Storyboard Prompt Standardizer** | ✅ Included (`standardize_shot_prompt`) | ✅ + Character Visual Anchor Library |
| **3-Tier Credit Optimizer & FFmpeg Grain Formula** | ✅ Included | ✅ + Automated Batch FFmpeg Render Pipeline |
| **CapCut / JianYing Timeline Manifest** | ✅ JSON Manifest | 🚀 **Direct `D:\CapCut Drafts` One-Click Writer (`pyJianYingDraft`)** |
| **Studio Audio Denoise & Anti-Buzzer BGM Gate** | ✅ Included (`inspect_audio_track_quality`) | 🚀 **Automated Sidechain Ducking & Mastering Engine** |
| **Mobile 9:16 Safe-Zone & Title Gate** | ✅ Included (`inspect_caption_safe_zone`) | 🚀 **Automated Dynamic UI Overlay & Crop Preview Engine** |
| **Cross-Shot Facial Consistency Anchoring** | — | 🚀 **Frontal Anchor + 6-View Multi-Angle Generation Pipeline** |
| **HTML5 WebGame Pre-Flight Doctor** | ✅ Included (`inspect_webgame_bundle`) | 🚀 **6-Platform Build Automation (HTML5, EXE, APK, WeChat, Toy)** |
| **8-Platform Zero-Popup Matrix Publisher** | — | 🚀 **One-Click Multi-Platform Publishing (Chrome M144+ Live CDP)** |

> 🔗 **Underlying Infrastructure**: Check our cognitive agent security runtime & Chrome M144+ live CDP MCP server 👉 **[`17671454333/jev-cognitive-mcp`](https://github.com/17671454333/jev-cognitive-mcp)**
