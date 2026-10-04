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

    def test_paid_reel_disclosure_title_or_video(self):
        meta = {"paid": True, "format": "REELS", "audio_source": "original"}
        res = check({"caption.txt": "#광고 리추얼"}, "ega", meta)
        self.assertFalse(rules_hit(res, "missing-ad-disclosure"))
        self.assertEqual(rules_hit(res, "reel-disclosure-in-video")[0]["severity"], "FLAG")
        res2 = check({"caption.txt": "리추얼"}, "ega", dict(meta, on_video_disclosure_start=True, on_video_disclosure_end=True))
        self.assertFalse(rules_hit(res2, "missing-ad-disclosure"))
        res3 = check({"caption.txt": "리추얼"}, "ega", meta)
        self.assertTrue(rules_hit(res3, "missing-ad-disclosure"))


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


class ReviewRegressionTest(unittest.TestCase):
    """Cases from the adversarial review corpus (2026-10-04)."""

    def v(self, text, brand, meta=None):
        return check({"caption.txt": text}, brand, meta)["verdict"]

    def test_disclaimer_does_not_cancel_violation_in_other_sentence(self):
        self.assertEqual(self.v("브레인 사우나 90분, 불면증이 사라졌어요.\n※ 본 콘텐츠는 질병의 예방·치료를 목적으로 하지 않습니다.", "ega"), "REJECT")
        self.assertEqual(self.v("본 제품은 건강기능식품이 아닙니다. 매일 아침 NMN 한 병으로 NAD+ 수치를 높이고 피로 회복까지.", "ega"), "REJECT")
        self.assertEqual(self.v("디지털 디톡스와 NMN 드링크로 몸속 독소까지 비우는 하루", "ega"), "REJECT")

    def test_ega_misses_now_caught(self):
        for text in ["브레인 사우나 다녀오면 집중력이 확 올라가요. 임산부·음주 후 이용 자제, 어지러우면 바로 휴식하세요.",
                     "한 번에 500칼로리 소모! 어지러우면 바로 휴식하세요.",
                     "두통이 싹 사라졌어요 — 방문객 후기. 임산부·음주 후 이용 자제.",
                     "약사님이 추천하는 NMN 핸드크림",
                     "Boost your NAD+ levels and support cellular repair with our NMN ritual drink.",
                     "NMN × RECOVERY",
                     "손이 10년은 젊어 보여요. NMN 핸드크림"]:
            self.assertEqual(self.v(text, "ega"), "REJECT", text)

    def test_ega_safe_copy_not_rejected(self):
        for text in ["냉탕 입수 전 체크리스트 고혈압·당뇨가 있다면 이용 전 전문의와 상의하세요. 어지러우면 바로 멈추세요.",
                     "온탕과 냉탕 사이, 오늘의 리셋 루틴. 어지러우면 무조건 휴식하세요.",
                     "20-30세 직장인 대상 NMN 핸드크림 샘플링 이벤트, 이번 주말 성수 팝업에서 만나요.",
                     "오픈 첫 주, 단 2일 만에 10월 예약이 마감되었습니다.",
                     "NMN 250mg 함유"]:
            self.assertNotEqual(self.v(text, "ega"), "REJECT", text)

    def test_safety_line_needs_real_advice(self):
        self.assertEqual(self.v("냉탕 3분 챌린지 오늘 컨디션 리셋!", "ega"), "FLAG")
        self.assertEqual(self.v("Hot 12 min, cold plunge 2 min. Skip it if you're pregnant or have a heart condition. Feeling dizzy? Rest.", "ega"), "PASS")

    def test_brand_hashtag_alone_does_not_need_safety_line(self):
        res = check({"caption.txt": "회복은 버티는 힘일까요, 돌아오는 힘일까요? #에가브레인사우나"}, "ega")
        self.assertFalse(rules_hit(res, "sauna-safety-line"))

    def test_recovery_ritual_as_drink_name_flagged(self):
        res = check({"caption.txt": "Recovery Ritual — 운동 후 한 잔, 리추얼 드링크"}, "ega")
        self.assertTrue(rules_hit(res, "recovery-ritual-drink"))

    def test_negated_disclosure_rejected(self):
        res = check({"caption.txt": "광고 아님! 내돈내산 브레인 사우나 후기. 임산부·음주 후 이용 자제."}, "ega", {"paid": True})
        self.assertTrue(rules_hit(res, "missing-ad-disclosure"))
        spec = {"slides": [{"layout": "cover", "eyebrow": "협찬·제휴 문의 DM", "title": "루틴"}]}
        res2 = check({"carousel.json": spec, "caption.txt": "다녀왔어요"}, "ega", {"gifted": True})
        self.assertTrue(rules_hit(res2, "missing-ad-disclosure"))

    def test_adro_false_positives_gone(self):
        for text in ["Orange weave, 3 finishes.", "Arrange a fitting: 2 bays open this Saturday.",
                     "AOX beta: drag & drop up to 3 STL files.", "셀프 장착 가이드 3편", "LCD 계기판 커버 2종 출시",
                     "주문 폭주로 2차 생산 들어갑니다.", "Build No. 14 delivered to Busan.", "신형 카본 디퓨저 최초 공개.",
                     "Since the pandemic, our Seoul workshop has hand-laid 120 kits."]:
            self.assertEqual(self.v(text, "adro"), "PASS", text)

    def test_adro_misses_now_caught(self):
        for text in ["AOX: 기존 CFD보다 10배 빠른 해석", "순정 대비 40% 가벼운 카본 후드",
                     "단속에 안 걸리는 디자인. 구조변경 안 해도 됩니다.", "100% 합법, 불법 튜닝 아님.",
                     "세계 최고 수준의 다운포스"]:
            self.assertEqual(self.v(text, "adro"), "REJECT", text)

    def test_dangerous_driving_not_downgraded_by_evidence(self):
        meta = {"evidence_ids": ["evidence/aox-cfd.pdf"], "tuning_cert_id": "T-123"}
        self.assertEqual(self.v("공도 레이스 OK, 칼치기에도 흔들림 없는 다운포스", "adro", meta), "REJECT")

    def test_unknown_brand_raises(self):
        with self.assertRaises(ValueError):
            check({"caption.txt": "x"}, "ega ")

    def test_long_literal_caption(self):
        content, meta = load_package("가" * 120)
        self.assertEqual(check(content, "ega", meta)["verdict"], "PASS")

    def test_json_file_caption_is_read(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"meta": {"paid": True}, "caption": "[광고] 다녀왔어요 #a #b #c #d #e #f"}, f, ensure_ascii=False)
        try:
            content, meta = load_package(f.name)
            res = check(content, "ega", meta)
        finally:
            os.unlink(f.name)
        self.assertFalse(rules_hit(res, "missing-ad-disclosure"))
        self.assertTrue(rules_hit(res, "hashtag-cap"))


