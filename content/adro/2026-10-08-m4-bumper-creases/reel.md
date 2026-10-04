# Reel: Every crease on this bumper has a job. Here are 3.

- Brand: adro (@adro.inc) · Pillar 1 AERO PROOF · Hook adro-h16
- Format: Reels, 1080×1920 (9:16), target **38 s** (brief limit: 30–45 s)
- Publish: 2026-10-08 18:00 PT, as two Trial Reels (Variant A orbit / Variant B crease). The variants differ only in 0.0–3.0 s.
- Language: English on screen, in subtitles and in the VO. Korean lines appear only at the end of the caption.
- Sound-on design: the VO carries the story. Subtitles are always burned in.
- Placeholders marked `[TODO …]` are waiting on the design team (brief.md TODO 1). Nothing in them is a claim yet.

## 1. Hook, 0.0–3.0 s (two variants)

| t (s) | Variant A: orbit | Variant B: crease | On-screen text (both) | VO (both) |
|---|---|---|---|---|
| 0.0–0.5 | Finished car with the adro front bumper. Slow cinematic orbit around the front 3/4, low eye level, light falling on the bumper, wheels aligned. Already moving at frame 1. | Macro on crease 01 under raking light, slow push along the line. Already moving at frame 1. | Small label, top (y ≈ 300): `BMW M4 G82 · FRONT BUMPER` | (VO starts at 0.3) |
| 0.5–1.5 | Orbit continues toward the bumper. | Push continues, the line catches the light. | Large, centered: `Every crease has a job.` | "Every crease on this bumper has a job." |
| 1.5–3.0 | Orbit settles on a straight-on front view of the bumper. | Rack focus out to reveal more of the bumper. | `Here are 3.` + three empty markers `01 02 03` | "Here are three." |

The 1-second rule: Variant B's macro frame alone does not show what the video is about, so the car/part label must be visible from frame 1 in both variants.

## 2. Timeline (shared after 3.0 s)

| t (s) | Scene | Visual | On-screen text | VO / subtitle |
|---|---|---|---|---|
| 3.0–5.0 | Map | Straight-on front of the bumper. Three thin red lines (#E1251B) draw onto the three creases in order, each tagged 01 / 02 / 03. | `01` `02` `03` beside each line | "Watch where each line goes." |
| 5.0–13.0 | Crease 01 | 1) Location insert (still from the G8X vertical set, slow push, red line on crease 01). 2) Macro tracking shot along crease 01 (slider or gimbal). 3) Hold on the end of the line. | `01 · [TODO crease 01 name]` / `[TODO job, max 6 words]` | "[TODO crease 01 VO, max 20 words, design-intent language]" |
| 13.0–21.0 | Crease 02 | Same pattern: location insert, macro track, hold. | `02 · [TODO crease 02 name]` / `[TODO job, max 6 words]` | "[TODO crease 02 VO, max 20 words]" |
| 21.0–29.0 | Crease 03 | Same pattern. Put the most surprising of the three here; it is the payoff. | `03 · [TODO crease 03 name]` / `[TODO job, max 6 words]` | "[TODO crease 03 VO, max 20 words]" |
| 29.0–33.0 | Payoff | Pull back to the full car. All three red lines light at once, and the orbit resumes. | `Three lines. Three jobs.` | "Three lines. Three jobs." |
| 33.0–38.0 | CTA | Slow orbit continues. The last frame matches Variant A's first frame so the reel loops. | `Next: AOX, our aero CFD software` / `Launching mid-November · Follow @adro.inc` | "Next up: AOX, our aero CFD software. It launches mid-November. Follow so you don't miss it." |

Rules for filling the TODO slots (brief.md TODO 1):
- One crease per scene, one message per scene.
- Write the job as design intent ("shaped to…", "guides air toward…", "keeps the line of the OEM hood running into…"). Do not write measured outcomes.
- No numbers, percentages or comparisons with the OEM part. If the design team wants an outcome claim, it needs `evidence_ids` and an on-screen condition line held for at least 2 s (compliance.md §5). Re-run the compliance check after filling.
- Every on-screen job line must match the VO.

## 3. On-screen text and subtitle spec
- Safe zone: all text inside x 65–1015, y 269–1248. Nothing near the bottom-right button column.
- Hook line: Inter Tight 900, about 96 px, white, one line per phrase.
- Labels and markers: JetBrains Mono, 34 px, red #E1251B.
- Burned-in subtitles: Inter Tight 800, 64 px, white with a 5 px dark outline. At most 2 lines (about 32 characters per line in English). The bottom of the subtitle block must sit at or above y 1240.
- Hold every on-screen job line for at least 2 s.
- Keep the adro logo small and only at the end. No other platform's logos or watermarks.

## 4. Shot list and footage sources (real footage only)

| # | Shot | Used in | Source | Status |
|---|---|---|---|---|
| S1 | Slow cinematic orbit, front 3/4, low eye level, vertical, light on the bumper | A 0.0–3.0, 29–38 | Team b-roll: Drive `G8X Bumper teaser.MP4`; raw `BMW G82 .mp4`. Also check the two `SOCIAL MEDIA/IG POST` folders. | Not checked whether a usable vertical orbit exists. If none does, shoot one with the team grammar (adro.md: slow orbit, vertical, car placed in the light, wheels aligned, low eye level). |
| S2 | Macro of crease 01 under raking light, slow push | B 0.0–3.0, 5–13 | New shoot (no confirmed macro b-roll found in Drive) | TODO |
| S3 | Macro tracking shots along creases 02 and 03 | 13–29 | New shoot | TODO |
| S4 | Straight-on front of the bumper, static, for the 3-line map | 3–5 | Drive stills `G8X instagram vertical_1…_9.jpg` (BMW/G8X/ADRO CUSTOMER) or `vertical-1…-6.jpg` (BMW/G8X/NEW CUSTOMER), or a frame from S1 | Pick the frame. Check owner consent and plates (customer cars). |
| S5 | Location inserts for each crease (slow push on a still) | 5–29 | Same G8X vertical stills | Same consent check |
| Ref | Design explanation of the creases | script | Drive `G8X BUMPER DESIGN VLOG.mp4` (FINAL VIDEO folder) | Check whether a designer explains these creases there. If so, use it as the fact source, and its VO bites may be cut in (adro's own footage). |

Do not use third-party footage, platform downloads, or anything with another app's watermark. No driving shots are planned (`public_road_driving: false`). If driving b-roll is added, set the flag in meta.json and re-run the check.

## 5. Audio
- Lead: original VO recorded clean by a team member (TODO: designer, see brief.md TODO 5). TTS is for the draft animatic only.
- Bed: original ambient sound, or a Meta Sound Collection track added in the edit. If one is added, change `audio_source` to `meta_sound_collection`. Do not burn licensed or trending app music into the master.
- Give each crease a soft tick sound as its red line draws. This is original sound design.

## 6. Cover (cover_url)
- `cover.json` renders to `out/2026-10-08-m4-bumper-creases-cover_01.jpg` (1080×1920; text kept in y 300–1240 so it survives the Reels UI and the 3:4 grid crop).
- Cover copy: eyebrow `BMW M4 G82 · FRONT BUMPER`, title `Every crease has a job.`, sub `Here are 3.`
- TODO: add the chosen G8X still as `image` and re-render (brief.md TODO 6).

## 7. Export
- One clean 9:16 master per variant, then `tools/reels/prepare.sh master.mp4 out.mp4` (H.264 High, 30 fps, AAC 48 kHz, faststart, no edit lists).
- Variant files: `variant-A-orbit.mp4`, `variant-B-crease.mp4`. They are identical after 3.0 s.
