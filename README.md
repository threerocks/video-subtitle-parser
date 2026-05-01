# Video Subtitle Parser

[![CI](https://github.com/threerocks/video-subtitle-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/threerocks/video-subtitle-parser/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.9--3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platforms](https://img.shields.io/badge/platforms-Douyin%20%7C%20YouTube%20%7C%20Bilibili-orange)

把抖音、YouTube、B 站视频链接变成本地文字稿、时间轴分段和元数据，让 Codex、OpenClaw、Hermes、Claude Code、Cursor、Windsurf、Aider 等 AI 编程工具可以稳定读取、改写、总结和复用。

视频链接本身不适合直接交给 AI。它可能限流，可能没有字幕，可能字幕明天变了，也很难复查。Video Subtitle Parser 做的事很简单：先把视频变成一组本地证据文件，再让 AI 基于这些文件工作。

## 使用边界

请把这个工具用于正当的个人学习、研究和内容整理场景。比如：不方便看视频时提取文字来学习知识，把自己的视频素材整理成可检索笔记，或者为图文类自媒体工作收集参考素材。

请尊重版权、平台规则和原作者劳动成果。不要把转写稿、总结、截图或派生素材用于完整复刻他人成果，不要冒充原创，不要绕过署名和授权，更不要在未获得必要权利的情况下用于商业发布或商业变现。

**重要：**
> 因使用者对产物的保存、改写、发布、传播、商用或其他后续行为产生的版权、平台、商业或法律纠纷，均由使用者自行承担，与本工具及维护者无关。

## 快速识别

```bash
git clone https://github.com/threerocks/video-subtitle-parser.git
cd video-subtitle-parser
python3 -m pip install -e .
video-subtitle-parser --check
video-subtitle-parser "$VIDEO_URL" --platform auto --out-dir materials/video-001
```

典型输出：

```text
materials/video-001/
├── youtube_dQw4w9WgXcQ_metadata.json
├── youtube_dQw4w9WgXcQ_segments_clean.md
├── youtube_dQw4w9WgXcQ_transcript_turbo.txt
└── youtube_dQw4w9WgXcQ_transcript_turbo_clean.txt
```

最小 metadata 形态：

```json
{
  "platform": "youtube",
  "video_id": "dQw4w9WgXcQ",
  "title": "示例标题",
  "author": "示例频道",
  "caption_source": "youtube_subtitles_or_auto_captions",
  "artifacts": {
    "transcript_clean_txt": "materials/video-001/youtube_dQw4w9WgXcQ_transcript_turbo_clean.txt",
    "segments_clean_md": "materials/video-001/youtube_dQw4w9WgXcQ_segments_clean.md"
  }
}
```

## 支持平台

| 平台 | 优先路径 | 兜底路径 | 可选媒体 |
| --- | --- | --- | --- |
| 抖音 | 移动分享页解析 | 本地 `mlx-whisper` ASR | clean MP4 和音频 |
| YouTube | `yt-dlp` 获取人工/自动字幕 | 字幕失败、为空或限流后本地 ASR | `--download-video` 下载 MP4 |
| Bilibili | `yt-dlp` 获取字幕 | 字幕不可用、为空或登录限制后本地 ASR | `--download-video` 下载 MP4 |

## 功能特性

稳定功能：

- 自动识别抖音、YouTube、B 站链接。
- 优先使用人工/官方字幕。
- 在 ASR 前复用自动字幕。
- 使用 `mlx-whisper` 做本地 ASR 兜底。
- 生成清理稿、时间轴分段和 metadata。
- 可选下载 MP4，服务后续截帧。
- 通过 `--term-file` 做项目术语清洗。
- 通过 `--initial-prompt` 给 ASR 传入领域词汇。
- 通过同一套 CLI 契约接入 Codex、OpenClaw、Hermes、Claude Code、Cursor、Windsurf、Aider、Roo Code、Cline。

计划功能：

- TikTok 支持。
- 快手/Kwai 支持。
- cookie / 浏览器会话交接。
- Chrome 远程调试集成。
- 批量队列模式。
- faster-whisper、whisper.cpp 等更多 ASR 后端。
- JSONL 分段导出。

## 依赖与限制
正式使用前，请**务必阅读** [依赖与限制](docs/requirements-and-limitations.zh-CN.md)，**这是它可用的基础和前提**。


## 安装

### 让 Agent 直接安装

如果你使用支持安装 GitHub skill 的 AI 编程工具，可以直接对它说：

```text
帮我安装这个 skill：https://github.com/threerocks/video-subtitle-parser
```

也可以用英文：

```text
Install this skill: https://github.com/threerocks/video-subtitle-parser
```

仓库根目录包含 `SKILL.md`，支持 GitHub skill 安装的 Agent 可以直接克隆并按同一套 CLI 契约使用。

### 手动安装

```bash
git clone https://github.com/threerocks/video-subtitle-parser.git
cd video-subtitle-parser
python3 -m pip install -e .
```

如果需要本地 ASR 兜底，Apple Silicon 用户可以安装：

```bash
python3 -m pip install -e ".[asr]"
```

检查环境：

```bash
video-subtitle-parser --check
```

常规依赖包括 `yt-dlp`、`requests`、`imageio-ffmpeg`、`opencc-python-reimplemented`。`mlx-whisper` 是可选依赖，只有在需要本地语音识别兜底时才必须安装。
不必担心，你的 Agent 会帮你安装这些。


版本范围见 [CHANGELOG.md](CHANGELOG.md)。Agent 安装验证清单见 [Agent Install Smoke Test](docs/agent-install-smoke-test.md)。

## 快速开始

自动识别平台：

```bash
video-subtitle-parser "VIDEO_URL" \
  --platform auto \
  --out-dir runs/video-material/example
```

抖音：

```bash
video-subtitle-parser "https://www.douyin.com/video/VIDEO_ID" \
  --platform douyin \
  --language zh \
  --out-dir runs/douyin/VIDEO_ID
```

YouTube：

```bash
video-subtitle-parser "https://www.youtube.com/watch?v=VIDEO_ID" \
  --platform youtube \
  --language en \
  --download-video \
  --out-dir runs/youtube/VIDEO_ID
```

B 站：

```bash
video-subtitle-parser "https://www.bilibili.com/video/BVxxxx" \
  --platform bilibili \
  --language zh \
  --download-video \
  --out-dir runs/bilibili/BVxxxx
```

## 输出文件

每条视频会生成一组稳定的素材文件：

```text
<platform>_<id>_transcript_turbo.txt
<platform>_<id>_transcript_turbo_clean.txt
<platform>_<id>_segments_clean.md
<platform>_<id>_metadata.json
<platform>_<id>_transcript_turbo.json   # 使用 ASR 兜底时生成
<platform>_<id>_audio.mp3               # 使用 ASR 兜底时生成
<platform>_<id>.mp4                     # 请求下载视频或平台路径需要时生成
```

建议把 `*_transcript_turbo_clean.txt` 当作写作输入，把 `*_segments_clean.md` 当作时间轴复查入口，把 `*_metadata.json` 当作来源记录。

## 仓库结构

```text
src/video_subtitle_parser/   Python CLI 包
tests/                       纯解析和清理测试
docs/                        Agent 接入、产物契约、平台说明
agents/                      可复制的规则和 workflow 片段
examples/                    示例术语表
articles/                    首发和推广文章草稿
SKILL.md                     Agent 安装器识别的根目录 skill
```

## 术语清洗

ASR 经常听错人名、作品名和专有名词。通用工具不应该内置某个项目的词表，所以这里使用显式参数：

```bash
video-subtitle-parser "VIDEO_URL" \
  --term-file examples/jianlai_terms.txt \
  --initial-prompt "陈平安 宁姚 阮秀 骊珠洞天 落魄山" \
  --out-dir runs/jianlai/BVxxxx
```

词表是 UTF-8 文本：

```text
wrong=>right
软秀=>阮秀
逆瑶=>宁姚
```

只有 `wrong=>right` 行会自动替换。单独写一行术语可以作为人工参考，不会被自动处理。

## AI 编程工具接入

Video Subtitle Parser 是 CLI-first 工具。任何能运行 shell 命令、读取本地文件的 AI 编程工具都能使用它。

推荐提示词：

```text
请使用 video-subtitle-parser 解析这个视频链接，生成本地素材包。
优先使用官方/人工字幕，其次自动字幕，字幕不可用时再使用本地 ASR。
写作前先读取 metadata 和 cleaned transcript。
除非我明确要求外部资料，不要额外补充视频外信息。
```

更多示例见：[docs/ai-agent-integration.md](docs/ai-agent-integration.md)，其中包含 Codex、OpenClaw、Hermes、Claude Code、Cursor、Windsurf、Aider、Roo Code、Cline 的接入方式。

## 设计原则

1. 本地素材优于远程链接。
   链接会变化、限流、失效；本地文字稿可以复查、diff、引用和复用。

2. 字幕优先，ASR 兜底。
   有官方/人工/自动字幕时先用字幕；字幕失败、为空或限流时，再走本地语音识别。

3. 元数据也是证据。
   标题、作者、时长、来源链接、字幕来源和本地文件路径，都会影响后续 AI 判断。

4. 项目术语归项目管理。
   核心工具保持通用。人名、作品名、行业术语通过 `--term-file` 和 `--initial-prompt` 输入。

5. 视频截图需要人工判断。
   下载 MP4 方便截帧，但发布前仍要检查平台 UI、字幕条、作者水印和画面标记。

## 常见工作流

生成写作素材包：

```bash
video-subtitle-parser "$URL" --out-dir materials/video-001
```

生成可截帧素材包：

```bash
video-subtitle-parser "$URL" --download-video --out-dir materials/video-001
```

只修复元数据或下载，不重新 ASR：

```bash
video-subtitle-parser "$URL" --skip-asr --force --out-dir materials/video-001
```

修改模型或词表后强制重跑：

```bash
video-subtitle-parser "$URL" --force --term-file terms.txt --out-dir materials/video-001
```

## 公众号示例

这个工具最早来自真实内容生产流程。

「一只国漫观察猫」会用它处理国漫解析视频，例如《剑来》人物志、剧情问答、逐帧解析。先看 metadata 判断视频类型，再决定文章标题和结构，避免把人物志误写成“第几集逐帧解析”。

「人间缓冲站」则适合用它处理情绪、关系和生活经验类长视频。先把视频落成文字稿，再让 AI 围绕材料写作，减少凭空补理论、补案例的问题。

两个公众号题材不同，但底层方法一样：先让素材有证据，再让表达发生。


## 路线图

- 支持 faster-whisper / whisper.cpp 等 ASR 后端
- 批量队列模式
- 更多字幕格式
- 可选 JSONL 分段导出
- 登录态/cookie 的更清晰交接方式

## License

MIT
