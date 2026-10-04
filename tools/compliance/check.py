#!/usr/bin/env python3
"""Rule-based compliance gate for Instagram content (Korean law + Meta rules + brand voice).

    python3 tools/compliance/check.py <package-dir | content.json | caption.txt | "text"> --brand ega|adro [--paid]

Package mode (recommended): pass content/<brand>/<date>-<slug>/ and the checker reads
meta.json, carousel.json, reel.md, reel.*.json, caption.txt and alt.txt together.

meta.json fields the checker understands (all optional):
  format            REELS | CAROUSEL | IMAGE
  product_category  none | general_food | hff | functional_food | special_nutrition |
                    cosmetic | functional_cosmetic | sauna_service | auto_part | saas
  paid, gifted, employee_post        economic tie with a creator/employee (free tickets count)
  on_video_disclosure_start / _end   Reels: '광고' overlay at start and end
  review_id         자율심의 번호 (required for hff / functional_food / special_nutrition)
  evidence_ids      list of substantiation files for numbers / superlatives / certified parts
  ai_assets         list of AI-generated images / video / voice used
  is_ai_generated   Meta AI self-disclosure flag will be set at publish
  ai_persona_role   none | customer | expert | ambassador
  audio_source      original | meta_sound_collection | ig_library | licensed
  audio_license_id, third_party_footage, footage_license_id, public_road_driving, competitor_named

Verdict: REJECT (rewrite before review) > FLAG (human/legal check) > PASS.
Exit code: 2 = REJECT, 1 = FLAG, 0 = PASS, 3 = checker error (treat as REJECT). This is a screening tool, not legal advice.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULES_PATH = Path(__file__).with_name("rules.json")
SEVERITY_ORDER = {"PASS": 0, "FLAG": 1, "REJECT": 2}
SKIP_KEYS = {"image", "video", "id", "brand", "size", "layout", "audio", "format", "handle", "meta"}
REVIEW_REQUIRED = {"hff", "functional_food", "special_nutrition", "special_medical"}
MAX_HASHTAGS, MAX_CAPTION = 5, 2200
BRANDS = {"ega", "adro"}


def collect_text(node, path="$"):
    """Yield (json_path, text) for every string in the content."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in SKIP_KEYS:
                continue
            yield from collect_text(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from collect_text(v, f"{path}[{i}]")


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_package(arg: str) -> tuple[dict, dict]:
    """Return (content, meta). content maps a source name to its parsed content."""
    p = Path(arg)
    try:
        is_dir, exists = p.is_dir(), p.exists()
    except OSError:  # literal caption longer than NAME_MAX bytes
        is_dir = exists = False
    if is_dir:
        meta = _read_json(p / "meta.json") or {}
        content: dict = {}
        for name in ("carousel.json", "cover.json"):
            if (p / name).exists():
                content[name] = _read_json(p / name) or {}
        for f in sorted(p.glob("reel*.json")):
            content[f.name] = _read_json(f) or {}
        for name in ("reel.md", "caption.txt", "alt.txt"):
            if (p / name).exists():
                content[name] = (p / name).read_text(encoding="utf-8")
        return content, meta
    raw = p.read_text(encoding="utf-8") if exists else arg
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"caption.txt": raw}, {}
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    return {p.name if exists else "content": data}, meta


def _hit(sev, rule_id, why, law="", fix="", where="$", match=""):
    return {"severity": sev, "rule": rule_id, "law": law, "why": why, "fix": fix, "where": where, "match": match}


