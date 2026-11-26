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
11. **📦 多平台网页游戏 ZIP 发行包结构与体积门禁 (`inspect_webgame_archive_manifest`)**：
    - 面向 **B站 Toy、Itch.io、CrazyGames 与微信小游戏** 上架前 ZIP 清单审计：拦截外层目录嵌套白屏（`dist/index.html`）、Windows 反斜杠 ZIP 条目、`.env` / `.git` / `.map` 敏感源码泄露、平台主包体积超限（如微信小游戏 `4MB` 硬顶）、Linux CDN 大小写敏感资源 404 以及无 COOP/COEP 头平台的 `SharedArrayBuffer` 多线程 WASM 兼容隐患。
12. **🗣️ TTS 配音字音同步与硬烧双字幕防重影门禁 (`inspect_tts_subtitle_alignment`)**：
    - 面向剪映/CapCut 成片合成前的字幕与配音对账：自动拦截 AI 裸片自带硬烧乱码字幕导致的双层重影（`BURNED_IN_SUBTITLE_CONFLICT`）、相邻字幕时间重叠踩踏、`< 0.45s` 闪帧字幕、TTS 起止时间漂移 `> 0.25s`、竖屏句尾冗余标点（`，。、；`）及 `> 6.5 字/秒` 超速抢拍，并同步输出去尾标点与时间轴归一化的 `cleaned_cues`。
13. **🧭 2D 俯视站位调度与 180° 轴线防穿模门禁 (`inspect_scene_staging_plan`)**：
    - 面向分镜生图前的空间走位确定性对账：校验 `[0.05, 0.95]` 俯视安全平面锚点坐标、双向核对在场演员与剧本角色表（杜绝漏排说话人或混入幽灵人物）、拦截同一锚点同侧叠人穿模（`SAME_SIDE_COLLISION`）与 `< 0.08` 贴脸融合风险（`PROXIMITY_CROWDING_RISK`）、强制锁定 180° 摄影机轴线与群演分区（`extras_zone`），并确定性生成英文首镜走位句 `opening_blocking_line`。
14. **🏛️ 场景空景锚点与白底无手道具设定集门禁 (`inspect_scene_prop_bible`)**：
    - 面向美术设定集与下游垫图一致性的确定性审计：强制每个场景具备 `[3, 5]` 个跨集不变视觉锚点、拦截场景空景提示词混入路人/角色（`SCENE_EMPTY_PLATE_ACTOR_CONTAMINATION`，杜绝垫图假人叠影）、拦截叙事道具提示词带手握持（`PROP_HAND_CONTAMINATION`）或非纯白底不可抠图（`PROP_NON_ISOLATED_BACKGROUND`）及缺失 `[0.5, 500.0]` cm 物理尺度参照，并双向对账剧本所需的场景光照变体与道具状态变体。
15. **📈 跨集爽点节奏、黄金开篇与付费卡点转化门禁 (`inspect_series_paywall_pacing`)**：
    - 面向整季短剧改编大纲的留存与变现确定性审计：强制黄金前 3 集兑现核心爽点（`GOLDEN_OPENING_PAYOFF_MISSING`）、拦截连续超过 3 集无高潮反转的断档弃剧风险（`PAYOFF_DROUGHT_GAP_EXCEEDED`）、校验付费卡点集悬念强度（`cliffhanger_grade >= 8.0`）、前置集情绪拉升（`PAYWALL_MISSING_PRE_ESCALATION`）与防提前泄气收尾（`PAYWALL_PREMATURE_RESOLUTION`）、约束单集时长 `±15%` 走廊，并动态封顶主角人数（`<= 3`）与跨集主场景预算。
16. **🕹️ 多端小游戏/互动影游运行时性能预算与上架合规门禁 (`inspect_game_release_readiness`)**：
    - 面向 **微信小游戏、抖音小游戏、B站 Toy、TapTap、Itch.io 与 CrazyGames** 上架前运行时体检：强制校验分包总和上限（微信/抖音 `30MB`）与首屏可交互冷启动 `<= 3000ms`、移动端 WebGL 贴图尺寸 `<= 2048px` 与峰值 `DrawCall <= 150` 防黑屏掉帧、首帧点击手势解锁 `AudioContext.resume()`、同源沙箱 `<game_slug>:` 命名空间 `localStorage` 存档防串号、生产环境剥离 `vConsole`/`eruda` 调试探针，以及国内渠道必备的 48 字《健康游戏忠告》闪屏合规校验。
