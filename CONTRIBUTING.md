# Contributing

Thanks for helping improve Video Subtitle Parser.

## Development Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,asr]"
pytest
ruff check src tests
```

`mlx-whisper` currently targets Apple Silicon. Contributions that add a clean backend abstraction for faster-whisper, whisper.cpp, or remote ASR services are welcome, as long as the default CLI remains deterministic and local-first.

## Pull Request Guidelines

- Keep platform logic isolated. Douyin, YouTube, and Bilibili each have different failure modes.
- Preserve artifact compatibility: `*_transcript_turbo_clean.txt`, `*_segments_clean.md`, and `*_metadata.json` are the stable handoff files.
- Do not add project-specific terms to the default code path. Put them in examples or pass them through `--term-file`.
- Add or update tests for pure parsing, cleanup, and metadata behavior whenever possible.

## Content and Platform Respect

This project is meant for lawful personal workflows, research, accessibility, and content production. Respect each platform's terms, copyright rules, robots policies, and the rights of creators whose videos you process.
