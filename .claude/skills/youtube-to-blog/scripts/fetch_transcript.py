#!/usr/bin/env python3
"""Fetch a YouTube video's metadata and English captions, and write a clean transcript.

Usage: fetch_transcript.py <youtube-url> <out-dir> [--chunk-seconds 30]

Writes to <out-dir>:
  metadata.json   title, channel, upload_date, duration, url, description, chapters
  transcript.md   de-duplicated captions grouped into ~30s paragraphs with [hh:mm:ss] stamps,
                  with chapter headings inserted when the video has chapters

YouTube auto-captions repeat each line across rolling cues and embed per-word timing tags;
this strips both so the transcript is readable at roughly 1/10th of the raw VTT size.
Requires yt-dlp on PATH.
"""
import argparse
import glob
import html
import json
import os
import re
import subprocess
import sys

CUE_TIME = re.compile(r"^(\d+):(\d\d):(\d\d)\.\d+\s+-->")
TAG = re.compile(r"<[^>]+>")


def run_ytdlp(url, out_dir):
    base = os.path.join(out_dir, "video")
    # Prefer human-written subtitles; fall back to auto-generated ones.
    cmd = [
        "yt-dlp", "--skip-download", "--write-info-json",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", "en,en-US,en-GB,en-orig", "--sub-format", "vtt",
        "-o", base + ".%(ext)s", url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"yt-dlp failed:\n{proc.stderr[-2000:]}")
    return base


def pick_vtt(base, info):
    manual = set((info.get("subtitles") or {}).keys())
    files = glob.glob(base + ".*.vtt")
    if not files:
        sys.exit("No English captions available for this video.")

    def rank(path):
        lang = path[len(base) + 1:-4]
        return (lang not in manual, lang != "en", lang)

    return sorted(files, key=rank)[0]


def parse_vtt(path):
    """Yield (seconds, text_line) with rolling duplicates removed."""
    recent = []
    start = 0
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            m = CUE_TIME.match(line)
            if m:
                h, mi, s = map(int, m.groups())
                start = h * 3600 + mi * 60 + s
                continue
            if not line.strip() or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
                continue
            text = html.unescape(TAG.sub("", line)).strip()
            if not text or text in recent:
                continue
            recent = (recent + [text])[-4:]
            yield start, text


def stamp(sec):
    return f"{sec // 3600:02d}:{sec % 3600 // 60:02d}:{sec % 60:02d}"


def build_transcript(lines, chapters, chunk):
    chapters = sorted(chapters or [], key=lambda c: c["start_time"])
    out, para, para_start, ci = [], [], None, 0

    def flush():
        if para:
            out.append(f"[{stamp(para_start)}] " + " ".join(para) + "\n")

    for sec, text in lines:
        while ci < len(chapters) and sec >= chapters[ci]["start_time"]:
            flush()
            para, para_start = [], None
            out.append(f"\n## {chapters[ci]['title']}  ({stamp(int(chapters[ci]['start_time']))})\n")
            ci += 1
        if para_start is None:
            para_start = sec
        para.append(text)
        if sec - para_start >= chunk and text.endswith((".", "?", "!")):
            flush()
            para, para_start = [], None
    flush()
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out_dir")
    ap.add_argument("--chunk-seconds", type=int, default=30)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    base = run_ytdlp(args.url, args.out_dir)
    with open(base + ".info.json", encoding="utf-8") as f:
        info = json.load(f)
    vtt = pick_vtt(base, info)

    meta = {
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "upload_date": info.get("upload_date"),
        "duration": info.get("duration_string"),
        "url": info.get("webpage_url") or args.url,
        "description": info.get("description"),
        "chapters": [
            {"start": stamp(int(c["start_time"])), "title": c["title"]}
            for c in (info.get("chapters") or [])
        ],
        "captions": os.path.basename(vtt),
    }
    with open(os.path.join(args.out_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    body = build_transcript(parse_vtt(vtt), info.get("chapters"), args.chunk_seconds)
    header = f"# {meta['title']}\n{meta['channel']} · {meta['duration']} · {meta['url']}\n\n"
    with open(os.path.join(args.out_dir, "transcript.md"), "w", encoding="utf-8") as f:
        f.write(header + body)

    manual = vtt[len(base) + 1:-4] in (info.get("subtitles") or {})
    os.remove(base + ".info.json")
    for f in glob.glob(base + ".*.vtt"):
        os.remove(f)
    words = len(body.split())
    print(f"title:      {meta['title']}")
    print(f"channel:    {meta['channel']}  duration: {meta['duration']}  uploaded: {meta['upload_date']}")
    print(f"captions:   {meta['captions']}  ({'manual' if manual else 'auto-generated'})")
    print(f"chapters:   {len(meta['chapters'])}")
    print(f"transcript: {os.path.join(args.out_dir, 'transcript.md')}  ({words} words)")


if __name__ == "__main__":
    main()