17. **🔀 互动短剧/分支影游状态机拓扑与无缝预加载门禁 (`inspect_interactive_branch_graph`)**：
    - 面向 **B站互动视频、B站 Toy、微信/Steam 互动影游与分支剧情网页游戏** 打包前状态机审计：通过正向 BFS 揪出从入口不可达的孤岛废片节点（`UNREACHABLE_ORPHAN_NODE`，防白烧积分与撑爆包体）、反向 BFS 从全结局节点倒推捕获无出口死循环陷阱（`INFINITE_TRAP_WITHOUT_ENDING`）、拦截悬挂选项引用与非结局死胡同黑屏（`DANGLING_CHOICE_TARGET` / `NON_TERMINAL_DEAD_END`）、约束 9:16 竖屏触控选项数 `[2, 4]` 与 `[4.0s, 20.0s]` 限时抉择超时默认兜底分支（`is_default=True`），并强制对账下一跳视频 `preload_targets` 预加载清单（杜绝切镜解码黑屏闪烁）。
18. **📱🖥️ 跨端 PC `.exe` 与 Android `.apk` 原生壳封装签名门禁 (`inspect_native_shell_package`)**：
    - 面向 **TapTap、Google Play、Steam 与 Itch.io** 原生安装包提审审计：自动拦截未改默认模板包名（`com.example.*` / `org.godotengine.*` / `io.tauri.dev`）、测试证书/未签名包（`DEBUG_OR_UNSIGNED_RELEASE`）、生产包未关 F12 调试器导致 AI 短剧原片裸奔（`DEVTOOLS_EXPOSED_IN_RELEASE`）、Android `target_sdk < 34` 或漏打 64 位 `arm64-v8a` 架构、越权申请通讯录/短信/定位等敏感权限（`EXCESSIVE_DANGEROUS_PERMISSION`）、Windows 端未封包 `asar`/`pck` 源码裸露或缺失 `per_monitor_v2` 高分屏 DPI 清单导致 2K/4K 缩放模糊，以及低于 `512x512` 的商店图标。
19. **🌍 多语种短剧出海译制配音与游戏本地化门禁 (`inspect_localization_dubbing_pack`)**：
    - 面向 **ReelShort、DramaBox、TikTok、YouTube Shorts 与 Steam 多语言版本**（`en-US` / `es-ES` / `pt-BR` / `id-ID` / `ja-JP` / `ko-KR` / `ar-SA`）合成前确定性对账：自动拦截外语台词/UI 残留未翻译汉字（`UNTRANSLATED_CJK_LEAK`）、`{var}`/`%s` 格式化占位符错漏（`PLACEHOLDER_TOKEN_MISMATCH`）、跨集人名/宗门术语表译名漂移（`GLOSSARY_TERM_DRIFT`）、拉丁语系翻译膨胀单行爆框（`TRANSLATION_EXPANSION_OVERFLOW`）、配音语速超原片口型时间窗导致倍速鬼畜（`LOCALIZED_DUB_PACE_EXCEEDED`）、字体子集漏包目标语种导致 `□□□` 豆腐块（`FONT_LOCALE_COVERAGE_MISSING`）以及阿拉伯语未开 RTL 双向排版（`RTL_BIDI_LAYOUT_DISABLED`）。
20. **🛡️ 商用资产版权溯源与 Steam/多平台 AIGC 披露合规门禁 (`inspect_asset_license_provenance`)**：
    - 面向 **Steam、YouTube、TikTok、ReelShort、抖音、视频号与 TapTap** 提审前版权排雷与 AIGC 披露核验：自动拦截非商用/传染性/未知协议混入（`CC-BY-NC` / `CC-BY-ND` / `GPL-3.0-only`、`NON_COMMERCIAL_OR_UNKNOWN_LICENSE`）、未获商业授权封装 `微软雅黑`/`方正`/`汉仪` 字体（`UNLICENSED_COMMERCIAL_FONT`）、YouTube/TikTok Content ID 音乐静音索赔风险（`CONTENT_ID_CLAIM_RISK`）、`CC-BY-4.0` 开源音效漏挂鸣谢表（`MISSING_REQUIRED_ATTRIBUTION`）、生图提示词残留漫威/迪士尼/任天堂等受保护商标或真人明星肖像词（`PROTECTED_IP_OR_LIKENESS_LEAK`）、交付资产缺失 SHA-256 指纹（`MISSING_ASSET_CHECKSUM`）以及漏填 Valve `steam_ai_disclosure` 或短视频 `platform_aigc_flag` 原生合成标识（`MISSING_PLATFORM_AI_DISCLOSURE`）。
