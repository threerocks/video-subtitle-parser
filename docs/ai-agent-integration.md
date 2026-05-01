# AI Agent Integration

Video Subtitle Parser is a normal command-line tool. Any AI coding assistant that can run shell commands and read local files can use it.

## Universal Contract

1. Run the parser into a dedicated output directory.
2. Read `*_metadata.json`.
3. Read `*_transcript_turbo_clean.txt`.
4. Use `*_segments_clean.md` when timestamps or quote checks matter.
5. If image work is needed, use the downloaded MP4 only after visual review.

Before using it in production, review [Requirements and Limitations](requirements-and-limitations.md). Agents should not assume browser login, Chrome remote debugging, cookies, or unlimited subtitle requests are available.

```bash
video-subtitle-parser "$VIDEO_URL" \
  --platform auto \
  --out-dir materials/video-source
```

## Codex

Create a Codex skill that points to this CLI:

```md
---
name: video-subtitle-parser
description: Parse Douyin, YouTube, and Bilibili links into local transcript, segment, and metadata artifacts.
---

Use `video-subtitle-parser "$URL" --platform auto --out-dir <project>/materials/<slug>`.
After the command finishes, read the metadata JSON and cleaned transcript before writing.
```

## OpenClaw

Use this as an OpenClaw/ClawHub-ready skill wrapper around the CLI. The CLI remains the source of truth; the skill only teaches the agent when and how to call it.

```md
---
name: video-subtitle-parser
description: Parses Douyin, YouTube, and Bilibili links into local transcript, segment, and metadata artifacts. Use when a user provides a supported video URL and needs writing, analysis, summarization, or frame-extraction source material.
version: 0.1.0
metadata:
  openclaw:
    homepage: https://github.com/threerocks/video-subtitle-parser
    requires:
      anyBins:
        - python3
---

# Video Subtitle Parser

Run:

video-subtitle-parser "$VIDEO_URL" --platform auto --out-dir materials/<safe-slug>

Then read metadata, cleaned transcript, and timestamped segments before drafting.
```

If the CLI is not installed globally, use the repository path:

```bash
PYTHONPATH=/path/to/video-subtitle-parser/src \
python3 -m video_subtitle_parser "$VIDEO_URL" --platform auto --out-dir materials/<safe-slug>
```

## Hermes

Hermes can use the same CLI contract as long as it can run shell commands and inspect local files. Add this project-level instruction or workflow step:

```md
For Douyin, YouTube, or Bilibili video URLs:

1. Run `video-subtitle-parser "<url>" --platform auto --out-dir materials/<safe-slug>`.
2. Read `*_metadata.json`.
3. Read `*_transcript_turbo_clean.txt`.
4. Use `*_segments_clean.md` for timestamp checks.
5. Do not draft from the video URL directly when transcript artifacts are missing.
```

For project-specific vocabulary, pass:

```bash
video-subtitle-parser "$VIDEO_URL" \
  --term-file terms.txt \
  --initial-prompt "important names and domain terms" \
  --out-dir materials/<safe-slug>
```

## Claude Code

Add a project command such as `.claude/commands/parse-video.md`:

```md
Parse the supplied video URL with:

video-subtitle-parser "$ARGUMENTS" --platform auto --out-dir materials/video-source

Then inspect the generated metadata and cleaned transcript. Use only the transcript unless I ask you to add outside research.
```

## Cursor

Add a project rule:

```md
When the user gives a Douyin, YouTube, or Bilibili video URL, run:

video-subtitle-parser "<url>" --platform auto --out-dir materials/<safe-slug>

Use `*_transcript_turbo_clean.txt` as the canonical source for article drafting.
```

## Windsurf

Add a Cascade instruction:

```md
For video-source tasks, first call `video-subtitle-parser` and write outputs under `materials/`.
Never draft directly from a video URL when transcript artifacts are missing.
```

## Aider

Use it as a pre-step:

```bash
video-subtitle-parser "$URL" --out-dir materials/video-001
aider materials/video-001/*_transcript_turbo_clean.txt materials/video-001/*_metadata.json
```

## Roo Code / Cline

Add this to project instructions:

```md
For supported video URLs, use the local CLI `video-subtitle-parser`.
Do not rely on browser-visible captions as the only source. Produce and read local transcript artifacts first.
```

## Recommended Agent Guardrails

- Do not repeatedly hit subtitle endpoints after HTTP 429; use ASR fallback or retry later.
- Do not add external facts unless the user explicitly asks for research.
- Do not blur, inpaint, or over-crop watermarked frames for publication.
- Keep generated artifacts next to the draft so future revisions can audit the source.