class DryRunFrictionTest(unittest.TestCase):
    """Cases from the 2026-10-04 producer/reviewer dry run."""

    def test_placeholder_rejected(self):
        res = check({"reel.md": "01 · [TODO crease 01 name]"}, "adro")
        self.assertTrue(rules_hit(res, "placeholder"))
        self.assertEqual(res["verdict"], "REJECT")

    def test_myth_debunk_is_flag_not_reject(self):
        res = check({"caption.txt": "땀으로 독소가 빠진다? 사실이 아니에요."}, "ega")
        hit = rules_hit(res, "food-function-claim")
        self.assertEqual(hit[0]["severity"], "FLAG")
        res3 = check({"caption.txt": "MYTH 02 · 땀으로 독소가 빠진다"}, "ega")
        self.assertEqual(rules_hit(res3, "food-function-claim")[0]["severity"], "FLAG")
        res2 = check({"caption.txt": "땀으로 독소 배출까지 한 번에"}, "ega")
        self.assertEqual(rules_hit(res2, "food-function-claim")[0]["severity"], "REJECT")

    def test_hydration_tip_with_ritual_hashtag_not_flagged(self):
        res = check({"caption.txt": "들어가기 전 물 마시기 #에가브레인사우나 #RecoveryRitual"}, "ega")
        self.assertFalse(rules_hit(res, "recovery-ritual-drink"))


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
