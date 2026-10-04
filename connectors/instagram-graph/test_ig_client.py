"""Offline tests for ig_client against a fake Instagram API.

Run: python3 -m unittest connectors/instagram-graph/test_ig_client.py
"""

import json
import os
import sys
import tempfile
import unittest
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ig_client import (  # noqa: E402
    Account,
    IGClient,
    IGError,
    derive,
    load_accounts,
    to_unix,
)


class FakeAPI:
    """Records calls and answers from a route table keyed by (method, path-suffix)."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, method, url, params, body, headers):
        form = dict(urllib.parse.parse_qsl(body.decode())) if body and headers and \
            headers.get("Content-Type", "").startswith("application/x-www-form") else {}
        self.calls.append({"method": method, "url": url, "params": params or {}, "form": form,
                           "headers": headers or {}, "body_len": len(body) if body else 0})
        path = urllib.parse.urlsplit(url).path
        for (m, suffix), handler in self.routes.items():
            if m == method and path.endswith(suffix):
                return handler(params or {}, form) if callable(handler) else handler
        raise AssertionError(f"unexpected call {method} {path}")


def make_client(routes, host="facebook", publish=False):
    acct = Account(brand="ega", token="TOKEN1234567890", user_id="1789", host=host)
    api = FakeAPI(routes)
    return IGClient({"ega": acct}, transport=api, api_version="v24.0",
                    publish_enabled=publish, sleep=lambda s: None), api


class LoadAccountsTest(unittest.TestCase):
    def test_discovers_brands_from_env(self):
        accts = load_accounts({
            "IG_EGA_TOKEN": "t1", "IG_EGA_USER_ID": "1",
            "IG_ADRO_TOKEN": "t2", "IG_ADRO_USER_ID": "2", "IG_ADRO_HOST": "facebook",
            "IG_API_VERSION": "v24.0",
        })
        self.assertEqual(set(accts), {"ega", "adro"})
        self.assertEqual(accts["adro"].host, "facebook")
        self.assertEqual(accts["ega"].host, "facebook")  # no IG prefix -> Facebook Login default

    def test_host_detected_from_token(self):
        accts = load_accounts({"IG_EGA_TOKEN": "IGAAxyz", "IG_ADRO_TOKEN": "EAAGxyz"})
        self.assertEqual(accts["ega"].host, "instagram")
        self.assertEqual(accts["adro"].host, "facebook")

    def test_rejects_unknown_host(self):
        with self.assertRaises(IGError):
            load_accounts({"IG_EGA_TOKEN": "t", "IG_EGA_HOST": "tiktok"})


class RedactionTest(unittest.TestCase):
    def test_scrub_and_redact(self):
        from ig_client import redact, scrub
        payload = {"data": [{"id": "1"}], "paging": {"next": "https://graph.facebook.com/v26.0/1/media?access_token=EAAsecret"},
                   "msg": "GET /v26.0/1?access_token=EAAsecret&x=1", "access_token": "EAAsecret"}
        out = scrub(payload)
        self.assertNotIn("paging", out)
        self.assertNotIn("access_token", out)
        self.assertNotIn("EAAsecret", json.dumps(out))
        self.assertEqual(redact("Authorization: OAuth EAAsecret"), "Authorization: OAuth ***")

    def test_transport_errors_never_include_token(self):
        from ig_client import urllib_transport
        with self.assertRaises(IGError) as ctx:
            urllib_transport("GET", "https://graph.facebook.com/v26.0/1 2/insights", {"access_token": "EAAsecret"}, None, None)
        self.assertNotIn("EAAsecret", str(ctx.exception))


class HelpersTest(unittest.TestCase):
    def test_to_unix(self):
        self.assertEqual(to_unix("2026-10-01"), 1790812800)
        self.assertEqual(to_unix(1790812800), 1790812800)
        self.assertEqual(to_unix("1790812800"), 1790812800)


class DeriveTest(unittest.TestCase):
    def test_ratios_and_target(self):
        d = derive({"views": 120000, "reach": 80000, "shares": 1600, "saved": 800,
                    "likes": 4000, "comments": 80, "ig_reels_avg_watch_time": 8450, "reels_skip_rate": 0.41})
        self.assertEqual(d["shares_per_reach"], 0.02)
        self.assertEqual(d["saves_per_reach"], 0.01)
        self.assertEqual(d["avg_watch_time_s"], 8.45)
        self.assertTrue(d["hit_100k"])
        self.assertEqual(d["views_per_reach"], 1.5)
        self.assertEqual(d["skip_rate"], 0.41)

    def test_zero_reach_is_skipped(self):
        d = derive({"views": 10, "reach": 0, "shares": 1})
        self.assertNotIn("shares_per_reach", d)
        self.assertFalse(d["hit_100k"])


class ReadTest(unittest.TestCase):
    def test_media_insights_reels_uses_reel_metrics(self):
        def insights(params, form):
            names = params["metric"].split(",")
            return {"data": [{"name": n, "period": "lifetime", "values": [{"value": 10}]} for n in names]}
        c, api = make_client({("GET", "/101/insights"): insights})
        res = c.media_insights("ega", "101", media_product_type="REELS")
        self.assertIn("ig_reels_avg_watch_time", api.calls[0]["params"]["metric"])
        self.assertNotIn("impressions", api.calls[0]["params"]["metric"])
        self.assertNotIn("plays", api.calls[0]["params"]["metric"].split(","))
        self.assertEqual(res["metrics"]["views"], 10)
        self.assertTrue(api.calls[0]["url"].startswith("https://graph.facebook.com/v24.0/"))

    def test_media_insights_skips_unsupported_metric(self):
        def insights(params, form):
            if "," in params["metric"] or params["metric"] == "profile_visits":
                raise IGError("(#100) metric[0] must be one of the following values", code=100)
            return {"data": [{"name": params["metric"], "values": [{"value": 5}]}]}
        c, _ = make_client({("GET", "/102/insights"): insights})
        res = c.media_insights("ega", "102", metrics=["views", "profile_visits", "reach"])
        self.assertEqual(res["metrics"], {"views": 5, "reach": 5})
        self.assertEqual(res["unsupported_metrics"], ["profile_visits"])

    def test_non_metric_error_is_raised(self):
        def boom(params, form):
            raise IGError("Invalid OAuth access token", code=190)
        c, _ = make_client({("GET", "/103/insights"): boom})
        with self.assertRaises(IGError):
            c.media_insights("ega", "103", media_product_type="REELS")

    def test_missing_object_is_not_treated_as_unsupported_metric(self):
        def gone(params, form):
            raise IGError("Unsupported get request. Object with ID '104' does not exist", code=100, subcode=33)
        c, api = make_client({("GET", "/104/insights"): gone})
        with self.assertRaises(IGError):
            c.media_insights("ega", "104", media_product_type="REELS")
        self.assertEqual(len(api.calls), 1)

    def test_rejects_non_numeric_ids(self):
        c, api = make_client({})
        for bad in ("17890 123", "c1\n", "1789/media?fields=id&x="):
            with self.assertRaises(IGError):
                c.media_insights("ega", bad)
            with self.assertRaises(IGError):
                c.container_status("ega", bad)
        self.assertEqual(api.calls, [])

    def test_recent_performance_sorts_and_summarizes(self):
        media = {"data": [
            {"id": "201", "media_product_type": "REELS", "caption": "hook A\nbody"},
            {"id": "202", "media_product_type": "FEED", "caption": "carousel B"},
            {"id": "203", "media_product_type": "REELS", "caption": "reel C"},
            {"id": "209", "media_product_type": "STORY"},
        ]}
        views = {"201": 150000, "202": 3000, "203": 1000}

        def ins(media_id):
            def h(params, form):
                return {"data": [{"name": "views", "total_value": {"value": views[media_id]}},
                                 {"name": "reach", "total_value": {"value": 1000}}]}
            return h
        c, _ = make_client({
            ("GET", "/1789/media"): media,
            ("GET", "/201/insights"): ins("201"),
            ("GET", "/202/insights"): ins("202"),
            ("GET", "/203/insights"): ins("203"),
        })
        res = c.recent_performance("ega", limit=10, since_days=30)
        self.assertEqual([p["id"] for p in res["posts"]], ["201", "202", "203"])
        self.assertEqual(res["summary"]["hits_100k"], 1)
        self.assertEqual(res["summary"]["median_reel_views"], 75500)  # reels only: 150000, 1000
        self.assertEqual(res["summary"]["median_views_all"], 3000)
        self.assertEqual(res["posts"][0]["caption_head"], "hook A")

    def test_recent_performance_raises_on_auth_error(self):
        def denied(params, form):
            raise IGError("Application does not have permission", code=10)
        c, _ = make_client({("GET", "/1789/media"): {"data": [{"id": "301", "media_product_type": "REELS"}]},
                            ("GET", "/301/insights"): denied})
        with self.assertRaises(IGError):
            c.recent_performance("ega")

    def test_competitor_requires_facebook_host(self):
        c, _ = make_client({}, host="instagram")
        with self.assertRaises(IGError) as ctx:
            c.competitor("ega", "someone")
        self.assertIn("Facebook Login", str(ctx.exception))

    def test_competitor_on_facebook_host(self):
        bd = {"business_discovery": {"username": "rival", "followers_count": 1000,
                                     "media": {"data": [{"id": "x", "like_count": 90, "comments_count": 10}]}}}
        c, api = make_client({("GET", "/1789"): bd}, host="facebook")
        res = c.competitor("ega", "rival", media_limit=5)
        self.assertEqual(res["media"][0]["engagement_per_follower"], 0.1)
        self.assertIn("business_discovery.username(rival)", api.calls[0]["params"]["fields"])
        self.assertTrue(api.calls[0]["url"].startswith("https://graph.facebook.com/"))

    def test_unknown_brand(self):
        c, _ = make_client({})
        with self.assertRaises(IGError) as ctx:
            c.profile("adro")
        self.assertIn("IG_ADRO_TOKEN", str(ctx.exception))


class PublishTest(unittest.TestCase):
    def test_reel_from_local_file_uses_resumable_upload(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"\x00" * 2048)
            path = f.name
        try:
            c, api = make_client({
                ("POST", "/1789/media"): {"id": "501", "uri": "https://rupload.facebook.com/ig-api-upload/v24.0/501"},
                ("POST", "/ig-api-upload/v24.0/501"): {"success": True},
            })
            res = c.create_reel("ega", "caption", video_path=path, trial_graduation="SS_PERFORMANCE",
                                collaborators=["a", "b", "c"])
        finally:
            os.unlink(path)
        create, upload = api.calls
        self.assertEqual(create["form"]["media_type"], "REELS")
        self.assertEqual(create["form"]["upload_type"], "resumable")
        self.assertEqual(json.loads(create["form"]["trial_params"]), {"graduation_strategy": "SS_PERFORMANCE"})
        self.assertEqual(len(json.loads(create["form"]["collaborators"])), 3)
        self.assertEqual(upload["headers"]["file_size"], "2048")
        self.assertEqual(upload["headers"]["Authorization"], "OAuth TOKEN1234567890")
        self.assertFalse(res["published"])

    def test_reel_disclosure_and_location_params(self):
        c, api = make_client({("POST", "/1789/media"): {"id": "502"}})
        c.create_reel("ega", "[광고] 리추얼", video_url="https://a/v.mp4", is_paid_partnership=True,
                      branded_content_sponsor_ids=["111", "222"], location_id="999", is_ai_generated=True)
        form = api.calls[0]["form"]
        self.assertEqual(form["is_paid_partnership"], "true")
        self.assertEqual(json.loads(form["branded_content_sponsor_ids"]), [111, 222])
        self.assertEqual(form["location_id"], "999")
        with self.assertRaises(IGError):
            c.create_reel("ega", "x", video_url="https://a/v.mp4", branded_content_sponsor_ids=["1", "2", "3"])
        with self.assertRaises(IGError):
            c.create_reel("ega", "x", video_url="https://a/v.mp4", collaborators=["a", "b", "c", "d"])
        self.assertEqual(form["is_ai_generated"], "true")

    def test_instagram_login_limits(self):
        c, api = make_client({}, host="instagram")
        with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
            with self.assertRaises(IGError) as ctx:
                c.create_reel("ega", "x", video_path=f.name)
        self.assertIn("Facebook Login", str(ctx.exception))
        with self.assertRaises(IGError):
            c.create_reel("ega", "[광고] x", video_url="https://a/v.mp4", is_paid_partnership=True)
        with self.assertRaises(IGError):
            c.create_reel("ega", "x", video_url="https://a/v.mp4", collaborators=["someone"])
        self.assertEqual(api.calls, [])

    def test_reel_needs_exactly_one_source(self):
        c, _ = make_client({})
        with self.assertRaises(IGError):
            c.create_reel("ega", "x")
        with self.assertRaises(IGError):
            c.create_reel("ega", "x", video_url="https://a", video_path="/tmp/b.mp4")

    def test_bad_trial_strategy(self):
        c, _ = make_client({})
        with self.assertRaises(IGError):
            c.create_reel("ega", "x", video_url="https://a/v.mp4", trial_graduation="AUTO")

    def test_carousel_builds_children_waits_for_video_then_parent(self):
        counter = iter(["601", "602", "603", "699"])
        c, api = make_client({("POST", "/1789/media"): lambda p, f: {"id": next(counter)},
                              ("GET", "/603"): {"id": "603", "status_code": "FINISHED"}})
        res = c.create_carousel("ega", "cap", [{"image_url": "https://x/1.jpg", "alt_text": "slide one"},
                                               {"image_url": "https://x/2.jpeg"},
                                               {"video_url": "https://x/3.mp4"}], is_ai_generated=True)
        self.assertEqual(res["children"], ["601", "602", "603"])
        self.assertEqual(api.calls[2]["form"]["media_type"], "VIDEO")
        self.assertTrue(api.calls[3]["url"].endswith("/603"))  # status poll before the parent
        parent = api.calls[4]["form"]
        self.assertEqual(parent["children"], "601,602,603")
        self.assertEqual(parent["media_type"], "CAROUSEL")
        self.assertEqual(api.calls[0]["form"]["alt_text"], "slide one")
        self.assertEqual(parent["is_ai_generated"], "true")
        self.assertNotIn("is_ai_generated", api.calls[0]["form"])

    def test_carousel_stops_if_video_child_fails(self):
        counter = iter(["611", "612"])
        c, api = make_client({("POST", "/1789/media"): lambda p, f: {"id": next(counter)},
                              ("GET", "/612"): {"id": "612", "status_code": "ERROR", "status": "2207026"}})
        with self.assertRaises(IGError) as ctx:
            c.create_carousel("ega", "cap", [{"image_url": "https://x/1.jpg"}, {"video_url": "https://x/2.mp4"}])
        self.assertIn("611,612", str(ctx.exception))
        self.assertFalse(any(x["form"].get("media_type") == "CAROUSEL" for x in api.calls))

    def test_carousel_bounds(self):
        c, _ = make_client({})
        with self.assertRaises(IGError):
            c.create_carousel("ega", "cap", [{"image_url": "https://x/1.jpg"}])
        with self.assertRaises(IGError):
            c.create_carousel("ega", "cap", [{"image_url": f"https://x/{i}.jpg"} for i in range(11)])

    def test_carousel_rejects_png(self):
        c, api = make_client({})
        with self.assertRaises(IGError) as ctx:
            c.create_carousel("ega", "cap", [{"image_url": "https://x/1.png"}, {"image_url": "https://x/2.jpg"}])
        self.assertIn("JPEG", str(ctx.exception))
        self.assertEqual(api.calls, [])

    def test_hashtag_cap(self):
        c, api = make_client({})
        with self.assertRaises(IGError) as ctx:
            c.create_reel("ega", "훅 #사우나 #냉탕 #회복 #루틴 #웰니스 #서울", video_url="https://a/v.mp4")
        self.assertIn("5", str(ctx.exception))
        self.assertEqual(api.calls, [])

    def test_publish_is_dry_run_when_disabled(self):
        c, api = make_client({}, publish=False)
        res = c.publish("ega", "701")
        self.assertTrue(res["dry_run"])
        self.assertEqual(api.calls, [])

    def test_publish_refuses_unfinished_container(self):
        c, api = make_client({("GET", "/702"): {"id": "702", "status_code": "IN_PROGRESS"}}, publish=True)
        with self.assertRaises(IGError):
            c.publish("ega", "702")
        self.assertFalse(any(call["url"].endswith("media_publish") for call in api.calls))

    def test_publish_when_enabled_and_finished(self):
        c, api = make_client({
            ("GET", "/703"): {"id": "703", "status_code": "FINISHED"},
            ("GET", "/1789/content_publishing_limit"): {"data": [{"quota_usage": 3, "config": {"quota_total": 100}}]},
            ("POST", "/1789/media_publish"): {"id": "799"},
            ("GET", "/799"): {"permalink": "https://instagram.com/p/x", "timestamp": "t"},
        }, publish=True)
        res = c.publish("ega", "703")
        self.assertTrue(res["published"])
        self.assertEqual(res["permalink"], "https://instagram.com/p/x")
        publish_call = [x for x in api.calls if x["url"].endswith("media_publish")][0]
        self.assertEqual(publish_call["form"]["creation_id"], "703")

    def test_publish_success_survives_permalink_failure(self):
        def flaky(params, form):
            raise IGError("An unexpected error has occurred", code=2)
        c, _ = make_client({
            ("GET", "/704"): {"id": "704", "status_code": "FINISHED"},
            ("GET", "/1789/content_publishing_limit"): {"data": [{"quota_usage": 3, "config": {"quota_total": 100}}]},
            ("POST", "/1789/media_publish"): {"id": "798"},
            ("GET", "/798"): flaky,
        }, publish=True)
        res = c.publish("ega", "704")
        self.assertTrue(res["published"])
        self.assertEqual(res["media_id"], "798")
        self.assertIn("permalink_error", res)

    def test_publish_stops_at_quota(self):
        c, api = make_client({
            ("GET", "/706"): {"id": "706", "status_code": "FINISHED"},
            ("GET", "/1789/content_publishing_limit"): {"data": [{"quota_usage": 50, "config": {"quota_total": 50}}]},
        }, publish=True)
        with self.assertRaises(IGError) as ctx:
            c.publish("ega", "706")
        self.assertIn("quota", str(ctx.exception))
        self.assertFalse(any(x["url"].endswith("media_publish") for x in api.calls))

    def test_wait_until_ready_polls(self):
        states = iter(["IN_PROGRESS", "IN_PROGRESS", "FINISHED"])
        c, api = make_client({("GET", "/705"): lambda p, f: {"status_code": next(states)}})
        self.assertEqual(c.wait_until_ready("ega", "705")["status_code"], "FINISHED")
        self.assertEqual(len(api.calls), 3)


if __name__ == "__main__":
    unittest.main()