def check(content: dict, brand: str, meta: dict | None = None, paid: bool = False, rules: dict | None = None) -> dict:
    if brand not in BRANDS:
        raise ValueError(f"unknown brand {brand!r}; expected one of {sorted(BRANDS)}")
    rules = rules or json.loads(RULES_PATH.read_text(encoding="utf-8"))
    meta = dict(meta or {})
    if meta.get("brand") and str(meta["brand"]).strip().lower() != brand:
        raise ValueError(f"meta.json brand {meta['brand']!r} does not match --brand {brand!r}")
    if paid:
        meta["paid"] = True
    texts = list(collect_text(content))
    all_text = "\n".join(t for _, t in texts)
    hits: list[dict] = []

    # 1. Regex rules
    for rule in rules["rules"]:
        if rule.get("brands") and brand not in rule["brands"]:
            continue
        if rule.get("when_text") and not re.search(rule["when_text"], all_text, re.IGNORECASE):
            continue
        rx = re.compile(rule["pattern"], re.IGNORECASE)
        unless = re.compile(rule["unless"], re.IGNORECASE) if rule.get("unless") else None
        sev = rule["severity"]
        if rule.get("escalate_when") and re.search(rule["escalate_when"], all_text, re.IGNORECASE):
            sev = "REJECT"
        if sev == "REJECT" and rule.get("downgrade_if_meta") and meta.get(rule["downgrade_if_meta"]):
            sev = "FLAG"
        for path, text in texts:
            for m in rx.finditer(text):
                if unless and unless.search(_sentence(text, m)):
                    continue
                hits.append(_hit(sev, rule["id"], rule["why"], rule.get("law", ""), rule.get("fix", ""), path, m.group(0)))
                break

    # 2. Pre-review for health functional food classes
    if meta.get("product_category") in REVIEW_REQUIRED and not meta.get("review_id"):
        hits.append(_hit("REJECT", "missing-pre-review", "건강기능식품·기능성표시식품·특수영양식품 광고는 자율심의 필수",
                         "식품표시광고법 제10조, 시행규칙 제10조", "심의 번호를 meta.review_id에 넣고 승인 문구 그대로 사용"))

    # 3. Numeric performance claims
    num = rules.get("numeric_claims")
    if num and brand in num.get("brands", [brand]):
        claim_rx = re.compile(num["pattern"], re.IGNORECASE)
        cond_rx = re.compile(num["condition_pattern"], re.IGNORECASE)
        for path, text in texts:
            m = claim_rx.search(text)
            if not m:
                continue
            if not meta.get("evidence_ids"):
                hits.append(_hit("REJECT", "numeric-claim-no-evidence", num["why"], num["law"], num["fix"], path, m.group(0)))
            elif not (cond_rx.search(text) or _sibling_has(content, path, cond_rx)):
                hits.append(_hit("FLAG", "numeric-claim-no-condition", "수치와 같은 장/프레임에 조건 표기가 없음",
                                 num["law"], num["fix"], path, m.group(0)))

    # 4. Disclosure for economic ties
    disc = rules["disclosure"]
    tied = any(meta.get(k) for k in ("paid", "gifted", "employee_post"))
    if tied:
        caption = _caption(content)
        first_line = caption.strip().split("\n", 1)[0] if caption else ""
        head = first_line[: disc.get("head_chars", 30)]
        first_slide = _first_slide_text(content)
        valid = re.compile(disc["valid"])
        in_caption = bool(valid.search(head))
        in_image = bool(re.search(r"광고(?! ?(아님|아니|아닙|문의|없))|협찬(?! ?(아님|아니|아닙|문의|·?제휴))", first_slide))
        in_video = bool(meta.get("on_video_disclosure_start") and meta.get("on_video_disclosure_end"))
        is_reel = (meta.get("format") or "").upper() == "REELS"
        if is_reel:
            # 예규 499 Ⅴ.6: 동영상은 '제목 또는 동영상 내' — caption head OR in-video (start, end, repeated).
            if not (in_caption or in_video):
                hits.append(_hit("REJECT", "missing-ad-disclosure", disc["why"], disc["law"], disc["fix"], "$.caption", head))
            elif not in_video:
                hits.append(_hit("FLAG", "reel-disclosure-in-video", "캡션 표시는 충족. 영상만 보는 시청자를 위해 영상 시작·끝 '광고' 표시 권장",
                                 disc["law"], "영상 첫·마지막 프레임에 '광고' 오버레이 후 meta에 표시"))
        if not is_reel and not (in_caption or in_image):
            why = disc["why"]
            if re.search(disc["invalid_only"], head, re.IGNORECASE):
                why += " (영문·모호 표기만 있음)"
            hits.append(_hit("REJECT", "missing-ad-disclosure", why, disc["law"], disc["fix"], "$.caption", head))

    # 5. AI content
    role = (meta.get("ai_persona_role") or "none").lower()
    if role in ("customer", "expert"):
        hits.append(_hit("REJECT", "ai-persona", "AI 생성 인물을 실제 고객·전문가처럼 사용",
                         "공정위 심사지침 Ⅴ.5, 식품표시광고법 제8조①11·화장품법 제13조①4(2026-11-27)", "실제 인물로 교체하거나 삭제"))
    if role == "ambassador" and "가상인물" not in all_text:
        hits.append(_hit("REJECT", "ai-persona-label", "가상인물 추천에 '가상인물' 표시 없음",
                         "공정위 심사지침 Ⅴ.5", "게시물 첫머리와 인물 옆에 '가상인물' 표기"))
    if meta.get("ai_assets"):
        if not meta.get("is_ai_generated"):
            hits.append(_hit("FLAG", "ai-flag", "AI 에셋 사용 — 게시 시 is_ai_generated=true 설정 필요",
                             "Meta AI 라벨, AI 기본법 제31조(적용 범위 미확정)", "meta.is_ai_generated=true"))
        if not re.search(r"AI ?(생성|음성)|AI-generated", all_text, re.IGNORECASE):
            hits.append(_hit("FLAG", "ai-visible-note", "AI 이미지·음성에 보이는 표기 없음",
                             "AI 기본법 제31조③(적용 범위 미확정)", "캡션 말미 'AI 생성 이미지 포함'"))

    # 6. Audio / footage rights
    if (meta.get("format") or "").upper() == "REELS":
        src = meta.get("audio_source")
        if not src:
            hits.append(_hit("FLAG", "audio-source-missing", "릴스 음원 출처 미기재", "저작권법(2026-08-11 개정)",
                             "meta.audio_source = original | meta_sound_collection | ig_library | licensed"))
        elif src == "licensed" and not meta.get("audio_license_id"):
            hits.append(_hit("REJECT", "audio-license-missing", "라이선스 음원인데 라이선스 ID 없음",
                             "저작권법 제136조(7년/1억), 제125조④(징벌적 5배)", "meta.audio_license_id 기입"))
        elif src == "ig_library":
            hits.append(_hit("FLAG", "audio-ig-library", "앱 인기 음원 — 비즈니스 계정 상업 사용 가능 여부 확인",
                             "Instagram 음악 가이드라인", "비즈니스 라이브러리 노출 여부 확인"))
    if meta.get("third_party_footage") and not meta.get("footage_license_id"):
        hits.append(_hit("REJECT", "footage-license-missing", "타사·방송 영상 사용에 라이선스 없음 (Top Gear/BBC 포함)",
                         "저작권법, 인스타 독창성 정책(2026-04-30)", "자체 촬영 BTS 또는 라이선스 ID"))
    if meta.get("public_road_driving"):
        hits.append(_hit("FLAG", "public-road", "공도 주행 장면 — 합법 속도·차분한 주행인지 확인, 트랙이면 '트랙 촬영' 표기",
                         "도로교통법 제46·46조의3", ""))
    if meta.get("competitor_named"):
        hits.append(_hit("FLAG", "competitor-meta", "경쟁사 언급 — 동일 조건 비교·조건 공개 필요",
                         "비교표시·광고 심사지침", ""))

    # 7. Sauna safety line (EGA)
    safety = rules.get("safety_line")
    if safety and brand in safety.get("brands", [brand]):
        # Hashtags (#에가브레인사우나 on every post) don't make a post about heat/cold exposure.
        body = re.sub(r"#\S+", "", all_text)
        if re.search(safety["when_text"], body, re.IGNORECASE) and not re.search(safety["pattern"], all_text, re.IGNORECASE):
            hits.append(_hit("FLAG", "sauna-safety-line", safety["why"], safety["law"], safety["fix"]))

    # 8. Caption platform limits
    caption = _caption(content)
    if caption:
        tags = re.findall(r"(?<![\w&])#[\w가-힣]+", caption)
        if len(tags) > MAX_HASHTAGS:
            hits.append(_hit("REJECT", "hashtag-cap", f"해시태그 {len(tags)}개 — 인스타 상한 5개(2025-12)", "Instagram 정책",
                             "5개 이하로"))
        if len(caption) > MAX_CAPTION:
            hits.append(_hit("REJECT", "caption-length", f"캡션 {len(caption)}자 — 상한 2,200자", "Instagram API", "줄이기"))

    verdict = "PASS"
    for h in hits:
        if SEVERITY_ORDER[h["severity"]] > SEVERITY_ORDER[verdict]:
            verdict = h["severity"]
    return {"verdict": verdict, "brand": brand, "hits": hits}


