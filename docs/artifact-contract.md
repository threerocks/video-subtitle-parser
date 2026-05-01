# Artifact Contract

Every successful run should leave enough local evidence for another agent, editor, or human reviewer to continue the work without opening the original platform page.

## Required Artifacts

```text
<platform>_<id>_transcript_turbo_clean.txt
<platform>_<id>_segments_clean.md
<platform>_<id>_metadata.json
```

## Optional Artifacts

```text
<platform>_<id>_transcript_turbo.txt
<platform>_<id>_transcript_turbo.json
<platform>_<id>_audio.mp3
<platform>_<id>.mp4
<platform>_<id>*.vtt
```

## Metadata Fields

- `platform`
- `video_id`
- `source_url`
- `title`
- `description`
- `author`
- `duration`
- `caption_source`
- `subtitle_status`
- `segments`
- `model`
- `term_file`
- `artifacts`
- `watermark_policy`

## Stable Handoff Rule

Agents should treat `*_transcript_turbo_clean.txt` as the canonical writing source and `*_metadata.json` as the provenance record.
