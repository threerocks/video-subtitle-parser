# Cursor Rule

When the user supplies a Douyin, YouTube, or Bilibili video URL, create local transcript artifacts before drafting or summarizing.

```bash
video-subtitle-parser "<url>" --platform auto --out-dir materials/<safe-slug>
```

Read metadata first, then the cleaned transcript. Do not infer facts from the platform page alone.
