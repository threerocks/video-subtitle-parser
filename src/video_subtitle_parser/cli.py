#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1"
)

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"
SCRIPT_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = SCRIPT_DIR


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def require_import(module: str, package_hint: str | None = None) -> Any:
    try:
        return __import__(module)
    except ImportError as exc:
        hint = package_hint or module
        raise SystemExit(f"Missing dependency: {hint}. Install it with python3 -m pip install --user {hint}") from exc


def check_dependencies() -> int:
    checks = [
        ("yt_dlp", "yt-dlp"),
        ("requests", "requests"),
        ("imageio_ffmpeg", "imageio-ffmpeg"),
        ("opencc", "opencc-python-reimplemented"),
    ]
    ok = True
    for module, package in checks:
        try:
            __import__(module)
            print(f"OK {package}")
        except ImportError:
            print(f"MISSING {package}")
            ok = False
    try:
        __import__("mlx_whisper")
        print("OK mlx-whisper")
    except ImportError:
        print("OPTIONAL MISSING mlx-whisper (required only for local ASR fallback)")
    return 0 if ok else 1


def platform_from_url(value: str) -> str:
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "bilibili.com" in host or "b23.tv" in host or re.fullmatch(r"BV[0-9A-Za-z]+", value.strip()):
        return "bilibili"
    if "douyin.com" in host or "iesdouyin.com" in host or re.fullmatch(r"\d{10,}", value.strip()):
        return "douyin"
    raise SystemExit(f"Unsupported video platform: {value}")


def ytdlp_cmd() -> list[str]:
    if shutil.which("yt-dlp"):
        return [shutil.which("yt-dlp") or "yt-dlp"]
    try:
        __import__("yt_dlp")
        return ["python3", "-m", "yt_dlp"]
    except Exception as exc:
        raise SystemExit("Missing dependency: yt-dlp. Install it with python3 -m pip install --user yt-dlp") from exc


