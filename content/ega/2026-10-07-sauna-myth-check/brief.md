# Brief: ega / 2026-10-07 / sauna-myth-check

## Brief as received
```
slug: sauna-myth-check
brand: ega
date: 2026-10-07 (Wed) 19:30 KST
format: CAROUSEL (API path, 4:5, 7-8 slides)
pillar: 2 (RECOVERY, CALMLY EXPLAINED)
hook_id: ega-h01 — eyebrow "MYTH CHECK", headline "사우나는 오래 버틸수록 좋을까요?"
hypothesis: a myth-check carousel with a save-worthy checklist earns more sends/saves per reach than our routine posts
experiment: hook type = myth check
CTA: save for your next recovery day; location tag EGA Brain Sauna
trial: n/a (carousel)
paid: false. ai_assets: none (pure typographic cards).
```

## Hypothesis
A myth-check carousel that ends in a checklist people want to save earns higher saves/reach and sends/reach than our routine posts.
- Main metrics: `saved / reach` and `shares / reach` (kpi.md: saves/reach is the main carousel metric, sends/reach drives spread to non-followers).
- Supporting metric: `views / reach` (how often the carousel gets shown again, starting from slide 2).
- Comparison baseline: the median of EGA's routine (non-myth-check) carousels over the last 30 days. **TODO:** no EGA baseline exists in `data/insta/content-log.jsonl` yet, so mark this "collecting data" until there are 4 weeks of posts (playbook.md §4).

## Experiment
- Variable: hook type = `myth_check` (meta `experiment: "hook"`, `experiment_variant: "myth_check"`).
- Held constant: EGA card style (English eyebrow + Korean question headline), deep cobalt cover, pure type cards, 8 slides, single save CTA.

## Production decisions
- 8 slides, 4:5: cover (hook) → 4 myth/routine compare cards → save-worthy checklist → perspective shift → save CTA. This follows the brand-pack flow: relatable question → one-line insight → facts → new perspective → routine CTA.
- Slide 2 ("MYTH 01 / 오래 버틸수록 좋다?") works on its own as a hook for viewers who get the post again starting from slide 2.
- **No numbers, minutes, temperatures, or physiology claims.** No sourced duration or temperature guidance exists in the brand pack or the repo, so the copy uses only feelings and routine words ("편안한 호흡", "개운함", "내 컨디션"). This keeps every slide clear of the `sauna-physiology` FLAG and the evidence requirement.
- Classic sauna myths left out on purpose: "sweating removes toxins" contains words the checker blocks (디톡스/독소/노폐물 = REJECT even when the myth is debunked). "Better for sleep or stress" needs an SCI-level source (FLAG).
- Safety line (pregnancy, heart conditions, after drinking, dizziness) appears on the checklist slide (disclaimer) and in the caption.
- No NMN, drink, or product mentions. This is reach content, kept separate from sales (brand pack: "도달용과 판매용의 분리").

## Open items (TODO, do not invent)
- Instagram handle: **unconfirmed** in the brand pack. `carousel.json` has no `handle`, so the bottom-left of every slide is blank. Once a person confirms it, add `"handle"` to the spec and re-render.
- Location tag "에가 브레인 사우나 / EGA Brain Sauna": location_id is unknown. Set it at publish time (in the app, or via API `location_id`).
- Music: this goes out through the API, so there is no music. Showing in the Reels tab would need a 3:4 version posted from the app with music (production-spec.md); out of scope for this brief.
