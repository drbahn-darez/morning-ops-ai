#!/usr/bin/env bash
# Normalize a video for Instagram Reels API upload.
#   tools/reels/prepare.sh input.mp4 [output.mp4] [crop|pad]
# Output: 1080x1920 (9:16; non-9:16 sources are center-cropped by default, or padded with "pad"),
# H.264 High yuv420p SDR BT.709, 30fps closed GOP, AAC-LC 48 kHz stereo 128k, moov atom first
# (+faststart), no MP4 edit lists (Meta spec: "no edit lists"). HDR (HLG/PQ, e.g. iPhone) is
# tone-mapped to SDR. Fails before encoding if the source is outside 3 s - 15 min; the output
# file only appears when every check passes.
set -euo pipefail
in="${1:?usage: prepare.sh input.mp4 [output.mp4] [crop|pad]}"
out="${2:-${in%.*}.ig.mp4}"
fit="${3:-crop}"

case "$fit" in
  crop) geo="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" ;;
  pad)  geo="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black" ;;
  *) echo "fit must be crop or pad" >&2; exit 2 ;;
esac

src_dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
awk -v d="$src_dur" 'BEGIN { if (d < 3 || d > 900) { printf "source duration %.1fs outside 3s-15min\n", d > "/dev/stderr"; exit 1 } }'

trc=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer -of csv=p=0 "$in" || true)
case "$trc" in
  smpte2084|arib-std-b67)
    # HDR -> SDR BT.709 (iPhone HLG/PQ). Without this the 8-bit output keeps HDR tags and washes out.
    tone="zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv," ;;
  *) tone="" ;;
esac

tmp="${out%.*}.part.mp4"
trap 'rm -f "$tmp"' EXIT
ffmpeg -y -hide_banner -loglevel error -i "$in" \
  -vf "${tone}${geo},fps=30,format=yuv420p" \
  -c:v libx264 -profile:v high -preset medium -crf 19 -maxrate 18M -bufsize 36M \
  -g 60 -keyint_min 60 -sc_threshold 0 -x264-params open-gop=0 \
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
  -c:a aac -ar 48000 -ac 2 -b:a 128k \
  -movflags +faststart -use_editlist 0 "$tmp"

dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$tmp")
size=$(stat -c %s "$tmp" 2>/dev/null || stat -f %z "$tmp")
awk -v d="$dur" 'BEGIN { if (d < 3 || d > 900) { printf "output duration %.1fs outside 3s-15min\n", d > "/dev/stderr"; exit 1 } }'
if [ "$size" -gt $((300 * 1024 * 1024)) ]; then echo "file is over 300 MB" >&2; exit 1; fi
mv "$tmp" "$out"
trap - EXIT
awk -v d="$dur" 'BEGIN { if (d > 90) print "warning: over 90 s — flagship 100K attempts should be 20-60 s (max 90 s)" > "/dev/stderr" }'
echo "$out"
