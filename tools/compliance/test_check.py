"""Tests for the compliance gate. Run: python3 -m unittest tools/compliance/test_check.py"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check import check, load_package  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def rules_hit(res, rule):
    return [h for h in res["hits"] if h["rule"] == rule]


class SamplesTest(unittest.TestCase):
    def test_ega_sample_passes(self):
        content, meta = load_package(str(ROOT / "tools/carousel/examples/ega-sample.json"))
        res = check(content, "ega", meta)
        self.assertEqual(res["verdict"], "PASS", res["hits"])

    def test_adro_sample_passes(self):
        content, meta = load_package(str(ROOT / "tools/carousel/examples/adro-sample.json"))
        res = check(content, "adro", meta)
        self.assertEqual(res["verdict"], "PASS", res["hits"])


class EgaRulesTest(unittest.TestCase):
    def test_nmn_recovery_rejected(self):
        res = check({"caption.txt": "REVERSE AGING · NMN = RECOVERY"}, "ega")
        self.assertEqual(res["verdict"], "REJECT")
        self.assertTrue(rules_hit(res, "nmn-recovery-slogan"))
        self.assertEqual(rules_hit(res, "ega-anti-aging-slogan")[0]["severity"], "REJECT")  # escalated by NMN

    def test_reverse_aging_alone_is_flag(self):
        res = check({"caption.txt": "REVERSE AGING, 매일의 루틴"}, "ega")
        self.assertEqual(res["verdict"], "FLAG")

    def test_world_first_needs_evidence(self):
        res = check({"caption.txt": "전 세계 최초 브레인 사우나 오픈"}, "ega")
        self.assertEqual(rules_hit(res, "superlative")[0]["severity"], "REJECT")
        res2 = check({"caption.txt": "전 세계 최초 브레인 사우나 오픈"}, "ega", {"evidence_ids": ["evidence/first.pdf"]})
        self.assertEqual(rules_hit(res2, "superlative")[0]["severity"], "FLAG")

    def test_cell_claims_rejected(self):
        res = check({"caption.txt": "온탕에서 냉탕으로, 세포가 깨어난다"}, "ega")
        self.assertTrue(rules_hit(res, "food-function-claim"))

    def test_disclaimer_does_not_trigger_disease_rule(self):
        res = check({"caption.txt": "본 콘텐츠는 질병의 예방·치료를 목적으로 하지 않습니다."}, "ega")
        self.assertFalse(rules_hit(res, "food-disease-medicine"))

    def test_visitor_symptom_claim_rejected(self):
        res = check({"caption.txt": "방문 후기: 두통이 사라졌어요"}, "ega")
        self.assertEqual(res["verdict"], "REJECT")

    def test_sauna_without_safety_line_flagged(self):
        res = check({"caption.txt": "냉탕 90초 루틴, 오늘의 리셋"}, "ega")
        self.assertTrue(rules_hit(res, "sauna-safety-line"))
        res2 = check({"caption.txt": "냉탕 90초 루틴. 어지러우면 바로 휴식하세요"}, "ega")
        self.assertFalse(rules_hit(res2, "sauna-safety-line"))

    def test_hff_requires_review_id(self):
        res = check({"caption.txt": "오늘의 루틴"}, "ega", {"product_category": "hff"})
        self.assertTrue(rules_hit(res, "missing-pre-review"))

    def test_digital_detox_allowed(self):
        res = check({"caption.txt": "휴대폰 없는 90분, 디지털 디톡스"}, "ega")
        self.assertFalse(rules_hit(res, "food-function-claim"))


class AdroRulesTest(unittest.TestCase):
    def test_numeric_claim_without_evidence_rejected(self):
        res = check({"caption.txt": "This kit cut drag 15% on a Tesla Model Y"}, "adro")
        self.assertTrue(rules_hit(res, "numeric-claim-no-evidence"))
        self.assertEqual(res["verdict"], "REJECT")

    def test_numeric_claim_with_evidence_and_condition_is_flag_only(self):
        spec = {"slides": [{"layout": "stat", "stat": "15", "unit": "%", "title": "drag 15% lower",
                            "source": "adro 자체 테스트, Tesla Model Y, 100 km/h, 순정 대비"}]}
        res = check({"carousel.json": spec}, "adro", {"evidence_ids": ["evidence/model-y.pdf"]})
        self.assertFalse(rules_hit(res, "numeric-claim-no-evidence"))
        self.assertFalse(rules_hit(res, "numeric-claim-no-condition"))

    def test_efficiency_claim_always_flagged(self):
        res = check({"caption.txt": "전비 4.58% 개선"}, "adro", {"evidence_ids": ["evidence/x.pdf"]})
        self.assertTrue(rules_hit(res, "efficiency-claim"))

    def test_illegal_tuning_rejected(self):
        res = check({"caption.txt": "구조변경 없이 바로 장착, 단속 걱정 없음"}, "adro")
        self.assertEqual(res["verdict"], "REJECT")

    def test_top_gear_mark_flagged(self):
        res = check({"caption.txt": "As seen on Top Gear"}, "adro")
        self.assertTrue(rules_hit(res, "third-party-marks"))

    def test_competitor_flagged(self):
        res = check({"caption.txt": "Faster setup than Ansys"}, "adro")
        self.assertTrue(rules_hit(res, "competitor-named"))


class DisclosureTest(unittest.TestCase):
    def test_paid_without_korean_disclosure_rejected(self):
        res = check({"caption.txt": "#AD Thanks to @ega for the ritual"}, "ega", {"paid": True})
        hit = rules_hit(res, "missing-ad-disclosure")
        self.assertTrue(hit)
        self.assertIn("영문", hit[0]["why"])

    def test_paid_with_korean_disclosure_ok(self):
        res = check({"caption.txt": "[광고] 에가 브레인 사우나 초대로 다녀왔어요"}, "ega", {"gifted": True})
        self.assertFalse(rules_hit(res, "missing-ad-disclosure"))

    def test_disclosure_on_first_slide_ok(self):
        spec = {"slides": [{"layout": "cover", "eyebrow": "광고", "title": "회복 루틴"}]}
        res = check({"carousel.json": spec, "caption.txt": "회복 루틴 공유"}, "ega", {"paid": True})
        self.assertFalse(rules_hit(res, "missing-ad-disclosure"))

    def test_paid_reel_needs_in_video_disclosure(self):
        res = check({"caption.txt": "#광고 리추얼"}, "ega", {"paid": True, "format": "REELS", "audio_source": "original"})
        self.assertTrue(rules_hit(res, "reel-disclosure-in-video"))


class MetaChecksTest(unittest.TestCase):
    def test_ai_expert_rejected(self):
        res = check({"caption.txt": "루틴"}, "ega", {"ai_persona_role": "expert"})
        self.assertEqual(res["verdict"], "REJECT")

    def test_ai_assets_need_flag_and_note(self):
        res = check({"caption.txt": "루틴"}, "ega", {"ai_assets": ["cover.webp"]})
        self.assertTrue(rules_hit(res, "ai-flag"))
        self.assertTrue(rules_hit(res, "ai-visible-note"))
        res2 = check({"caption.txt": "루틴\nAI 생성 이미지 포함"}, "ega", {"ai_assets": ["c.webp"], "is_ai_generated": True})
        self.assertFalse(rules_hit(res2, "ai-flag") or rules_hit(res2, "ai-visible-note"))

    def test_licensed_audio_needs_id(self):
        res = check({"caption.txt": "x"}, "adro", {"format": "REELS", "audio_source": "licensed"})
        self.assertTrue(rules_hit(res, "audio-license-missing"))

    def test_third_party_footage(self):
        res = check({"caption.txt": "x"}, "adro", {"third_party_footage": True})
        self.assertEqual(res["verdict"], "REJECT")

    def test_hashtag_cap(self):
        res = check({"caption.txt": "x #a #b #c #d #e #f"}, "adro")
        self.assertTrue(rules_hit(res, "hashtag-cap"))


class PackageModeTest(unittest.TestCase):
    def test_reads_package_dir(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "meta.json").write_text(json.dumps({"format": "CAROUSEL", "paid": True}), encoding="utf-8")
            (p / "carousel.json").write_text(json.dumps({"slides": [{"layout": "cover", "title": "루틴"}]}), encoding="utf-8")
            (p / "caption.txt").write_text("#협찬 오늘의 루틴", encoding="utf-8")
            content, meta = load_package(d)
            self.assertTrue(meta["paid"])
            res = check(content, "ega", meta)
            self.assertFalse(rules_hit(res, "missing-ad-disclosure"))


if __name__ == "__main__":
    unittest.main()
