#!/usr/bin/env python3
"""Rule-based compliance gate for Instagram content (Korean law + brand voice).

    python3 tools/compliance/check.py <content.json | caption.txt> --brand ega|adro [--paid]

Reads every string in a carousel spec / reel script JSON (or a plain text caption),
applies tools/compliance/rules.json and prints a verdict:

    REJECT  must be rewritten before anyone reviews it
    FLAG    a human must look at it (listed reasons)
    PASS    no rule fired (this is not legal advice; the reviewer agent still checks context)

Exit code: 2 = REJECT, 1 = FLAG, 0 = PASS.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RULES_PATH = Path(__file__).with_name("rules.json")
SEVERITY_ORDER = {"PASS": 0, "FLAG": 1, "REJECT": 2}


def collect_text(node, path="$"):
    """Yield (json_path, text) for every string in the content."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in ("image", "video", "id", "brand", "size", "layout", "audio"):
                continue
            yield from collect_text(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from collect_text(v, f"{path}[{i}]")


def load_content(arg: str):
    p = Path(arg)
    raw = p.read_text(encoding="utf-8") if p.exists() else arg
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"caption": raw}


def check(content, brand: str, paid: bool = False, rules: dict | None = None) -> dict:
    rules = rules or json.loads(RULES_PATH.read_text(encoding="utf-8"))
    texts = list(collect_text(content))
    hits = []
    for rule in rules["rules"]:
        if rule.get("brands") and brand not in rule["brands"]:
            continue
        rx = re.compile(rule["pattern"], re.IGNORECASE)
        allow = re.compile(rule["unless"], re.IGNORECASE) if rule.get("unless") else None
        for path, text in texts:
            for m in rx.finditer(text):
                if allow and allow.search(text):
                    continue
                hits.append({
                    "severity": rule["severity"],
                    "rule": rule["id"],
                    "law": rule.get("law", ""),
                    "why": rule["why"],
                    "fix": rule.get("fix", ""),
                    "where": path,
                    "match": m.group(0),
                })

    # Numeric performance claims need a visible source somewhere in the content.
    all_text = "\n".join(t for _, t in texts)
    num_rule = rules.get("numeric_claims", {})
    if num_rule and brand in num_rule.get("brands", [brand]):
        claim_rx = re.compile(num_rule["pattern"])
        source_rx = re.compile(num_rule["source_pattern"], re.IGNORECASE)
        if claim_rx.search(all_text) and not source_rx.search(all_text):
            hits.append({
                "severity": num_rule["severity"],
                "rule": "numeric-claim-without-source",
                "law": num_rule.get("law", ""),
                "why": num_rule["why"],
                "fix": num_rule.get("fix", ""),
                "where": "$",
                "match": claim_rx.search(all_text).group(0),
            })

    # Paid / sponsored content must disclose at the very start of the caption.
    is_dict = isinstance(content, dict)
    if paid or (is_dict and content.get("paid")):
        caption = content.get("caption", "") if is_dict else ""
        disc = rules["disclosure"]
        head = caption.strip()[: disc.get("head_chars", 30)]
        if not re.search(disc["pattern"], head):
            hits.append({
                "severity": "REJECT",
                "rule": "missing-ad-disclosure",
                "law": disc["law"],
                "why": disc["why"],
                "fix": disc["fix"],
                "where": "$.caption",
                "match": head,
            })

    verdict = "PASS"
    for h in hits:
        if SEVERITY_ORDER[h["severity"]] > SEVERITY_ORDER[verdict]:
            verdict = h["severity"]
    return {"verdict": verdict, "brand": brand, "hits": hits}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("content")
    ap.add_argument("--brand", required=True)
    ap.add_argument("--paid", action="store_true", help="content is paid/sponsored/collab with compensation")
    args = ap.parse_args()
    res = check(load_content(args.content), args.brand.lower(), args.paid)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return SEVERITY_ORDER[res["verdict"]]


if __name__ == "__main__":
    sys.exit(main())
