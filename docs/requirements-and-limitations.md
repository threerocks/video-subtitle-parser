# Requirements and Limitations

Video Subtitle Parser is a local CLI wrapper around platform pages, `yt-dlp`, local media tools, and optional ASR. It helps AI agents work from local evidence files. It does not bypass platform rules, login walls, copyright limits, or network restrictions.

## Runtime Requirements

| Dependency | Required | Why it is used |
| --- | --- | --- |
| Python 3.9+ | Yes | CLI runtime and package installation |
| `requests` | Yes | Douyin mobile share page parsing and media download |
| `yt-dlp` | Yes | YouTube and Bilibili metadata, subtitles, audio, and video download |
| `imageio-ffmpeg` | Yes | Provides an `ffmpeg` binary for audio extraction |
| `opencc-python-reimplemented` | Yes | Traditional-to-Simplified Chinese cleanup |
| `mlx-whisper` | Optional | Local ASR fallback when subtitles are unavailable |

Run:

```bash
video-subtitle-parser --check
```

`mlx-whisper` may be reported as optional missing. That is acceptable until a run needs local ASR fallback.

## System Requirements

- Local disk space is required for transcripts, metadata, audio, and optional MP4 files.
- ASR can be slow and memory-heavy. The default model is `mlx-community/whisper-large-v3-turbo`.
- `mlx-whisper` is mainly intended for Apple Silicon environments. Other ASR backends are planned but not exposed in the first release.
- The tool creates an `out-dir/bin/ffmpeg` symlink to the `imageio-ffmpeg` binary and prepends that directory to `PATH` for the current process.
- Network access is required for metadata, subtitles, and media download.

## Browser, Chrome, and Remote Debugging

The current stable release does not control Chrome and does not use Chrome remote debugging.

That means:

- no browser automation is required;
- no Chrome profile is read;
- no logged-in browser session is reused;
- no Chrome remote debugging port is opened;
- videos that require browser-only login or session access may fail.

Cookie or browser-session handoff may be added later, but it is not part of the current stable contract.

## Login State and Private Content

The stable CLI does not accept cookies, account credentials, or browser profiles.

Implications:

- public videos are the expected input;
- private, friends-only, age-gated, region-gated, member-only, or login-gated videos may fail;
- Bilibili subtitles can be unavailable or login-gated even when the video page is visible in a browser;
- YouTube captions or metadata can differ by region, account, age status, or network;
- Douyin share pages can change structure or block requests.

Do not put account credentials, cookies, or private tokens into issues or public logs.

## Network and Rate Limits

Platform endpoints can rate-limit, block, redirect, or return partial data.

Known patterns:

- YouTube subtitle/timedtext endpoints may return HTTP 429 after repeated access.
- `yt-dlp` extractors can break when platforms change pages or APIs.
- Bilibili may expose metadata but not subtitles.
- Douyin mobile share pages may omit expected router data or media URLs.
- Media downloads can fail while transcript artifacts from subtitles still succeed.

Recommended behavior:

- do not repeatedly hammer a failing subtitle endpoint;
- retry later or from a clean network when rate-limited;
- use ASR fallback when legal and appropriate;
- keep generated metadata so failures are auditable.

## Platform-Specific Limits

### Douyin

- Uses `https://www.iesdouyin.com/share/video/<id>/` with a mobile user agent.
- Parses `window._ROUTER_DATA`; page structure changes can break extraction.
- Tries `/play/` when the share page gives `/playwm/`, but watermark-free download is not guaranteed.
- Always downloads video and extracts audio before ASR.
- Does not use browser login, cookies, or Chrome profiles.

### YouTube

- Uses `yt-dlp` for metadata, manual subtitles, auto subtitles, audio, and optional video download.
- Prefers subtitles, then ASR fallback.
- Captions can be disabled, unavailable, auto-generated with errors, translated, rate-limited, or region/account dependent.
- `--download-video` is optional; without it, the tool may only keep transcript artifacts.
- Repeated subtitle access can trigger rate limits; do not loop aggressively after HTTP 429.

### Bilibili

- Uses `yt-dlp --ignore-config`.
- Some videos have no subtitles, empty subtitles, login-gated subtitles, or metadata that differs by region/account.
- Falls back to audio download plus local ASR when subtitles fail and ASR is available.
- `--download-video` is optional and may fail independently from transcript generation.

## Media, Screenshots, and Watermarks

Downloaded MP4 files are for review and frame extraction workflows. They are not a guarantee that frames are publishable.

Before publishing screenshots, visually check for:

- platform UI;
- embedded subtitles;
- creator marks;
- watermarks;
- cropped logos;
- private or sensitive content.

If a usable clean frame cannot be obtained, generate an original concept image or use another lawful source.

## Accuracy Limits

- ASR can mishear names, numbers, languages, and domain terms.
- Auto captions can be wrong or incomplete.
- `--term-file` only performs literal `wrong=>right` replacement; it is not a full editor.
- `--initial-prompt` can improve ASR recognition but does not guarantee correctness.
- Always review the cleaned transcript before publishing or quoting.

## File and Privacy Limits

- Generated transcripts may contain copyrighted, private, personal, or sensitive content.
- Do not commit generated MP4, MP3, transcript, subtitle, or metadata files unless your project intentionally keeps fixtures.
- `.gitignore` excludes common generated media and transcript artifacts by default.
- Store output under a project-local `materials/` or `runs/` directory so later agents can audit sources.

## Planned but Not Stable

The following are roadmap items, not current stable features:

- TikTok support;
- Kuaishou/Kwai support;
- cookie/browser-session handoff;
- Chrome remote debugging integration;
- batch queues;
- ASR backends beyond `mlx-whisper`;
- JSONL segment export.
