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

Use this skill as a thin agent wrapper around the repository CLI.

## Install

If the CLI is not installed yet, install it from this skill directory:

```bash
python3 -m pip install -e ".[asr]"
```

Use plain `python3 -m pip install -e .` when local ASR fallback is not needed.

## Usage

```bash
video-subtitle-parser "VIDEO_URL" --platform auto --out-dir materials/video-source
```

If the command is not on `PATH`, run it through the local source tree:

```bash
PYTHONPATH={baseDir}/src python3 -m video_subtitle_parser "VIDEO_URL" --platform auto --out-dir materials/video-source
```

After parsing:

- Read `*_metadata.json`.
- Read `*_transcript_turbo_clean.txt`.
- Use `*_segments_clean.md` for timestamp checks.
- Use downloaded MP4 files only after visual review for watermarks, subtitles, and platform UI.

For project-specific names or terms:

```bash
video-subtitle-parser "VIDEO_URL" \
  --term-file terms.txt \
  --initial-prompt "important names and domain terms" \
  --out-dir materials/video-source
```

Do not draft directly from the original video URL when local transcript artifacts are missing.