def _caption(content: dict) -> str:
    if content.get("caption.txt"):
        return content["caption.txt"]
    return next((d["caption"] for d in content.values() if isinstance(d, dict) and isinstance(d.get("caption"), str)), "")


def _sentence(text, m):
    seps = ".!?\n。"
    start = max(text.rfind(c, 0, m.start()) for c in seps) + 1
    ends = [i for i in (text.find(c, m.end()) for c in seps) if i != -1]
    return text[start:min(ends) if ends else len(text)]


def _first_slide_text(content: dict) -> str:
    for data in content.values():
        if isinstance(data, dict) and isinstance(data.get("slides"), list) and data["slides"]:
            return " ".join(t for _, t in collect_text(data["slides"][0]))
    return ""


def _sibling_has(content: dict, path: str, rx: re.Pattern) -> bool:
    """True if another field of the same slide/scene (same JSON object) matches rx."""
    m = re.match(r"^(.*\[\d+\])\.", path)
    if not m:
        return False
    prefix = m.group(1) + "."
    return any(p.startswith(prefix) and rx.search(t) for p, t in collect_text(content))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("content", help="package dir, JSON/text file, or literal text")
    ap.add_argument("--brand", required=True, type=lambda v: v.strip().lower(), choices=sorted(BRANDS))
    ap.add_argument("--paid", action="store_true", help="paid / gifted / collab with compensation")
    args = ap.parse_args()
    try:
        content, meta = load_package(args.content)
        res = check(content, args.brand, meta, args.paid)
    except Exception as e:  # a crash must never look like PASS or FLAG
        print(json.dumps({"verdict": "ERROR", "error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 3
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return SEVERITY_ORDER[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
