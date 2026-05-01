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

Use this OpenClaw skill as a thin wrapper around the CLI.

## Command

```bash
video-subtitle-parser "VIDEO_URL" --platform auto --out-dir materials/video-source
```

If the CLI is not globally installed:

```bash
PYTHONPATH=/path/to/video-subtitle-parser/src \
python3 -m video_subtitle_parser "VIDEO_URL" --platform auto --out-dir materials/video-source
```

## Agent Rules

- Read `*_metadata.json` before writing.
- Read `*_transcript_turbo_clean.txt` as the canonical source.
- Use `*_segments_clean.md` for timestamp checks.
- Pass `--term-file` and `--initial-prompt` for project-specific names.
- Do not draft directly from the original video URL when local artifacts are missing.
