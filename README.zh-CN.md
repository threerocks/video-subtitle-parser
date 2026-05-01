# Video Subtitle Parser

[English](README.md) | [中文](README.zh-CN.md)

把抖音、YouTube、B 站视频链接变成本地文字稿、时间轴分段和元数据，让 Codex、OpenClaw、Hermes、Claude Code、Cursor、Windsurf、Aider 等 AI 编程工具可以稳定读取、改写、总结和复用。

视频链接本身不适合直接交给 AI。它可能限流，可能没有字幕，可能字幕明天变了，也很难复查。Video Subtitle Parser 做的事很简单：先把视频变成一组本地证据文件，再让 AI 基于这些文件工作。

## 支持平台

| 平台 | 优先路径 | 兜底路径 | 可选媒体 |
| --- | --- | --- | --- |
| 抖音 | 移动分享页解析 | 本地 `mlx-whisper` ASR | clean MP4 和音频 |
| YouTube | `yt-dlp` 获取人工/自动字幕 | 字幕失败、为空或限流后本地 ASR | `--download-video` 下载 MP4 |
| Bilibili | `yt-dlp` 获取字幕 | 字幕不可用、为空或登录限制后本地 ASR | `--download-video` 下载 MP4 |

TikTok 和快手/Kwai 已列入即将支持，但不会作为第一版稳定平台暴露。

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

## 使用边界

请把这个工具用于合法的个人工作流、研究、无障碍、内容生产和资料整理。处理视频时，请尊重平台条款、版权、创作者权益、私密内容边界和当地法律。没有权利发布的文字稿或截图，不要发布。

## 路线图

- 支持 faster-whisper / whisper.cpp 等 ASR 后端
- TikTok 支持，完成样本验证后开放
- 快手/Kwai 支持，完成 extractor 和登录态验证后开放
- 批量队列模式
- 更多字幕格式
- 可选 JSONL 分段导出
- 登录态/cookie 的更清晰交接方式

## License

MIT
