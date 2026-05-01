# Platform Notes

For full runtime dependencies, login-state boundaries, rate limits, browser/Chrome status, and privacy notes, read [Requirements and Limitations](requirements-and-limitations.md).

## Douyin

The Douyin path uses the mobile share page because it exposes structured router data for many share URLs. When a `/playwm/` video URL appears, the tool first tries the corresponding `/play/` URL, then falls back to the original URL if needed.

Watermark-free download is not guaranteed. Review frames before publishing screenshots.

## YouTube

The YouTube path uses `yt-dlp` to prefer manual subtitles and auto captions. If captions fail or the timedtext endpoint rate-limits, the tool falls back to local ASR when `mlx-whisper` is installed.

Do not hammer caption endpoints after repeated 429 errors.

## Bilibili

The Bilibili path also uses `yt-dlp`. Some videos have no subtitles, empty subtitles, or login-gated subtitle data. In those cases the tool downloads audio and runs ASR when available.

For frame extraction, check for embedded subtitles, creator marks, and platform UI before publication.

## Planned Features

- TikTok support: validate metadata, subtitle, audio, and video samples across regions before exposing it in `--platform`.
- Kuaishou/Kwai support: validate URL shapes, login state, extractor stability, and domestic/international surface differences before exposing it in `--platform`.