21. **🚀 多平台矩阵发布防限流、挂车与 B站 Toy 互动影游绑定门禁 (`inspect_matrix_publish_manifest`)**：
    - 面向 **抖音、视频号、小红书、B站（含 Toy 互动游戏挂载）、YouTube 与 TikTok** 分发前元数据确定性审计：按渠道校验标题字数红线（视频号 `<= 16` 字、小红书 `<= 20` 字、抖音 `<= 30` 字）、拦截公开文案与置顶评论误带本机 `C:\`/`/Users/` 路径、`localhost` 调试地址、邮箱或手机号（`PUBLIC_METADATA_PII_OR_PATH_LEAK`）、拦截跨平台废片水印与国内导流限流黑词（`加微`/`VX:`/`公众号搜`/`私信领`、`TRAFFIC_DIVERSION_OR_WATERMARK_TRAP`）、校验话题标签上限与重复堆砌（`HASHTAG_QUOTA_OR_DUPLICATE_VIOLATION`）、核验视频号 `[4, 12]` 字左下角挂车短标题与 B站 `toy_slug`/`BV` 号互动游戏绑定格式（`COMMERCE_OR_TOY_MOUNT_INVALID`），并对账 `[15, 20160]` 分钟定时发布窗口与短剧合集 `第N集`/`Ep N` 连载序号（`EPISODE_COLLECTION_INDEX_MISMATCH`）。
22. **💳 内购计费、激励广告频控与防沉迷实名合规门禁 (`inspect_monetization_iap_compliance`)**：
    - 面向 **微信小游戏、抖音小游戏、TapTap、B站 Toy、Google Play、App Store 与 Steam** 商业化提审确定性审计：强制国内渠道付费解锁接入实名认证与未成年人充值限额硬锁（`MINOR_ANTI_ADDICTION_UNENFORCED`）、校验 SKU 价格合法性与买断制/季票恢复购买入口并拦截默认勾选自动续费暗黑模式（`IAP_SKU_PRICING_OR_RESTORE_TRAP`）、拦截纯客户端本地验单导致 0 元改档破解（`CLIENT_ONLY_RECEIPT_TRUST_RISK`）、核验抽卡/盲盒 `100%` 概率公示表与 `<= 180` 抽硬保底上限（`GACHA_PROBABILITY_DISCLOSURE_MISSING`），并约束激励视频广告 `>= 90s` 冷却间隔、开局 `>= 30s` 免打扰保护期及无填充优雅降级兜底（`REWARDED_AD_CADENCE_OR_FALLBACK_VIOLATION`）。
23. **☁️ 云端存档跨版本迁移、热更 CDN 完整性与 HTTP 206 流式续播门禁 (`inspect_cloud_save_cdn_manifest`)**：
    - 面向 **微信小游戏、抖音小游戏、B站 Toy、iOS Safari H5、Android APK 与 Steam** 热更与云同步上线前确定性审计：强制远程热更资源启用 HTTPS、不可变内容哈希文件名与 SHA-256 SRI 摘要防缓存错配白屏（`CDN_HTTPS_HASH_OR_SRI_MISSING`）、校验分集视频流切片体积上限（`15MB~25MB`）、首帧海报防切镜黑屏（`poster_frame_ready`）及 iOS WebKit / 微信 WebView 必备的 HTTP `206` `byte_range_supported` 拖动续播支持（`STREAMING_CHUNK_OR_POSTER_VIOLATION`）、强制配置独立 HTTPS 备用 CDN 源站（`CDN_MULTI_ORIGIN_FALLBACK_MISSING`）、校验 `v1 -> vN` 连续无断档存档迁移链防热更清档（`SAVE_SCHEMA_MIGRATION_BROKEN`），并约束云存档体积配额、HMAC 防改档签名与敏感手机号/Token 字段隔离（`CLOUD_SAVE_QUOTA_INTEGRITY_OR_PII_RISK`）。

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
