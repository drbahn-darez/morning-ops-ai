#!/usr/bin/env bash
# Normalize a video for Instagram Reels API upload.
#   tools/reels/prepare.sh input.mp4 [output.mp4]
# Output: 1080x1920 (9:16, padded if needed), H.264 High yuv420p 30fps closed GOP,
# AAC 48 kHz stereo 128k, moov atom first (+faststart). Fails if > 300 MB or not 3s-15min.
set -euo pipefail
in="${1:?usage: prepare.sh input.mp4 [output.mp4]}"
out="${2:-${in%.*}.ig.mp4}"

ffmpeg -y -hide_banner -loglevel error -i "$in" \
  -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black,fps=30,format=yuv420p" \
  -c:v libx264 -profile:v high -preset medium -crf 20 -maxrate 20M -bufsize 40M -g 60 -keyint_min 60 -sc_threshold 0 \
  -c:a aac -ar 48000 -ac 2 -b:a 128k \
  -movflags +faststart "$out"

dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")
size=$(stat -c %s "$out" 2>/dev/null || stat -f %z "$out")
awk -v d="$dur" 'BEGIN { if (d < 3 || d > 900) { printf "duration %.1fs outside 3s-15min\n", d; exit 1 } }'
if [ "$size" -gt $((300 * 1024 * 1024)) ]; then echo "file is over 300 MB" >&2; exit 1; fi
awk -v d="$dur" 'BEGIN { if (d > 180) print "warning: over 3 min — not recommended to non-followers" > "/dev/stderr" }'
echo "$out"
