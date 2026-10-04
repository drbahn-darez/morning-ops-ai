#!/usr/bin/env bash
# Normalize a video for Instagram Reels API upload.
#   tools/reels/prepare.sh input.mp4 [output.mp4] [crop|pad]
# Output: 1080x1920 (9:16; non-9:16 sources are center-cropped by default, or padded with "pad"),
# H.264 High yuv420p 30fps closed GOP, AAC-LC 48 kHz stereo 128k, moov atom first (+faststart),
# no MP4 edit lists (Meta spec: "no edit lists"). Fails if > 300 MB or outside 3 s - 15 min.
set -euo pipefail
in="${1:?usage: prepare.sh input.mp4 [output.mp4] [crop|pad]}"
out="${2:-${in%.*}.ig.mp4}"
fit="${3:-crop}"

case "$fit" in
  crop) vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" ;;
  pad)  vf="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" ;;
  *) echo "fit must be crop or pad" >&2; exit 2 ;;
esac

ffmpeg -y -hide_banner -loglevel error -i "$in" \
  -vf "$vf,fps=30,format=yuv420p" \
  -c:v libx264 -profile:v high -preset medium -crf 19 -maxrate 18M -bufsize 36M \
  -g 60 -keyint_min 60 -sc_threshold 0 -x264-params open-gop=0 \
  -c:a aac -ar 48000 -ac 2 -b:a 128k \
  -movflags +faststart -use_editlist 0 "$out"

dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")
size=$(stat -c %s "$out" 2>/dev/null || stat -f %z "$out")
awk -v d="$dur" 'BEGIN { if (d < 3 || d > 900) { printf "duration %.1fs outside 3s-15min\n", d > "/dev/stderr"; exit 1 } }'
if [ "$size" -gt $((300 * 1024 * 1024)) ]; then echo "file is over 300 MB" >&2; exit 1; fi
awk -v d="$dur" 'BEGIN { if (d > 90) print "warning: over 90 s — flagship 100K attempts should be 20-60 s (max 90 s)" > "/dev/stderr" }'
echo "$out"
