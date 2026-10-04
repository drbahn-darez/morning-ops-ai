# Brief: adro / 2026-10-08 / m4-bumper-creases

## Brief as received (verbatim)

```
slug: m4-bumper-creases
brand: adro
date: 2026-10-08 (Thu) 18:00 PT
format: REELS (30-45 s)
pillar: 1 (AERO PROOF)
hook_id: adro-h16 — "Every crease on this bumper has a job. Here are 3."
hypothesis: an explainer of visible design details on the G8X M4 bumper gets higher average watch time than install timelapses
experiment: first frame = finished car slow cinematic orbit vs close-up of a crease (make two hook variants for Trial Reels)
sources: real footage only — G8X instagram vertical stills and team b-roll from Drive "IG POST" folders; no third-party footage; no performance numbers
CTA: follow for the AOX launch (mid-November)
trial: SS_PERFORMANCE for both hook variants
paid: false.
```

## Hypothesis
A short explainer of three visible design details on the adro front bumper for the BMW M4 (G82) holds viewers longer than an install timelapse. Measure: `ig_reels_avg_watch_time` as seconds and as a percentage of video length (kpi.md). Using the percentage matters because this cut is 30–45 s and install timelapses run up to 60 s.

- Baseline: `data/insta/content-log.jsonl` has no install-timelapse rows yet, so there is nothing to compare against today. The analyst has to pull the comparison set from Insights (instagram-graph or Supermetrics IGI) before calling this.
- The hook is adro-h16 (status `active`, pillar 1). It has never been used (uses 0).

## Experiment: first frame (Trial Reels, 2 variants)
| Variant | 0.0–0.5 s first frame | Everything after 0.5 s |
|---|---|---|
| **A — orbit** | Finished car, slow cinematic orbit, front 3/4, low eye level (team shooting grammar, adro.md) | Identical |
| **B — crease** | Macro close-up of crease 01 under raking light, slow push | Identical |

- Only the first 0.0–3.0 s differs (see reel.md §1). The VO, on-screen hook text and the rest of the cut are shared, so the first frame is the only variable.
- Brand pack rule "first frame = result scene" fits Variant A. Variant B deliberately breaks that rule, and breaking it is what the test measures. Variant B carries a car/part label from 0.0 s so viewers can tell what it is about within 1 second.
- Trial graduation: brief says `SS_PERFORMANCE` for both. This needs explicit human confirmation at publish time (SKILL.md publish step 2: SS_PERFORMANCE only if a human explicitly picks it).

## Sources (verified in Drive on 2026-10-04 by filename/metadata only; contents NOT viewed)
| Use | File | Drive location | Drive ID |
|---|---|---|---|
| Stills for location inserts / cover candidate | G8X instagram vertical_1…_9.jpg (9 files) | …/BMW/G8X/ADRO CUSTOMER/ | folder 1rd99KFXsEZzsZ1SYGM5B2zYSCYP4fHGq |
| Stills for location inserts / cover candidate | G8X instagram vertical-1…-6.jpg (6 files) | …/BMW/G8X/NEW CUSTOMER/ | folder 1JbNOyUISuayIteIymh8Ei7b5rPPijQL3 |
| Orbit b-roll candidate | G8X Bumper teaser.MP4 (6 MB, 2025-12-10) | parent 1wYH84b5C0Go81bcLXLctbO3v_hoZJe80 | 1ue4jS-ezY4CSEFdl_tKm-c6xDP4q19TQ |
| Orbit b-roll candidate (raw) | BMW G82 .mp4 (8.7 GB, 2024-10-16) | parent 19oejtYbqM6LuL8zq_6BZfVmmAE4fUs4g | 10yK_keUWrXggcIAQyN1kSYTEQLtRvgwr |
| **Fact source for the 3 crease jobs** (check) | G8X BUMPER DESIGN VLOG.mp4 (4.6 GB, 2026-06-20) | …/FINAL VIDEO/ | 1XgKByY3NMNFqVc2vkZ-vjFlcLxH5khLs |
| Product photos (2023) | Original images / Final images | …/M3 M4 (G8X) Bumper/ | folder 1Dv_RR-pX03eHu2EyzfMwJUHIz4RQJxa3 |
| Product facts | [DONE] G8X M3/M4 Front Bumper & Aero Kit Catalog.pptx | Drive | 1e4E08GQm1-J_Il_1apPKXjCtUVpd5NdA |

