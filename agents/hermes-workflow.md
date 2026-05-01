# Hermes Workflow

Use Video Subtitle Parser as a local evidence-preparation step before drafting, summarizing, or extracting frames from a supported video URL.

## Instruction

```md
When the user gives a Douyin, YouTube, or Bilibili URL, run:

video-subtitle-parser "<url>" --platform auto --out-dir materials/<safe-slug>

Then inspect:

- `*_metadata.json`
- `*_transcript_turbo_clean.txt`
- `*_segments_clean.md`

Use the cleaned transcript as the source of truth. Do not rely on the URL alone.
```

## With Project Vocabulary

```bash
video-subtitle-parser "$URL" \
  --term-file terms.txt \
  --initial-prompt "important names and domain terms" \
  --out-dir materials/video-001
```

## Fallback Without Global Install

```bash
PYTHONPATH=/path/to/video-subtitle-parser/src \
python3 -m video_subtitle_parser "$URL" --platform auto --out-dir materials/video-001
```
