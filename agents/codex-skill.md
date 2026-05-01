---
name: video-subtitle-parser
description: Parse Douyin, YouTube, and Bilibili links into local transcript, segment, and metadata artifacts for writing, analysis, and frame extraction.
---

# Video Subtitle Parser

Run the project CLI instead of relying on a browser-only video summary.

```bash
video-subtitle-parser "VIDEO_URL" --platform auto --out-dir materials/video-source
```

After parsing:

- read `*_metadata.json`
- read `*_transcript_turbo_clean.txt`
- use `*_segments_clean.md` for timestamp checks
- use downloaded MP4 only after visual review for watermarks and platform UI

If the project has specialized names or vocabulary, pass:

```bash
--term-file terms.txt --initial-prompt "important names and terms"
```
