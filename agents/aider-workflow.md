# Aider Workflow

```bash
video-subtitle-parser "$URL" --platform auto --out-dir materials/video-001
aider materials/video-001/*_metadata.json materials/video-001/*_transcript_turbo_clean.txt
```

Ask Aider to write or revise from the transcript artifacts, not from the original video URL.
