# 🎬 Open Short-Drama & WebGame Studio (`open-short-drama-studio`)

**English** · [简体中文](README.zh-CN.md)

[![CI](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg)](pyproject.toml)

**Deterministic Quality Gates, 85%-Credit-Saving Video Budget Optimizer, CapCut/JianYing Timeline Manifest Generator, HTML5 WebGame Pre-Flight Doctor & Studio BGM Audio Quality Gate for AI Creators.**

---

## ✨ Why `open-short-drama-studio`?

Most AI video & short-drama scripts fail before generation even starts: weak cold-open hooks, bloated 60-character dialogue lines that ruin TTS pacing, burning 100% of credits on 1080p Pro models for static talking heads, annoying synthetic sine-wave buzzer artifacts, and manual timeline dragging in CapCut/JianYing.

`open-short-drama-studio` provides **100% deterministic, zero-dependency Python engines** to validate scripts, slash video generation costs by **80%+**, enforce studio audio standards, and generate microsecond-aligned CapCut track manifests.

### Core Modules (`drama_kit`)

1. **🎯 14-Point Episode Outline & Script Gate (`validate_episode_outline`)**:
   - Enforces **Cold-Open Hook within the first 3 beats** (`index 0..2`).
   - Enforces **$\le 35$ characters per dialogue line** for natural TTS lip-sync.
   - Verifies concrete episode cliffhangers and visual action beat density.
2. **💰 3-Tier Video Credit Blade Optimizer (`calculate_storyboard_budget`)**:
   - Routes VFX/empty scenery shots to monthly unlimited pools (`0` marginal credits), static gaze/dialogue to `480p Lite`, standard movement to `480p Standard`, and hard-caps expensive `Pro` models to $\le 2$ climax hero shots per episode.
   - Pairs `480p` cloud output with a deterministic **FFmpeg Lanczos + Unsharp + Dynamic Film-Grain (`noise=alls=6:allf=t+u`)** 1080p upscaling filter, cutting credit costs by **80%~86%**.
3. **✂️ CapCut / JianYing Microsecond Track Manifest (`export_capcut_timeline_manifest`)**:
   - Converts storyboard shots and speaker lines into microsecond-aligned (`1,000,000 us = 1s`) 9:16 vertical video & subtitle tracks ready for draft injection.
4. **🎮 HTML5 WebGame Portal Doctor (`inspect_webgame_bundle`)**:
   - Static pre-flight checker for AI-generated HTML5/Three.js games targeting **Bilibili Toy, Itch.io, CrazyGames, and WeChat Mini-Games** (blocks root-absolute `/assets/...` 404 traps, external CDN leaks, and missing mobile viewport tags).
5. **🎵 Studio Stereo Audio & Anti-Buzzer BGM Quality Gate (`inspect_audio_track_quality`)**:
   - Rejects synthetic pure sine/square-wave buzzer noise (73Hz, 110Hz, 146Hz, 220Hz, 432Hz) with monotonic ratios $> 0.42$.
   - Enforces stereo channel layouts and studio background music master tracks (`ancient_suspense`, `epic_climax`, `action_battle`, `modern_urban`, `tech_showcase`).
   - Generates production-grade vocal denoise (`highpass=f=85,afftdn=nf=-25`) and sidechain ducking filter chain to keep dialogues crystal clear over BGM.

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

`open-short-drama-studio` follows an **Open-Core** model. The deterministic validation, budget planning, and timeline calculation core is 100% free and MIT-licensed. For studios and full-time creators seeking end-to-end automation:

| Feature / Module | Community Core (This Repo · MIT) | Studio Pro Edition (Commercial / Sponsors) |
| :--- | :---: | :---: |
| **Deterministic Script & Hook Quality Gates** | ✅ Included | ✅ Included + Multi-Episode Arc Matrix |
| **3-Tier Credit Optimizer & FFmpeg Grain Formula** | ✅ Included | ✅ + Automated Batch FFmpeg Render Pipeline |
| **CapCut / JianYing Timeline Manifest** | ✅ JSON Manifest | 🚀 **Direct `D:\CapCut Drafts` One-Click Writer (`pyJianYingDraft`)** |
| **Studio Audio Denoise & Anti-Buzzer BGM Gate** | ✅ Included (`inspect_audio_track_quality`) | 🚀 **Automated Sidechain Ducking & Mastering Engine** |
| **Cross-Shot Character Face-Locking** | — | 🚀 **6-View Anchor Reference Sheet & Consistency Engine** |
| **Story Studio E-Commerce Viral Corpus** | — | 🚀 **370+ Proven High-Conversion Hooks & Word-Level Audio Alignment** |
| **WebGame 6-Target Omni-Packager** | ✅ Pre-Flight Doctor | 🚀 **Web `.zip` + Windows `.exe` + Android `.apk` + WeChat Mini-Game + 60-Page Copyright PDF** |
| **8-Platform Zero-Login Matrix Auto-Publisher** | — | 🚀 **One-Click Live Chrome Publishing (YouTube, TikTok, Bilibili, Xiaohongshu, Douyin, WeChat Channels, Kuaishou, EAZO)** |

> 🔗 **Companion Cognitive Infrastructure**: Check out our coding agent 3+1 cognitive security and Chrome M144+ zero-popup live CDP MCP server 👉 **[`17671454333/jev-cognitive-mcp`](https://github.com/17671454333/jev-cognitive-mcp)**
