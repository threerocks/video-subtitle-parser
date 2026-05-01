# Agent Instructions

Use this repository as a CLI-first video intake tool.

The same command contract applies to Codex, OpenClaw, Hermes, Claude Code, Cursor, Windsurf, Aider, Roo Code, Cline, and similar tools.

When a user gives a Douyin, YouTube, or Bilibili URL:

1. Run `video-subtitle-parser "<url>" --platform auto --out-dir materials/<safe-slug>`.
2. Read `*_metadata.json`.
3. Read `*_transcript_turbo_clean.txt`.
4. Use `*_segments_clean.md` for timestamp checks.
5. Do not draft directly from the URL when local artifacts are missing.

If a project has custom names or terms, pass a term file:

```bash
video-subtitle-parser "$URL" --term-file terms.txt --initial-prompt "important project names" --out-dir materials/source-001
```

Do not commit generated MP4, MP3, transcript, or metadata artifacts unless a project explicitly keeps fixtures.