def extract_video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"\d{10,}", value):
        return value

    parsed = urlparse(value)
    query = parse_qs(parsed.query)
    for key in ("modal_id", "video_id", "item_id", "aweme_id"):
        if query.get(key):
            return query[key][0]

    patterns = [
        r"/share/video/(\d+)",
        r"/video/(\d+)",
        r"modal_id=(\d+)",
        r"(\d{10,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)
    raise SystemExit(f"Could not extract Douyin video id from: {value}")


def fetch_router_data(video_id: str) -> tuple[dict[str, Any], str]:
    requests = require_import("requests", "requests")
    share_url = f"https://www.iesdouyin.com/share/video/{video_id}/"
    headers = {
        "User-Agent": MOBILE_UA,
        "Referer": "https://www.douyin.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(share_url, headers=headers, timeout=30)
    response.raise_for_status()
    match = re.search(r"window\._ROUTER_DATA\s*=\s*(\{.*?\})</script>", response.text, re.S)
    if not match:
        raise SystemExit("Could not find window._ROUTER_DATA in mobile share page.")
    return json.loads(match.group(1)), share_url


def first_video_item(router_data: dict[str, Any]) -> dict[str, Any]:
    loader = router_data.get("loaderData") or {}
    candidates = []
    for key, value in loader.items():
        if isinstance(value, dict) and "videoInfoRes" in value:
            candidates.append(value)
        if key.endswith("/page") and isinstance(value, dict):
            candidates.append(value)
    for page in candidates:
        items = (((page.get("videoInfoRes") or {}).get("item_list")) or [])
        if items:
            return items[0]
    raise SystemExit("Could not find videoInfoRes.item_list[0] in _ROUTER_DATA.")


def safe_filename(value: str, fallback: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|\r\n]+", " ", value).strip()
    value = re.sub(r"\s+", "-", value)
    return value[:80] or fallback


def ensure_ffmpeg_bin(out_dir: Path) -> Path:
    imageio_ffmpeg = require_import("imageio_ffmpeg", "imageio-ffmpeg")
    ffmpeg_src = Path(imageio_ffmpeg.get_ffmpeg_exe())
    bin_dir = out_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_link = bin_dir / "ffmpeg"
    if ffmpeg_link.exists() or ffmpeg_link.is_symlink():
        if ffmpeg_link.resolve() == ffmpeg_src:
            return ffmpeg_link
        ffmpeg_link.unlink()
    ffmpeg_link.symlink_to(ffmpeg_src)
    return ffmpeg_link


def play_url_candidates(play_url: str) -> list[str]:
    candidates = []
    if "/playwm/" in play_url:
        candidates.append(play_url.replace("/playwm/", "/play/"))
    candidates.append(play_url)
    seen = set()
    unique = []
    for url in candidates:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def download_file(urls: str | list[str], path: Path, force: bool = False) -> str:
    requests = require_import("requests", "requests")
    if path.exists() and path.stat().st_size > 0 and not force:
        eprint(f"Reuse existing video: {path}")
        if isinstance(urls, list):
            return urls[0]
        return urls

    tmp_path = path.with_suffix(path.suffix + ".part")
    headers = {
        "User-Agent": MOBILE_UA,
        "Referer": "https://www.iesdouyin.com/",
        "Accept": "*/*",
    }
    if isinstance(urls, str):
        urls = [urls]
    errors = []
    for url in urls:
        try:
            eprint(f"Trying video URL: {url.split('?')[0]}")
            with requests.get(url, headers=headers, stream=True, timeout=60, allow_redirects=True) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type") or ""
                if "video" not in content_type and "octet-stream" not in content_type:
                    raise RuntimeError(f"unexpected content-type: {content_type}")
                total = int(response.headers.get("content-length") or 0)
                done = 0
                with tmp_path.open("wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        handle.write(chunk)
                        done += len(chunk)
                        if total:
                            percent = done * 100 / total
                            eprint(f"\rDownloading video: {percent:5.1f}%",)
                eprint("")
            tmp_path.replace(path)
            return url
        except Exception as exc:
            errors.append(f"{url}: {exc}")
            if tmp_path.exists():
                tmp_path.unlink()
            eprint(f"Video URL failed, trying fallback if available: {exc}")
    raise SystemExit("All video download URLs failed:\n" + "\n".join(errors))


def extract_audio(video_path: Path, audio_path: Path, ffmpeg_path: Path, force: bool = False) -> None:
    if audio_path.exists() and audio_path.stat().st_size > 0 and not force:
        eprint(f"Reuse existing audio: {audio_path}")
        return
    cmd = [
        str(ffmpeg_path),
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "64k",
        str(audio_path),
    ]
    subprocess.run(cmd, check=True)


def load_replacements(term_file: Path | None = None) -> list[tuple[str, str]]:
    replacements: list[tuple[str, str]] = []
    if term_file and term_file.exists():
        for line in term_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=>" not in line:
                continue
            wrong, right = [part.strip() for part in line.split("=>", 1)]
            if wrong and right:
                replacements.append((wrong, right))
    return replacements


def clean_text(text: str, term_file: Path | None = None) -> str:
    opencc = require_import("opencc", "opencc-python-reimplemented")
    converter = opencc.OpenCC("t2s")
    cleaned = converter.convert(text)
    cleaned = cleaned.replace("\u3000", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    for wrong, right in load_replacements(term_file):
        cleaned = cleaned.replace(wrong, right)
    return cleaned.strip() + "\n"


def segment_text(result: dict[str, Any]) -> str:
    if result.get("segments"):
        return "\n".join((seg.get("text") or "").strip() for seg in result["segments"] if (seg.get("text") or "").strip())
    return (result.get("text") or "").strip()


def format_time(seconds: float | int | None) -> str:
    value = float(seconds or 0)
    minutes = int(value // 60)
    secs = value % 60
    return f"{minutes:02d}:{secs:05.2f}"


def segments_markdown(result: dict[str, Any], term_file: Path | None = None) -> str:
    lines = ["# Clean Transcript Segments", ""]
    for seg in result.get("segments") or []:
        text = clean_text((seg.get("text") or "").strip(), term_file).strip()
        if not text:
            continue
        lines.append(f"- [{format_time(seg.get('start'))} - {format_time(seg.get('end'))}] {text}")
    return "\n".join(lines).strip() + "\n"


def transcribe(audio_path: Path, model: str, initial_prompt: str | None, language: str | None = "zh") -> dict[str, Any]:
    mlx_whisper = require_import("mlx_whisper", "mlx-whisper")
    kwargs = {
        "path_or_hf_repo": model,
        "verbose": False,
        "initial_prompt": initial_prompt,
        "word_timestamps": False,
    }
    if language and language != "auto":
        kwargs["language"] = language
    return mlx_whisper.transcribe(str(audio_path), **kwargs)


def clean_caption_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_vtt_time(value: str) -> float:
    parts = value.strip().split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    return float(parts[0])


def parse_vtt(path: Path) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "-->" not in line:
            i += 1
            continue
        start_raw, end_raw = [part.strip().split()[0] for part in line.split("-->", 1)]
        i += 1
        text_lines = []
        while i < len(lines) and lines[i].strip():
            if not re.match(r"^(<c>|</c>|align:|position:)", lines[i].strip()):
                text_lines.append(lines[i])
            i += 1
        text = clean_caption_text(" ".join(text_lines))
        if text:
            segments.append({"start": parse_vtt_time(start_raw), "end": parse_vtt_time(end_raw), "text": text})
        i += 1
    return segments


def result_to_segments(result: dict[str, Any]) -> list[dict[str, Any]]:
    segments = []
    for seg in result.get("segments") or []:
        text = clean_caption_text(seg.get("text") or "")
        if text:
            segments.append({"start": float(seg.get("start") or 0), "end": float(seg.get("end") or 0), "text": text})
    if not segments and result.get("text"):
        segments.append({"start": 0.0, "end": 0.0, "text": clean_caption_text(result["text"])})
    return segments


def write_transcript_artifacts(
    out_dir: Path,
    slug: str,
    segments: list[dict[str, Any]],
    transcript_json: Path | None = None,
    asr_result: dict[str, Any] | None = None,
    term_file: Path | None = None,
) -> dict[str, str]:
    raw_text = "\n".join(seg["text"] for seg in segments if seg.get("text")).strip() + "\n"
    transcript_txt = out_dir / f"{slug}_transcript_turbo.txt"
    clean_txt = out_dir / f"{slug}_transcript_turbo_clean.txt"
    clean_segments = out_dir / f"{slug}_segments_clean.md"
    if transcript_json and asr_result is not None:
        write_json(transcript_json, asr_result)
    transcript_txt.write_text(raw_text, encoding="utf-8")
    clean_txt.write_text(clean_text(raw_text, term_file), encoding="utf-8")
    clean_segments.write_text(segments_markdown({"segments": segments}, term_file), encoding="utf-8")
    artifacts = {
        "transcript_txt": str(transcript_txt),
        "transcript_clean_txt": str(clean_txt),
        "segments_clean_md": str(clean_segments),
    }
    if transcript_json:
        artifacts["transcript_json"] = str(transcript_json)
    return artifacts


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def resolve_term_file(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"Term file not found: {path}")
    return path


def parse_douyin(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    video_id = extract_video_id(args.url)
    eprint(f"Video id: {video_id}")

    router_data, share_url = fetch_router_data(video_id)
    item = first_video_item(router_data)
    play_urls = (((item.get("video") or {}).get("play_addr") or {}).get("url_list") or [])
    if not play_urls:
        raise SystemExit("Could not find video.play_addr.url_list[0].")
    play_url = play_urls[0]
    candidate_play_urls = play_url_candidates(play_url)

    desc = item.get("desc") or ""
    author = ((item.get("author") or {}).get("nickname")) or ""
    duration_ms = ((item.get("video") or {}).get("duration")) or None
    slug = f"douyin_{video_id}"
    video_path = out_dir / f"{slug}.mp4"
    audio_path = out_dir / f"{slug}_audio.mp3"
    transcript_json = out_dir / f"{slug}_transcript_turbo.json"
    transcript_txt = out_dir / f"{slug}_transcript_turbo.txt"
    clean_txt = out_dir / f"{slug}_transcript_turbo_clean.txt"
    clean_segments = out_dir / f"{slug}_segments_clean.md"
    metadata_json = out_dir / f"{slug}_metadata.json"

    metadata = {
        "episode": args.episode,
        "video_id": video_id,
        "source_url": args.url,
        "mobile_share_url": share_url,
        "description": desc,
        "safe_description": safe_filename(desc, video_id),
        "author": author,
        "duration_ms": duration_ms,
        "play_url": play_url,
        "play_url_candidates": candidate_play_urls,
        "watermark_policy": "prefer /play/ no-watermark URL when the share page gives /playwm/, fallback to original URL",
        "model": args.model,
        "term_file": str(resolve_term_file(args.term_file)) if args.term_file else None,
        "artifacts": {
            "video": str(video_path),
            "audio": str(audio_path),
            "transcript_json": str(transcript_json),
            "transcript_txt": str(transcript_txt),
            "transcript_clean_txt": str(clean_txt),
            "segments_clean_md": str(clean_segments),
        },
    }
    write_json(metadata_json, metadata)

    ffmpeg_path = ensure_ffmpeg_bin(out_dir)
    os.environ["PATH"] = f"{ffmpeg_path.parent}{os.pathsep}{os.environ.get('PATH', '')}"
    downloaded_url = download_file(candidate_play_urls, video_path, args.force)
    metadata["downloaded_play_url"] = downloaded_url
    metadata["downloaded_without_playwm"] = "/playwm/" not in downloaded_url
    write_json(metadata_json, metadata)
    extract_audio(video_path, audio_path, ffmpeg_path, args.force)

    if args.skip_asr:
        eprint("Skip ASR requested.")
        return metadata

    if transcript_json.exists() and transcript_json.stat().st_size > 0 and not args.force:
        eprint(f"Reuse existing transcript: {transcript_json}")
        result = json.loads(transcript_json.read_text(encoding="utf-8"))
    else:
        result = transcribe(audio_path, args.model, args.initial_prompt, language=args.language)
        write_json(transcript_json, result)

    raw_text = segment_text(result).strip() + "\n"
    transcript_txt.write_text(raw_text, encoding="utf-8")
    term_file = resolve_term_file(args.term_file)
    clean_txt.write_text(clean_text(raw_text, term_file), encoding="utf-8")
    clean_segments.write_text(segments_markdown(result, term_file), encoding="utf-8")
    write_json(metadata_json, metadata)

    return metadata


def best_vtt_file(out_dir: Path, slug: str) -> Path | None:
    preferred = []
    for pattern in [
        f"{slug}.zh*.vtt",
        f"{slug}*.zh*.vtt",
        f"{slug}.en*.vtt",
        f"{slug}*.en*.vtt",
        f"{slug}*.vtt",
    ]:
        preferred.extend(sorted(out_dir.glob(pattern)))
    seen = set()
    for path in preferred:
        if path not in seen and path.exists() and path.stat().st_size > 0:
            return path
        seen.add(path)
    return None


def parse_youtube(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ytdlp = ytdlp_cmd()

    meta_cmd = ytdlp + [
        "--ignore-config",
        "--dump-json",
        "--no-warnings",
        "--skip-download",
        "--write-subs",
        "--write-auto-subs",
        "--sub-format",
        "vtt",
        "--sub-langs",
        args.sub_langs,
        "-o",
        str(out_dir / "youtube_%(id)s.%(ext)s"),
        args.url,
    ]
    meta_result = subprocess.run(meta_cmd, text=True, capture_output=True, check=False)
    if meta_result.returncode != 0:
        raise SystemExit(meta_result.stderr.strip() or "yt-dlp failed while reading YouTube metadata")
    metadata_raw = json.loads(meta_result.stdout.splitlines()[-1])
    video_id = metadata_raw.get("id") or safe_filename(args.url, "unknown")
    slug = f"youtube_{video_id}"

    transcript_json = out_dir / f"{slug}_transcript_turbo.json"
    metadata_json = out_dir / f"{slug}_metadata.json"
    audio_path = out_dir / f"{slug}_audio.mp3"
    video_path = out_dir / f"{slug}.mp4"

    subtitle_status = "not_attempted"
    subtitle_path = None
    segments: list[dict[str, Any]] = []
    if not args.force:
        existing = best_vtt_file(out_dir, slug)
        if existing:
            subtitle_path = existing
            segments = parse_vtt(existing)
            subtitle_status = "reused_existing_vtt"

    if not segments:
        subtitle_cmd = ytdlp + [
            "--ignore-config",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-format",
            "vtt",
            "--sub-langs",
            args.sub_langs,
            "-o",
            str(out_dir / f"{slug}.%(ext)s"),
            args.url,
        ]
        subtitle_result = subprocess.run(subtitle_cmd, text=True, capture_output=True, check=False)
        if subtitle_result.returncode == 0:
            subtitle_path = best_vtt_file(out_dir, slug)
            if subtitle_path:
                segments = parse_vtt(subtitle_path)
                subtitle_status = "downloaded"
        else:
            subtitle_status = "failed: " + (subtitle_result.stderr.strip() or subtitle_result.stdout.strip())[-600:]

    artifacts: dict[str, str] = {}
    caption_source = "youtube_subtitles_or_auto_captions"
    if segments:
        artifacts.update(write_transcript_artifacts(out_dir, slug, segments, term_file=resolve_term_file(args.term_file)))
    elif args.skip_asr:
        eprint("Skip ASR requested and no subtitles were available.")
    else:
        ffmpeg_path = ensure_ffmpeg_bin(out_dir)
        os.environ["PATH"] = f"{ffmpeg_path.parent}{os.pathsep}{os.environ.get('PATH', '')}"
        audio_cmd = ytdlp + [
            "--ignore-config",
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "64K",
            "-o",
            str(out_dir / f"{slug}_audio.%(ext)s"),
            args.url,
        ]
        audio_result = subprocess.run(audio_cmd, text=True, capture_output=True, check=False)
        if audio_result.returncode != 0:
            raise SystemExit(audio_result.stderr.strip() or "yt-dlp failed while downloading YouTube audio for ASR")
        audio_files = sorted(out_dir.glob(f"{slug}_audio*.mp3"))
        if audio_files:
            audio_path = audio_files[0]
        asr_result = transcribe(audio_path, args.model, args.initial_prompt, language=args.language)
        segments = result_to_segments(asr_result)
        artifacts.update(write_transcript_artifacts(out_dir, slug, segments, transcript_json, asr_result, resolve_term_file(args.term_file)))
        artifacts["audio"] = str(audio_path)
        caption_source = "local_asr_fallback"

    if args.download_video:
        video_cmd = ytdlp + [
            "--ignore-config",
            "-f",
            "bv*+ba/b",
            "--merge-output-format",
            "mp4",
            "-o",
            str(out_dir / f"{slug}.%(ext)s"),
            args.url,
        ]
        video_result = subprocess.run(video_cmd, text=True, capture_output=True, check=False)
        if video_result.returncode == 0 and video_path.exists():
            artifacts["video"] = str(video_path)
        elif video_result.returncode != 0:
            eprint("Video download failed; transcript artifacts were kept: " + (video_result.stderr.strip() or video_result.stdout.strip())[-600:])

    if subtitle_path:
        artifacts["subtitle_vtt"] = str(subtitle_path)

    metadata = {
        "platform": "youtube",
        "video_id": video_id,
        "source_url": args.url,
        "title": metadata_raw.get("title") or "",
        "description": metadata_raw.get("description") or "",
        "author": metadata_raw.get("uploader") or metadata_raw.get("channel") or "",
        "duration": metadata_raw.get("duration"),
        "published_at": metadata_raw.get("upload_date"),
        "metrics": {
            "views": metadata_raw.get("view_count"),
            "likes": metadata_raw.get("like_count"),
            "comments": metadata_raw.get("comment_count"),
        },
        "caption_source": caption_source,
        "subtitle_status": subtitle_status,
        "segments": segments,
        "model": args.model,
        "term_file": str(resolve_term_file(args.term_file)) if args.term_file else None,
        "artifacts": artifacts,
        "watermark_policy": "Use screenshots only after visual review; if platform UI, subtitles, creator marks, or watermarks remain, generate original concept images instead.",
    }
    write_json(metadata_json, metadata)
    metadata["artifacts"]["metadata_json"] = str(metadata_json)
    write_json(metadata_json, metadata)
    return metadata


def parse_bilibili(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    ytdlp = ytdlp_cmd()

    meta_cmd = ytdlp + [
        "--ignore-config",
        "--dump-json",
        "--no-warnings",
        "--skip-download",
        "--no-playlist",
        args.url,
    ]
    meta_result = subprocess.run(meta_cmd, text=True, capture_output=True, check=False)
    if meta_result.returncode != 0:
        raise SystemExit(meta_result.stderr.strip() or "yt-dlp failed while reading Bilibili metadata")
    metadata_raw = json.loads(meta_result.stdout.splitlines()[-1])
    video_id = metadata_raw.get("id") or metadata_raw.get("display_id") or safe_filename(args.url, "unknown")
    slug = f"bilibili_{video_id}"

    transcript_json = out_dir / f"{slug}_transcript_turbo.json"
    metadata_json = out_dir / f"{slug}_metadata.json"
    audio_path = out_dir / f"{slug}_audio.mp3"
    video_path = out_dir / f"{slug}.mp4"

    subtitle_status = "not_attempted"
    subtitle_path = None
    segments: list[dict[str, Any]] = []
    if not args.force:
        existing = best_vtt_file(out_dir, slug)
        if existing:
            subtitle_path = existing
            segments = parse_vtt(existing)
            subtitle_status = "reused_existing_vtt"

    if not segments:
        subtitle_cmd = ytdlp + [
            "--ignore-config",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-format",
            "vtt",
            "--sub-langs",
            args.sub_langs,
            "--no-playlist",
            "-o",
            str(out_dir / f"{slug}.%(ext)s"),
            args.url,
        ]
        subtitle_result = subprocess.run(subtitle_cmd, text=True, capture_output=True, check=False)
        if subtitle_result.returncode == 0:
            subtitle_path = best_vtt_file(out_dir, slug)
            if subtitle_path:
                segments = parse_vtt(subtitle_path)
                subtitle_status = "downloaded"
            else:
                subtitle_status = "not_available"
        else:
            subtitle_status = "failed: " + (subtitle_result.stderr.strip() or subtitle_result.stdout.strip())[-600:]

    artifacts: dict[str, str] = {}
    caption_source = "bilibili_subtitles_or_auto_captions"
    if segments:
        artifacts.update(write_transcript_artifacts(out_dir, slug, segments, term_file=resolve_term_file(args.term_file)))
    elif args.skip_asr:
        eprint("Skip ASR requested and no subtitles were available.")
    else:
        ffmpeg_path = ensure_ffmpeg_bin(out_dir)
        os.environ["PATH"] = f"{ffmpeg_path.parent}{os.pathsep}{os.environ.get('PATH', '')}"
        audio_cmd = ytdlp + [
            "--ignore-config",
            "-f",
            "ba/bestaudio/b",
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "64K",
            "--no-playlist",
            "-o",
            str(out_dir / f"{slug}_audio.%(ext)s"),
            args.url,
        ]
        audio_result = subprocess.run(audio_cmd, text=True, capture_output=True, check=False)
        if audio_result.returncode != 0:
            raise SystemExit(audio_result.stderr.strip() or "yt-dlp failed while downloading Bilibili audio for ASR")
        audio_files = sorted(out_dir.glob(f"{slug}_audio*.mp3"))
        if audio_files:
            audio_path = audio_files[0]
        asr_result = transcribe(audio_path, args.model, args.initial_prompt, language=args.language)
        segments = result_to_segments(asr_result)
        artifacts.update(write_transcript_artifacts(out_dir, slug, segments, transcript_json, asr_result, resolve_term_file(args.term_file)))
        artifacts["audio"] = str(audio_path)
        caption_source = "local_asr_fallback"

    if args.download_video:
        video_cmd = ytdlp + [
            "--ignore-config",
            "-f",
            "bv*+ba/b",
            "--merge-output-format",
            "mp4",
            "--no-playlist",
            "-o",
            str(out_dir / f"{slug}.%(ext)s"),
            args.url,
        ]
        video_result = subprocess.run(video_cmd, text=True, capture_output=True, check=False)
        if video_result.returncode == 0 and video_path.exists():
            artifacts["video"] = str(video_path)
        elif video_result.returncode != 0:
            eprint("Video download failed; transcript artifacts were kept: " + (video_result.stderr.strip() or video_result.stdout.strip())[-600:])

    if subtitle_path:
        artifacts["subtitle_vtt"] = str(subtitle_path)

    metadata = {
        "platform": "bilibili",
        "video_id": video_id,
        "source_url": args.url,
        "title": metadata_raw.get("title") or "",
        "description": metadata_raw.get("description") or "",
        "author": metadata_raw.get("uploader") or "",
        "duration": metadata_raw.get("duration"),
        "published_at": metadata_raw.get("upload_date") or metadata_raw.get("timestamp"),
        "metrics": {
            "views": metadata_raw.get("view_count"),
            "likes": metadata_raw.get("like_count"),
            "comments": metadata_raw.get("comment_count"),
        },
        "caption_source": caption_source,
        "subtitle_status": subtitle_status,
        "segments": segments,
        "model": args.model,
        "term_file": str(resolve_term_file(args.term_file)) if args.term_file else None,
        "artifacts": artifacts,
        "watermark_policy": "Bilibili screenshots must be visually reviewed; avoid frames with platform UI, embedded subtitles, creator marks, or watermarks.",
    }
    write_json(metadata_json, metadata)
    metadata["artifacts"]["metadata_json"] = str(metadata_json)
    write_json(metadata_json, metadata)
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and transcribe a Douyin, YouTube, or Bilibili video.")
    parser.add_argument("url", nargs="?", help="Douyin/YouTube/Bilibili URL or raw Douyin/Bilibili video id.")
    parser.add_argument("--platform", choices=["auto", "douyin", "youtube", "bilibili"], default="auto")
    parser.add_argument("--episode", type=int, help="Episode number for metadata.")
    parser.add_argument("--out-dir", default=".", help="Output directory.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="MLX Whisper model repo/path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing video/audio/transcript artifacts.")
    parser.add_argument("--skip-asr", action="store_true", help="Download metadata/subtitles/audio only; do not run ASR fallback.")
    parser.add_argument("--download-video", action="store_true", help="Also download an MP4 for later frame extraction when supported.")
    parser.add_argument("--check", action="store_true", help="Check Python dependencies and exit.")
    parser.add_argument("--sub-langs", default="zh.*,en.*", help="YouTube subtitle language selector passed to yt-dlp.")
    parser.add_argument("--language", default="auto", help="ASR language, e.g. zh, en, or auto.")
    parser.add_argument("--term-file", help="Optional UTF-8 term replacement file. Lines use wrong=>right.")
    parser.add_argument(
        "--initial-prompt",
        default=None,
        help="Prompt text passed to Whisper to improve name recognition.",
    )
    args = parser.parse_args()

    if args.check:
        return check_dependencies()
    if not args.url:
        parser.error("url is required unless --check is used")

    platform = platform_from_url(args.url) if args.platform == "auto" else args.platform
    if platform == "douyin":
        if args.language == "auto":
            args.language = "zh"
        metadata = parse_douyin(args)
    elif platform == "youtube":
        metadata = parse_youtube(args)
    elif platform == "bilibili":
        if args.language == "auto":
            args.language = "zh"
        metadata = parse_bilibili(args)
    else:
        raise SystemExit(f"Unsupported platform: {platform}")

    print(json.dumps(metadata, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
