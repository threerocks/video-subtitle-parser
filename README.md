# Video Subtitle Parser

[English](README.md) | [中文](README.zh-CN.md)

Turn Douyin, YouTube, and Bilibili links into local transcript artifacts that AI coding tools can read, cite, rewrite, summarize, and reuse.

Video is usually a poor source format for agents. It is remote, unstable, hard to diff, hard to quote, and often blocked by captions, rate limits, or platform UI. Video Subtitle Parser turns a link into a small local evidence package:

- cleaned transcript text
- timestamped segments
- metadata
- optional source video/audio for later frame extraction

It is a CLI first. Codex, OpenClaw, Hermes, Claude Code, Cursor, Windsurf, Aider, Roo Code, Cline, and other agentic coding tools can call it through the same command contract.

## What It Supports

| Platform | Primary path | Fallback path | Optional media |
| --- | --- | --- | --- |
| Douyin | mobile share page parsing | local ASR through `mlx-whisper` | clean MP4 and audio |
| YouTube | manual/auto subtitles through `yt-dlp` | local ASR when captions fail or rate-limit | MP4 with `--download-video` |
| Bilibili | subtitles through `yt-dlp` | local ASR when subtitles are unavailable or gated | MP4 with `--download-video` |

TikTok and Kuaishou/Kwai are planned next-platform candidates, but they are not exposed as stable platforms in the first open-source release.

## Installation

### Ask Your Agent To Install It

If you use an AI coding tool, you can simply say:

```text
Install this skill: https://github.com/threerocks/video-subtitle-parser
```

Or in Chinese:

```text
帮我安装这个 skill：https://github.com/threerocks/video-subtitle-parser
```

The repository includes a top-level `SKILL.md`, so agent tools that support GitHub skill installation can clone it and use the same CLI contract.

### Manual Install

```bash
git clone https://github.com/threerocks/video-subtitle-parser.git
cd video-subtitle-parser
python3 -m pip install -e .
```

For local ASR fallback on Apple Silicon:

```bash
python3 -m pip install -e ".[asr]"
```

Check the runtime:

```bash
video-subtitle-parser --check
```

`yt-dlp`, `requests`, `imageio-ffmpeg`, and `opencc-python-reimplemented` are normal dependencies. `mlx-whisper` is optional until a video needs ASR fallback.

Before production use, read [Requirements and Limitations](docs/requirements-and-limitations.md). It documents login-state boundaries, YouTube rate limits, Chrome/remote-debugging status, ASR constraints, media/watermark risks, and platform-specific failure modes.

## Quick Start

Auto-detect a platform:

```bash
video-subtitle-parser "VIDEO_URL" \
  --platform auto \
  --out-dir runs/video-material/example
```

Douyin:

```bash
video-subtitle-parser "https://www.douyin.com/video/VIDEO_ID" \
  --platform douyin \
  --language zh \
  --out-dir runs/douyin/VIDEO_ID
```

YouTube:

```bash
video-subtitle-parser "https://www.youtube.com/watch?v=VIDEO_ID" \
  --platform youtube \
  --language en \
  --download-video \
  --out-dir runs/youtube/VIDEO_ID
```

Bilibili:

```bash
video-subtitle-parser "https://www.bilibili.com/video/BVxxxx" \
  --platform bilibili \
  --language zh \
  --download-video \
  --out-dir runs/bilibili/BVxxxx
```

## Output Contract

For each video, the tool writes a stable artifact family:

```text
<platform>_<id>_transcript_turbo.txt
<platform>_<id>_transcript_turbo_clean.txt
<platform>_<id>_segments_clean.md
<platform>_<id>_metadata.json
<platform>_<id>_transcript_turbo.json   # when ASR fallback is used
<platform>_<id>_audio.mp3               # when ASR fallback is used
<platform>_<id>.mp4                     # when video download is requested or required
```

The cleaned transcript is the default writing input. The timestamped segments are the review surface. The metadata file records the original URL, platform, video id, title, author, duration, caption source, model, local artifacts, and screenshot/watermark policy.

## Term Cleanup

ASR often gets names and domain terms wrong. Keep the default CLI generic, then pass your project vocabulary explicitly:

```bash
video-subtitle-parser "VIDEO_URL" \
  --term-file examples/jianlai_terms.txt \
  --initial-prompt "陈平安 宁姚 阮秀 骊珠洞天 落魄山" \
  --out-dir runs/jianlai/BVxxxx
```

Term files are UTF-8 text:

```text
wrong=>right
软秀=>阮秀
逆瑶=>宁姚
```

Bare terms may be kept as human reference notes, but only `wrong=>right` lines are applied automatically.

## AI Agent Usage

Use Video Subtitle Parser as an evidence-preparation tool before writing, summarizing, indexing, or extracting frames.

Recommended agent prompt:

```text
Use video-subtitle-parser to parse this video link into a local artifact package.
Prefer official/manual subtitles, then auto subtitles, then local ASR fallback.
Read the cleaned transcript and metadata before writing.
Do not add outside facts unless explicitly asked.
```

See [docs/ai-agent-integration.md](docs/ai-agent-integration.md) for Codex, OpenClaw, Hermes, Claude Code, Cursor, Windsurf, Aider, Roo Code, and Cline examples.

## Design Philosophy

1. Local artifacts beat live links.
   A link can disappear, rate-limit, change captions, or hide behind login. A local transcript package can be reviewed, diffed, cited, and reused.

2. Subtitles are preferred over ASR.
   If official or auto captions exist, use them. ASR is a fallback, not a badge of cleverness.

3. Metadata is part of the evidence.
   Title, author, duration, source URL, caption source, and generated files matter when an AI agent later explains where a claim came from.

4. Project terms belong to the project.
   The core tool stays generic. Names, fandom vocabulary, product terms, and private glossaries enter through `--term-file` and `--initial-prompt`.

5. Screenshots need judgment.
   Downloaded video is useful for frame extraction, but frames must be visually reviewed for platform UI, subtitles, creator marks, and watermarks before publishing.

## Common Workflows

Build a writing packet:

```bash
video-subtitle-parser "$URL" --out-dir materials/video-001
```

Build a frame-extraction packet:

```bash
video-subtitle-parser "$URL" --download-video --out-dir materials/video-001
```

Repair metadata without re-running ASR:

```bash
video-subtitle-parser "$URL" --skip-asr --force --out-dir materials/video-001
```

Force a fresh run after changing model or vocabulary:

```bash
video-subtitle-parser "$URL" --force --term-file terms.txt --out-dir materials/video-001
```

## Ethics and Platform Respect

Use this tool for lawful personal workflows, research, accessibility, and content production. Respect platform terms, copyright, creator rights, private content boundaries, and local law. Do not publish transcripts or screenshots when you do not have the right to do so.

This tool does not use Chrome remote debugging, browser cookies, logged-in Chrome profiles, or account credentials in the current stable release. Public videos are the expected input. See [Requirements and Limitations](docs/requirements-and-limitations.md) for the full boundary list.

## Roadmap

- ASR backend interface for faster-whisper and whisper.cpp
- TikTok support after sample-based validation
- Kuaishou/Kwai support after extractor and login-flow validation
- batch queue mode
- richer subtitle format support
- optional JSONL segment export
- first-class browser-cookie handoff for logged-in platforms

## License

MIT
