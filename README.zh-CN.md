# 🎬 Open Short-Drama & WebGame Studio (`open-short-drama-studio`)

[English](README.md) · **简体中文**

[![CI](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)

**面向 AI 漫剧/短剧创作者、故事带货博主与独立游戏开发者的确定性质检门禁、省 85% 算力积分预算器、剪映/CapCut 时间轴生成与网页游戏六端体检工具（零第三方依赖）。**

---

## ✨ 解决什么核心痛点？

1. **🎯 短剧剧本与分镜确定性质检 (`validate_episode_outline`)**：
   - 不靠大模型“自我感觉良好”，用确定性代码硬性检查：**前 3 拍内必须出冷开场钩子 (`is_hook`)**、**单句台词 $\le 35$ 字（防 TTS 语速失真）**、**每集末尾具象悬念钩子**与**动作节拍密度**。
2. **💰 视频生成「刀刃分级」省 85%+ 积分计算器 (`calculate_storyboard_budget`)**：
   - 拒绝无脑全开 1080p Pro 烧钱！将特效/空镜自动分流至包月池（`0` 边际积分），单人凝视走 `480p Lite`（~23 积分），常规对话走 `480p Standard`，全集硬性熔断限制最多 `2` 个高潮名场面使用 `Pro` 模型。
   - 配套 **FFmpeg `Lanczos 插值 + 边缘微锐化 + 动态电影胶片颗粒 (noise=alls=6:allf=t+u)`** 1080p 放大滤镜参数，用胶片质感完美拉满高清成片。
3. **✂️ 剪映 / CapCut 微秒级时间轴清单导出 (`export_capcut_timeline_manifest`)**：
   - 自动将分镜时长与角色台词折算为微秒级（`1,000,000 us = 1s`）对齐的 9:16 竖屏轨道清单。
4. **🎮 HTML5 网页游戏上架预检医生 (`inspect_webgame_bundle`)**：
   - 一键扫描 B站 Toy、Itch.io、CrazyGames 与微信小游戏打包中最常见的白屏/404 元凶（根目录绝对路径 `/assets/...`、外部 CDN 依赖未本地化、缺失移动端 Viewport）。

---

## 🚀 30 秒快速体验

```bash
git clone https://github.com/17671454333/open-short-drama-studio.git
cd open-short-drama-studio
python -m drama_kit demo
python -m unittest discover -s tests -v
```

---

## 💎 Open-Core 社区版 vs. Studio Pro 商业完整版对比

本项目采用 **Open-Core（核心质量门与预算计算开源 + 工业级全自动流水线商业化）** 架构：

| 功能模块 | 社区开源版 (本仓库 · MIT 免费) | Studio Pro 商业旗舰版 (Sponsors / 商业授权) |
| :--- | :---: | :---: |
| **短剧剧本质量门与冷开场钩子校验** | ✅ 完整内置 | ✅ + 跨集爽点节奏矩阵与小说拆书引擎 |
| **Seedance/Flow 三级省积分计算器** | ✅ 完整内置 | ✅ + 本地 FFmpeg 全自动批处理胶片超分管线 |
| **剪映 / CapCut 时间轴导出** | ✅ 标准 JSON 清单 | 🚀 **直写本机 `D:\CapCut Drafts` 一键成片（含运镜/特效/配乐）** |
| **跨镜头角色锁脸三视图系统** | — | 🚀 **正面锚点 + 6 视图派生一致性锁脸生图引擎** |
| **视频号历史/人物故事高转化带货工坊** | — | 🚀 **370+ 爆款钩子语料库 + 毫秒级字音对齐 + 无跳戏复古案头带货镜** |
| **网页游戏六端一键打包器** | ✅ HTML5 白屏/404 预检 | 🚀 **一键生成 Web `.zip` + PC `.exe` + 安卓 `.apk` + 微信小游戏 + 60页软著 PDF** |
| **8 大海内外平台免扫码矩阵一键直发** | — | 🚀 **基于 Chrome M144+ 零弹窗接管一键群发：小红书/抖音/视频号/B站/快手/YouTube双频道/TikTok/EAZO** |

> 🔗 **关联底层开源基建**：查看我们的编码智能体 3+1 认知安全与 Chrome M144+ 零弹窗接管 MCP 服务端 👉 **[`17671454333/jev-cognitive-mcp`](https://github.com/17671454333/jev-cognitive-mcp)**