- **"IG POST" folders**: Drive has at least 5 folders named `IG POST`. Their parents are `GT3_Air Intake & Air Outlets` (under `992.2 GT3 (2024+)`), `992.2 GT3 (2024+)`, `GR Supra Widebody`, and two `SOCIAL MEDIA` folders. None is identifiably G8X. The G8X vertical stills sit under `BMW/G8X/ADRO CUSTOMER` and `BMW/G8X/NEW CUSTOMER` instead. The two `SOCIAL MEDIA/IG POST` folders were not opened (1rdceeUHsyHH2E8BJn4D6MvA1DVaskbiY, 1qUbX8G8lcmsc-LQGoEUMhKJj5Ficzub0). The editor should check them for G8X b-roll.
- **Do not use**: `BMW G8X M3_M4 Facelift Bumper & Aero Kit _ ADRO.mp4` (1dR1eV…). Its filename looks like a platform download, and production-spec says not to re-upload downloads from YouTube/TikTok. Use the original master if one exists.
- Product facts from the catalog (2022 catalog, last modified 2024-07): front bumper SKU A14A11-2101, **material TPO**. The front lip is wet carbon fiber. These facts are used only to avoid errors (see TODO 3). No numbers from the catalog appear in the content.

## Open TODOs (must be closed before review can APPROVE)
1. **The three creases and their jobs are unknown.** Neither the brand pack nor any document found in Drive says what specific creases on this bumper do. The design team has to supply, for each of the 3 creases: (a) location on the bumper, (b) a short name, (c) a one-sentence purpose in design-intent language ("shaped to…", "guides air toward…"). No measured outcomes, no %, no "reduces drag/improves cooling by…". Any outcome claim needs `evidence_ids` and an on-screen condition line (compliance.md §5). Check first whether `G8X BUMPER DESIGN VLOG.mp4` already covers this. The renderer example `tools/carousel/examples/adro-sample.json` (intake / edge / canard) is sample copy, **not** a source. Do not lift it.
2. **Which bumper version?** Drive has "FRONT BUMPER V1" (A14A11-2101), "G8X Facelift Bumper" naming, and `V1 vs V2 Draft 1.mp4`. The footage, the script and the caption must all show the same version.
3. **Material wording**: the brand-pack keyword example "BMW M4 G82 carbon front bumper" conflicts with the catalog ("TPO FRONT BUMPER"). The caption says "front bumper" without "carbon". Add "carbon" only for parts that are actually carbon (e.g. the front lip) and visible in the cut.
4. **Customer cars**: the vertical stills sit in folders named `ADRO CUSTOMER` / `NEW CUSTOMER`. Before use, confirm owner consent and check plates and faces (brand-pack collab standard: portrait rights, commercial-use rights).
5. **VO talent**: the brief does not name one. Recommended: a team designer's original voice. TTS is for drafts only (production-spec).
6. **Cover image**: `cover.json` currently renders on the brand background without a photo, because the Drive stills could not be viewed or downloaded in this session. Export the chosen still locally, set `slides[0].image`, and re-render.
7. **AOX launch timing**: the brief and the brand pack both say mid-November, and the brand pack also lists "AOX launch date confirmed" as a gate. Confirm "mid-November" may be stated publicly on 2026-10-08.
8. If the chosen car is fitted with the G82 wide-body kit, the Korean caption lines will trigger the tuning-approval FLAG (compliance.md §6). Prefer a car fitted with the bumper only.
