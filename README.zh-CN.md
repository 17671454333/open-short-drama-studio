# 🎬 Open Short-Drama & WebGame Studio (`open-short-drama-studio`)

[English](README.md) · **简体中文**

[![CI](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/17671454333/open-short-drama-studio/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg)](pyproject.toml)

**面向 AI 漫剧/短剧创作者、故事带货博主与独立游戏开发者的确定性质检门禁、六段式分镜提示词转写、省 85% 算力积分预算器、剪映/CapCut 时间轴生成、网页游戏六端体检与录音室立体声音频质检工具（零第三方依赖）。**

---

## ✨ 解决什么核心痛点？

1. **🎯 短剧剧本与分镜确定性质检 (`validate_episode_outline`)**：
   - 不靠大模型“自我感觉良好”，用确定性代码硬性检查：**前 3 拍内必须出冷开场钩子 (`is_hook`)**、**单句台词 $\le 35$ 字（防 TTS 语速失真）**、**每集末尾具象悬念钩子**与**动作节拍密度**。
2. **🎨 六段式分镜提示词标准化转写与门禁 (`standardize_shot_prompt`)**：
   - 彻底告别提示词结构混乱导致的人物抽卡变形或运镜丢失，严格规范为六段式电影语言：`【镜头运镜】+【主体一致性锚点】+【动作与微表情】+【空间与光影时段】+【电影影调焦段】+【负向排除词】`。
   - 自适应对齐 **MiniMax H3、Wan 2.1、可灵 Kling 与 Midjourney** 官方最佳工程预设。
3. **💰 视频生成「刀刃分级」省 85%+ 积分计算器 (`calculate_storyboard_budget`)**：
   - 拒绝无脑全开 1080p Pro 烧钱！将特效/空镜自动分流至包月池（`0` 边际积分），单人凝视走 `480p Lite`（~23 积分），常规对话走 `480p Standard`，全集硬性熔断限制最多 `2` 个高潮名场面使用 `Pro` 模型。
   - 配套 **FFmpeg `Lanczos 插值 + 边缘微锐化 + 动态电影胶片颗粒 (noise=alls=6:allf=t+u)`** 1080p 放大滤镜参数，用胶片质感完美拉满高清成片。
4. **✂️ 剪映 / CapCut 微秒级时间轴清单导出 (`export_capcut_timeline_manifest`)**：
   - 自动将分镜时长与角色台词折算为微秒级（`1,000,000 us = 1s`）对齐的 9:16 竖屏轨道清单。
5. **🎮 HTML5 网页游戏上架预检医生 (`inspect_webgame_bundle`)**：
   - 一键扫描 B站 Toy、Itch.io、CrazyGames 与微信小游戏打包中最常见的白屏/404 元凶（根目录绝对路径 `/assets/...`、外部 CDN 依赖未本地化、缺失移动端 Viewport）。
6. **🎵 录音室立体声音频消噪与杜绝正弦波嗡鸣门禁 (`inspect_audio_track_quality`)**：
   - 严禁任何视频生成脚本中使用 `sine=frequency=...` 或低频正弦波/方波充当底噪产生“变压器嗡鸣”，单频正弦能量占比 $> 0.42$ 自动拦截。
   - 硬性校验立体声声道并挂载真实录音室母带（`ancient_suspense` 古风悬疑、`epic_climax` 高燃史诗、`action_battle` 战斗、`modern_urban` 都市、`tech_showcase` 科技宣发）。
   - 自动生成硬件级人声消噪（`highpass=f=85,afftdn=nf=-25`）与人声侧链自动闪避压制（Sidechain Ducking）滤镜链，配乐饱满且不抢台词。
7. **📱 竖屏字幕安全区与多平台封面合规门禁 (`inspect_caption_safe_zone` / `inspect_social_cover_card`)**：
   - 自动校验视频号 16 字单行标题红线、抖音/快手/小红书底部进度条与右侧互动栏遮挡避让，以及 `3:4` / `9:16` / `16:9` / `1:1` 封面比例与 AI 辅助生成显著声明标识。
8. **🎭 跨镜头角色锚点拓扑与派生图过期校验门禁 (`inspect_character_anchor_pack`)**：
   - 强制执行「正面全身主锚点 (`frontal_full`) 单跳辐射派生图」星型拓扑（严禁 `A -> B -> C` 多跳参考导致五官漂移），主图重出后自动拦截过期子视图 (`STALE_DERIVED_VIEW`) 并对账剧本说话人覆盖度。
9. **🎞️ 多平台成片 `-14 LUFS` 母带交付预检门禁 (`inspect_master_video_delivery`)**：
   - 上架前一键核验 `-14.0 ± 2.5 LUFS` 响度靶心、`<= -1.0 dBTP` 防爆音真峰值上限、`yuv420p` 移动端硬解像素格式、`+faststart` 流式秒开 `moov` 前置头、CFR 恒定帧率防口型漂移、音画时长同步（误差 `<= 120ms`）与冷开场零黑屏（`<= 0.15s`），并自动输出 FFmpeg 母带重压制命令参数。
10. **🎬 多镜头单段 `<= 15s` 切点对齐与参考图槽位门禁 (`inspect_multishot_segment_cuts`)**：
    - 面向 MiniMax H3 `[Shot k]`、Seedance 2.0 与 Omni Flash 单次多镜生成，确定性校验主分镜图钉死 `0.00s`、切点时刻累加零漂移、单镜 `[1.5s, 6.0s]` 防闪烁/防长镜衰减、单段总长 `<= 15.0s` 防截断、单段参考图槽位 `<= 4` 张以及 `<d>` 台词口型语速 `<= 4.8 字/秒`。

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
| **六段式分镜提示词转写器** | ✅ 完整内置 (`standardize_shot_prompt`) | ✅ + 角色一致性特征资产库 |
| **Seedance/Flow 三级省积分计算器** | ✅ 完整内置 | ✅ + 本地 FFmpeg 全自动批处理胶片超分管线 |
| **剪映 / CapCut 时间轴导出** | ✅ 标准 JSON 清单 | 🚀 **直写本机 `D:\CapCut Drafts` 一键成片（含运镜/特效/配乐）** |
| **立体声音频消噪与杜绝正弦波嗡鸣门禁** | ✅ 完整内置 (`inspect_audio_track_quality`) | 🚀 **全自动侧链闪避混音与母带压制流水线** |
| **跨镜头角色锁脸三视图系统** | — | 🚀 **正面锚点 + 6 视图派生一致性锁脸生图引擎** |
| **网页游戏六端一键打包器** | ✅ HTML5 白屏/404 预检 | 🚀 **一键生成 Web `.zip` + PC `.exe` + 安卓 `.apk` + 微信小游戏 + 60页软著 PDF** |
| **8 大海内外平台免扫码矩阵一键直发** | — | 🚀 **基于 Chrome M144+ 零弹窗接管一键群发：小红书/抖音/视频号/B站/快手/YouTube双频道/TikTok/EAZO** |

> 🔗 **关联底层开源基建**：查看我们的编码智能体 3+1 认知安全与 Chrome M144+ 零弹窗接管 MCP 服务端 👉 **[`17671454333/jev-cognitive-mcp`](https://github.com/17671454333/jev-cognitive-mcp)**
