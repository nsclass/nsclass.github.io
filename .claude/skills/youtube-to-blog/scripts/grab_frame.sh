#!/usr/bin/env bash
# Save one video frame (e.g. a slide with code) as a PNG.
# Usage: grab_frame.sh <youtube-url> <hh:mm:ss> <out.png>
# Downloads only a 2-second clip at <=720p around the timestamp. Needs yt-dlp and ffmpeg.
set -euo pipefail
url="$1"; at="$2"; out="$3"

to_sec() { IFS=: read -r h m s <<<"$1"; echo $((10#$h * 3600 + 10#$m * 60 + 10#$s)); }
start=$(to_sec "$at"); end=$((start + 2))

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

yt-dlp -q --no-warnings \
  -f "bv*[height<=720][ext=mp4]/bv*[height<=720]/bv*" \
  --download-sections "*${start}-${end}" \
  -o "$tmp/clip.%(ext)s" "$url"

ffmpeg -loglevel error -y -i "$tmp"/clip.* -frames:v 1 "$out"
echo "$out"
