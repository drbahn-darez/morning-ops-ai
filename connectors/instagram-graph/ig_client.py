"""Instagram Platform API client used by the instagram-graph MCP server.

Pure standard library so it runs anywhere python3 runs (cloud session, Mac).
All network access goes through a single `transport` callable so tests can
swap in a fake API.

Brands are configured through environment variables, one set per brand:

    IG_<BRAND>_TOKEN     long-lived access token (required)
    IG_<BRAND>_USER_ID   Instagram professional account ID (required)
    IG_<BRAND>_HOST      "facebook" (graph.facebook.com, Facebook Login for Business;
                         recommended: Business Discovery, Hashtag Search, documented
                         resumable upload, non-expiring system-user tokens) or
                         "instagram" (graph.instagram.com, Instagram Login).
                         Default: detected from the token (Instagram Login tokens
                         start with "IG"), else facebook.

Global:
    IG_API_VERSION       Graph API version, default DEFAULT_API_VERSION
    IG_PUBLISH_ENABLED   "1" to allow media_publish. Anything else = dry run.
"""

from __future__ import annotations

import datetime as dt
import http.client
import json
import os
import re
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

DEFAULT_API_VERSION = "v26.0"  # released 2026-07-29

HOSTS = {
    "instagram": "https://graph.instagram.com",
    "facebook": "https://graph.facebook.com",
}
RUPLOAD_HOST = "https://rupload.facebook.com"

# Per-media insights metrics. `views` replaced plays/impressions/clips_replays_count
# (v22.0+ from 2025-01-21, all versions from 2025-04-21). reels_skip_rate and reposts
# were added in Dec 2025; metrics an account/version does not support are skipped.
REEL_METRICS = [
    "views",
    "reach",
    "likes",
    "comments",
    "shares",
    "saved",
    "total_interactions",
    "ig_reels_avg_watch_time",
    "ig_reels_video_view_total_time",
    "reels_skip_rate",
    "reposts",
    "crossposted_views",
    "facebook_views",
]
# follows / profile_visits / profile_activity are FEED-only; requesting them on a Reel is error 100.
FEED_METRICS = [
    "views",
    "reach",
    "likes",
    "comments",
    "shares",
    "saved",
    "total_interactions",
    "profile_visits",
    "follows",
    "reposts",
]
ACCOUNT_METRICS = [
    "reach",
    "views",
    "accounts_engaged",
    "total_interactions",
    "profile_links_taps",
]
MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,permalink,timestamp,"
    "like_count,comments_count,thumbnail_url,media_url"
)
DISCOVERY_MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,permalink,timestamp,"
    "like_count,comments_count,view_count"
)

VIEWS_TARGET = 100_000
MAX_HASHTAGS = 5  # Instagram cap since Dec 2025 (API docs still say 30)
MAX_CAPTION = 2200
CAROUSEL_MIN, CAROUSEL_MAX = 2, 10  # API limit; the app allows 20

Transport = Callable[[str, str, dict | None, bytes | None, dict | None], dict]

ID_RE = re.compile(r"\d{1,30}")
TOKEN_RE = re.compile(r"(access_token=|OAuth |Bearer )[^&\s'\"]+")
AUTH_CODES = {10, 102, 190, 200}  # permission / expired-token errors: never hide these


def redact(text: str) -> str:
    """Remove access tokens from any text that may reach the model."""
    return TOKEN_RE.sub(r"\1***", text)


def scrub(obj: Any) -> Any:
    """Drop paging blocks (their URLs embed the token) and redact tokens in API payloads."""
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items() if k not in ("paging", "access_token")}
    if isinstance(obj, list):
        return [scrub(v) for v in obj]
    if isinstance(obj, str):
        return redact(obj)
    return obj


class IGError(Exception):
    """API or configuration error with a message safe to show to the user."""

    def __init__(self, message: str, code: int | None = None, subcode: int | None = None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode


@dataclass
class Account:
    brand: str
    token: str
    user_id: str
    host: str = "instagram"

    @property
    def base(self) -> str:
        return HOSTS[self.host]


def _id(value: Any, what: str = "id") -> str:
    """Media and container ids are numeric; reject anything else so it cannot rewrite the request path."""
    s = str(value).strip()
    if not ID_RE.fullmatch(s):
        raise IGError(f"{what} must be a numeric Instagram id, got {value!r}")
    return s


def mask(token: str) -> str:
    return f"{token[:6]}…{token[-4:]}" if len(token) > 12 else "***"


def load_accounts(env: dict | None = None) -> dict[str, Account]:
    env = dict(os.environ if env is None else env)
    accounts: dict[str, Account] = {}
    for key, value in env.items():
        m = re.fullmatch(r"IG_([A-Z0-9]+)_TOKEN", key)
        if not m or not value:
            continue
        brand = m.group(1).lower()
        user_id = env.get(f"IG_{m.group(1)}_USER_ID", "")
        default_host = "instagram" if value.startswith("IG") else "facebook"
        host = env.get(f"IG_{m.group(1)}_HOST", default_host).lower()
        if host not in HOSTS:
            raise IGError(f"IG_{m.group(1)}_HOST must be one of {sorted(HOSTS)}, got {host!r}")
        accounts[brand] = Account(brand=brand, token=value, user_id=user_id, host=host)
    return accounts


def urllib_transport(method: str, url: str, params: dict | None, body: bytes | None, headers: dict | None) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            raise IGError(f"HTTP {e.code} from {urllib.parse.urlsplit(url).netloc}") from None
        err = payload.get("error", {})
        raise IGError(
            err.get("error_user_msg") or err.get("message") or f"HTTP {e.code}",
            code=err.get("code"),
            subcode=err.get("error_subcode"),
        ) from None
    except urllib.error.URLError as e:
        raise IGError(
            f"Network error reaching {urllib.parse.urlsplit(url).netloc}: {redact(str(e.reason))}. "
            "In a cloud session, allow graph.instagram.com, graph.facebook.com and "
            "rupload.facebook.com in the environment's network settings."
        ) from None
    except (http.client.HTTPException, ValueError, OSError) as e:
        raise IGError(f"Request to {urllib.parse.urlsplit(url).netloc} failed: {redact(str(e))}") from None
    try:
        return json.loads(raw or b"{}")
    except json.JSONDecodeError:
        raise IGError(f"Non-JSON response from {urllib.parse.urlsplit(url).netloc}") from None


def validate_caption(caption: str) -> None:
    if len(caption) > MAX_CAPTION:
        raise IGError(f"Caption is {len(caption)} chars; the limit is {MAX_CAPTION}.")
    tags = re.findall(r"(?<![\w&])#[\w가-힣]+", caption)
    if len(tags) > MAX_HASHTAGS:
        raise IGError(f"Caption has {len(tags)} hashtags; Instagram allows {MAX_HASHTAGS} per post since Dec 2025.")


def to_unix(value: str | int) -> int:
    """Accept unix seconds or YYYY-MM-DD (interpreted as UTC midnight)."""
    if isinstance(value, int) or str(value).isdigit():
        return int(value)
    return int(dt.datetime.strptime(str(value), "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())


def _ratio(num: Any, den: Any) -> float | None:
    try:
        return round(float(num) / float(den), 4) if den else None
    except (TypeError, ValueError):
        return None


def derive(insights: dict[str, Any]) -> dict[str, Any]:
    """Diagnostic ratios used by the analyst agent. Inputs are raw metric values."""
    reach = insights.get("reach")
    out = {
        "shares_per_reach": _ratio(insights.get("shares"), reach),
        "saves_per_reach": _ratio(insights.get("saved"), reach),
        "likes_per_reach": _ratio(insights.get("likes"), reach),
        "comments_per_reach": _ratio(insights.get("comments"), reach),
        "views_per_reach": _ratio(insights.get("views"), reach),
    }
    skip = insights.get("reels_skip_rate")
    if skip is not None:
        # Hook failure rate. Meta: "percentage of views from people who skipped during the first 3 seconds"
        # (estimated, in development; Supermetrics describes it per viewer). Empty for low-view Reels.
        out["skip_rate"] = skip
    avg_ms = insights.get("ig_reels_avg_watch_time")
    if avg_ms is not None:
        out["avg_watch_time_s"] = round(float(avg_ms) / 1000, 2)
    views = insights.get("views")
    if views is not None:
        out["hit_100k"] = views >= VIEWS_TARGET
        out["progress_to_100k"] = round(min(views / VIEWS_TARGET, 1.0), 3)
    return {k: v for k, v in out.items() if v is not None}


def _flatten_insights(payload: dict) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for item in payload.get("data", []):
        name = item.get("name")
        if "total_value" in item:
            values[name] = item["total_value"].get("value")
        elif item.get("values"):
            vals = item["values"]
            values[name] = vals[0].get("value") if len(vals) == 1 else [
                {"end_time": v.get("end_time"), "value": v.get("value")} for v in vals
            ]
    return values


def _is_metric_error(e: IGError) -> bool:
    return e.code == 100 and e.subcode != 33 and "metric" in str(e).lower()


def _check_lists(collaborators: list[str] | None, sponsors: list | None) -> None:
    if collaborators and len(collaborators) > 3:
        raise IGError(f"{len(collaborators)} collaborators given; the API allows 3.")
    if sponsors and len(sponsors) > 2:
        raise IGError(f"{len(sponsors)} branded_content_sponsor_ids given; the limit is 2.")


def _sponsor_ids(sponsors: list) -> str:
    return json.dumps([int(_id(s, "branded_content_sponsor_id")) for s in sponsors])


class IGClient:
    def __init__(
        self,
        accounts: dict[str, Account] | None = None,
        transport: Transport = urllib_transport,
        api_version: str | None = None,
        publish_enabled: bool | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.accounts = load_accounts() if accounts is None else accounts
        self.transport = transport
        self.api_version = api_version or os.environ.get("IG_API_VERSION", DEFAULT_API_VERSION)
        self.publish_enabled = (
            os.environ.get("IG_PUBLISH_ENABLED") == "1" if publish_enabled is None else publish_enabled
        )
        self.sleep = sleep

    # ---- plumbing -------------------------------------------------------

    def account(self, brand: str) -> Account:
        acct = self.accounts.get(brand.lower())
        if not acct:
            configured = ", ".join(sorted(self.accounts)) or "none"
            raise IGError(
                f"Brand {brand!r} is not configured (configured: {configured}). "
                f"Set IG_{brand.upper()}_TOKEN and IG_{brand.upper()}_USER_ID."
            )
        if not acct.user_id:
            raise IGError(f"IG_{brand.upper()}_USER_ID is missing.")
        return acct

    def _call(self, acct: Account, method: str, path: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        params["access_token"] = acct.token
        url = f"{acct.base}/{self.api_version}/{path.lstrip('/')}"
        if method == "GET":
            return self.transport("GET", url, params, None, None)
        body = urllib.parse.urlencode(params).encode()
        return self.transport(
            "POST", url, None, body, {"Content-Type": "application/x-www-form-urlencoded"}
        )

    def _require_facebook(self, acct: Account, feature: str) -> None:
        if acct.host != "facebook":
            raise IGError(
                f"{feature} is only available with Facebook Login (graph.facebook.com). "
                f"Set IG_{acct.brand.upper()}_HOST=facebook with a Facebook-Login token, "
                "or use Supermetrics 'Instagram Public Data' (IGPD2) instead."
            )

    # ---- read -----------------------------------------------------------

    def list_accounts(self) -> list[dict]:
        return [
            {
                "brand": a.brand,
                "host": a.host,
                "user_id": a.user_id or None,
                "token": mask(a.token),
                "publish_enabled": self.publish_enabled,
            }
            for a in self.accounts.values()
        ]

    def profile(self, brand: str) -> dict:
        acct = self.account(brand)
        fields = "id,username,name,followers_count,follows_count,media_count"
        if acct.host == "facebook":
            fields += ",biography,website"
        return self._call(acct, "GET", acct.user_id, {"fields": fields})

    def list_media(self, brand: str, limit: int = 25, since_days: int | None = None) -> list[dict]:
        acct = self.account(brand)
        params: dict[str, Any] = {"fields": MEDIA_FIELDS, "limit": min(limit, 100)}
        if since_days:
            params["since"] = int(time.time()) - since_days * 86400
        items: list[dict] = []
        path = f"{acct.user_id}/media"
        while path and len(items) < limit:
            page = self._call(acct, "GET", path, params)
            items.extend(page.get("data", []))
            after = page.get("paging", {}).get("cursors", {}).get("after")
            if not after or not page.get("paging", {}).get("next"):
                break
            params["after"] = after
        return items[:limit]

    def media_insights(self, brand: str, media_id: str, metrics: list[str] | None = None,
                       media_product_type: str | None = None) -> dict:
        acct = self.account(brand)
        media_id = _id(media_id, "media_id")
        if metrics is None:
            metrics = REEL_METRICS if (media_product_type or "").upper() == "REELS" else FEED_METRICS
        try:
            payload = self._call(acct, "GET", f"{media_id}/insights", {"metric": ",".join(metrics)})
            values = _flatten_insights(payload)
            skipped: list[str] = []
        except IGError as e:
            # One unsupported metric fails the whole request; retry one by one and skip the bad ones.
            # Only for metric errors — code 100 is also used for missing objects (subcode 33).
            if not _is_metric_error(e) or len(metrics) == 1:
                raise
            values, skipped, last = {}, [], e
            for m in metrics:
                try:
                    values.update(_flatten_insights(self._call(acct, "GET", f"{media_id}/insights", {"metric": m})))
                except IGError as inner:
                    if not _is_metric_error(inner):
                        raise
                    skipped.append(m)
                    last = inner
            if not values:
                raise IGError(f"No insights available for media {media_id}: {last}", last.code, last.subcode)
        result = {"media_id": media_id, "metrics": values, "derived": derive(values)}
        if skipped:
            result["unsupported_metrics"] = skipped
        return result

    def account_insights(self, brand: str, since: str, until: str, metrics: list[str] | None = None,
                         period: str = "day", metric_type: str = "total_value",
                         breakdown: str | None = None) -> dict:
        acct = self.account(brand)
        params: dict[str, Any] = {
            "metric": ",".join(metrics or ACCOUNT_METRICS),
            "period": period,
            "since": to_unix(since),
            "until": to_unix(until),
        }
        if metric_type:
            params["metric_type"] = metric_type
        if breakdown:
            params["breakdown"] = breakdown
        payload = self._call(acct, "GET", f"{acct.user_id}/insights", params)
        return {"since": since, "until": until, "metrics": _flatten_insights(payload), "raw": payload.get("data", [])}

    def recent_performance(self, brand: str, limit: int = 20, since_days: int | None = 30) -> dict:
        media = self.list_media(brand, limit=limit, since_days=since_days)
        rows = []
        for m in media:
            if m.get("media_product_type") == "STORY":
                continue
            try:
                ins = self.media_insights(brand, m["id"], media_product_type=m.get("media_product_type"))
            except IGError as e:
                if e.code in AUTH_CODES:
                    raise
                ins = {"metrics": {}, "derived": {}, "error": str(e)}
            rows.append({
                "id": m["id"],
                "timestamp": m.get("timestamp"),
                "type": m.get("media_product_type") or m.get("media_type"),
                "permalink": m.get("permalink"),
                "caption_head": (m.get("caption") or "").split("\n", 1)[0][:80],
                **ins.get("metrics", {}),
                **ins.get("derived", {}),
                **({"error": ins["error"]} if "error" in ins else {}),
            })
        rows.sort(key=lambda r: r.get("views") or 0, reverse=True)
        errors = [r for r in rows if "error" in r]
        if rows and len(errors) == len(rows):
            raise IGError(f"Insights failed for all {len(rows)} posts: {errors[0]['error']}")

        def nums(rs):
            return [r["views"] for r in rs if isinstance(r.get("views"), (int, float))]

        views = nums(rows)
        reel_views = nums(r for r in rows if r.get("type") == "REELS")
        summary = {
            "posts": len(rows),
            "reels": len([r for r in rows if r.get("type") == "REELS"]),
            "hits_100k": sum(1 for v in views if v >= VIEWS_TARGET),
            "max_views": max(views) if views else None,
            # Kill/Scale baseline = median of Reels only (playbook.md §4)
            "median_reel_views": statistics.median(reel_views) if reel_views else None,
            "median_views_all": statistics.median(views) if views else None,
            "errors": len(errors),
        }
        if errors:
            summary["first_error"] = errors[0]["error"]
        return {"brand": brand, "summary": summary, "posts": rows}

    def competitor(self, brand: str, username: str, media_limit: int = 12) -> dict:
        acct = self.account(brand)
        self._require_facebook(acct, "Business Discovery")
        fields = (
            f"business_discovery.username({username})"
            f"{{username,name,followers_count,media_count,"
            f"media.limit({media_limit}){{{DISCOVERY_MEDIA_FIELDS}}}}}"
        )
        data = self._call(acct, "GET", acct.user_id, {"fields": fields}).get("business_discovery", {})
        media = data.get("media", {}).get("data", [])
        followers = data.get("followers_count") or 0
        for m in media:
            eng = (m.get("like_count") or 0) + (m.get("comments_count") or 0)
            m["engagement_per_follower"] = _ratio(eng, followers)
        return {**{k: v for k, v in data.items() if k != "media"}, "media": media}

    def hashtag_top_media(self, brand: str, hashtag: str, edge: str = "top_media", limit: int = 25) -> dict:
        acct = self.account(brand)
        self._require_facebook(acct, "Hashtag search")
        if edge not in ("top_media", "recent_media"):
            raise IGError("edge must be top_media or recent_media")
        found = self._call(acct, "GET", "ig_hashtag_search", {"user_id": acct.user_id, "q": hashtag.lstrip("#")})
        if not found.get("data"):
            raise IGError(f"Hashtag #{hashtag} not found")
        tag_id = found["data"][0]["id"]
        media = self._call(acct, "GET", f"{tag_id}/{edge}", {
            "user_id": acct.user_id,
            "fields": "id,caption,media_type,permalink,timestamp,like_count,comments_count",
            "limit": min(limit, 50),
        })
        return {"hashtag": hashtag, "hashtag_id": tag_id, "media": media.get("data", [])}

    def publishing_limit(self, brand: str) -> dict:
        acct = self.account(brand)
        return self._call(acct, "GET", f"{acct.user_id}/content_publishing_limit", {"fields": "config,quota_usage"})

    # ---- write (containers are private until published) -----------------

    def _upload_local_video(self, acct: Account, container_id: str, path: str) -> dict:
        with open(path, "rb") as f:
            data = f.read()
        url = f"{RUPLOAD_HOST}/ig-api-upload/{self.api_version}/{container_id}"
        return self.transport("POST", url, None, data, {
            "Authorization": f"OAuth {acct.token}",
            "offset": "0",
            "file_size": str(len(data)),
        })

    def create_reel(self, brand: str, caption: str, video_url: str | None = None, video_path: str | None = None,
                    cover_url: str | None = None, thumb_offset_ms: int | None = None, share_to_feed: bool = True,
                    collaborators: list[str] | None = None, audio_name: str | None = None,
                    trial_graduation: str | None = None, is_ai_generated: bool = False,
                    is_paid_partnership: bool = False, branded_content_sponsor_ids: list | None = None,
                    location_id: str | None = None) -> dict:
        acct = self.account(brand)
        if bool(video_url) == bool(video_path):
            raise IGError("Pass exactly one of video_url (public URL) or video_path (local file).")
        validate_caption(caption)
        params: dict[str, Any] = {"media_type": "REELS", "caption": caption, "share_to_feed": str(share_to_feed).lower()}
        if video_url:
            params["video_url"] = video_url
        else:
            if not os.path.isfile(video_path):
                raise IGError(f"File not found: {video_path}")
            # Meta docs: upload_type=resumable is only for apps using Facebook Login for Business.
            self._require_facebook(acct, "Local video upload (resumable)")
            params["upload_type"] = "resumable"
        if cover_url:
            params["cover_url"] = cover_url
        if thumb_offset_ms is not None:
            params["thumb_offset"] = int(thumb_offset_ms)
        _check_lists(collaborators, branded_content_sponsor_ids)
        if collaborators:
            self._require_facebook(acct, "Collaborators")
            params["collaborators"] = json.dumps(collaborators)
        if audio_name:
            params["audio_name"] = audio_name
        if trial_graduation:
            if trial_graduation not in ("MANUAL", "SS_PERFORMANCE"):
                raise IGError("trial_graduation must be MANUAL or SS_PERFORMANCE")
            params["trial_params"] = json.dumps({"graduation_strategy": trial_graduation})
        if is_ai_generated:
            params["is_ai_generated"] = "true"
        if is_paid_partnership or branded_content_sponsor_ids:
            # The paid-partnership label is documented for Facebook Login only.
            self._require_facebook(acct, "Paid partnership label")
        if is_paid_partnership:
            params["is_paid_partnership"] = "true"
        if branded_content_sponsor_ids:
            params["branded_content_sponsor_ids"] = _sponsor_ids(branded_content_sponsor_ids)
        if location_id:
            params["location_id"] = location_id
        created = self._call(acct, "POST", f"{acct.user_id}/media", params)
        container_id = created.get("id")
        if video_path:
            try:
                upload = self._upload_local_video(acct, container_id, video_path)
            except IGError as e:
                hint = (" Resumable upload is documented for Facebook Login; with an Instagram Login token "
                        "pass a public video_url instead.") if acct.host == "instagram" else ""
                raise IGError(f"Video upload failed: {e}.{hint}", e.code, e.subcode) from None
            if not upload.get("success", True):
                raise IGError(f"Video upload failed: {upload}")
        return {"container_id": container_id, "status": "uploaded", "published": False,
                "next": "poll ig_container_status until FINISHED, then ig_publish after human approval"}

    def create_carousel(self, brand: str, caption: str, items: list[dict],
                        collaborators: list[str] | None = None, is_ai_generated: bool = False,
                        is_paid_partnership: bool = False, branded_content_sponsor_ids: list | None = None,
                        location_id: str | None = None) -> dict:
        acct = self.account(brand)
        if not CAROUSEL_MIN <= len(items) <= CAROUSEL_MAX:
            raise IGError(f"An API carousel needs {CAROUSEL_MIN} to {CAROUSEL_MAX} items (the app allows 20).")
        validate_caption(caption)
        _check_lists(collaborators, branded_content_sponsor_ids)
        children, video_children = [], []
        for i, item in enumerate(items):
            params: dict[str, Any] = {"is_carousel_item": "true"}
            if item.get("image_url"):
                if not re.search(r"\.jpe?g($|\?)", item["image_url"], re.IGNORECASE):
                    raise IGError(f"Item {i}: the API accepts JPEG images only (sRGB, max 8 MB). Render with format jpg.")
                params["image_url"] = item["image_url"]
                if item.get("alt_text"):
                    if len(item["alt_text"]) > 1000:
                        raise IGError(f"Item {i}: alt_text is {len(item['alt_text'])} chars; the limit is 1,000.")
                    params["alt_text"] = item["alt_text"]
            elif item.get("video_url"):
                params.update(media_type="VIDEO", video_url=item["video_url"])
            else:
                raise IGError(f"Item {i} needs image_url or video_url (public URLs).")
            cid = self._call(acct, "POST", f"{acct.user_id}/media", params)["id"]
            children.append(cid)
            if "video_url" in params:
                video_children.append(cid)
        # Video items must finish processing before the parent carousel container is created.
        for cid in video_children:
            st = self.wait_until_ready(brand, cid)
            if st.get("status_code") != "FINISHED":
                raise IGError(f"Carousel video item {cid} is {st.get('status_code')} ({st.get('status')}); "
                              f"children created so far: {','.join(children)}. Parent not created.")
        params = {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption}
        if collaborators:
            self._require_facebook(acct, "Collaborators")
            params["collaborators"] = json.dumps(collaborators)
        if is_ai_generated:
            params["is_ai_generated"] = "true"
        if is_paid_partnership or branded_content_sponsor_ids:
            # The paid-partnership label is documented for Facebook Login only.
            self._require_facebook(acct, "Paid partnership label")
        if is_paid_partnership:
            params["is_paid_partnership"] = "true"
        if branded_content_sponsor_ids:
            params["branded_content_sponsor_ids"] = _sponsor_ids(branded_content_sponsor_ids)
        if location_id:
            params["location_id"] = location_id
        parent = self._call(acct, "POST", f"{acct.user_id}/media", params)
        return {"container_id": parent.get("id"), "children": children, "published": False,
                "next": "poll ig_container_status until FINISHED, then ig_publish after human approval"}

    def container_status(self, brand: str, container_id: str) -> dict:
        acct = self.account(brand)
        res = self._call(acct, "GET", _id(container_id, "container_id"), {"fields": "id,status_code,status"})
        return {k: res.get(k) for k in ("id", "status_code", "status")}

    def wait_until_ready(self, brand: str, container_id: str, timeout_s: int = 300, every_s: int = 60) -> dict:
        # Meta guidance: poll once per minute for no more than 5 minutes. Containers expire after 24h.
        waited = 0
        while True:
            st = self.container_status(brand, container_id)
            code = st.get("status_code")
            if code in ("FINISHED", "PUBLISHED", "ERROR", "EXPIRED") or waited >= timeout_s:
                return st
            self.sleep(every_s)
            waited += every_s

    def publish(self, brand: str, container_id: str) -> dict:
        acct = self.account(brand)
        if not self.publish_enabled:
            return {"published": False, "dry_run": True, "container_id": container_id,
                    "reason": "IG_PUBLISH_ENABLED is not '1'. Nothing was posted."}
        st = self.container_status(brand, container_id)
        if st.get("status_code") != "FINISHED":
            raise IGError(f"Container {container_id} is {st.get('status_code')}: {st.get('status')}. Not publishing.")
        # Meta docs disagree on the quota (100 vs 50 per 24h): read the live value before every publish.
        limit = self.publishing_limit(brand).get("data", [{}])
        row = limit[0] if limit else {}
        used, total = row.get("quota_usage"), (row.get("config") or {}).get("quota_total")
        if isinstance(used, int) and isinstance(total, int) and used >= total:
            raise IGError(f"Publishing quota reached ({used}/{total} in the last 24h). Not publishing.")
        res = self._call(acct, "POST", f"{acct.user_id}/media_publish", {"creation_id": _id(container_id, "container_id")})
        media_id = res.get("id")
        out = {"published": True, "media_id": media_id}
        # The post is live now; a failed permalink lookup must not look like a failed publish.
        try:
            if media_id:
                link = self._call(acct, "GET", _id(media_id, "media_id"), {"fields": "permalink,timestamp"})
                out.update({k: link.get(k) for k in ("permalink", "timestamp")})
        except IGError as e:
            out["permalink_error"] = str(e)
        return out

    def refresh_token(self, brand: str) -> dict:
        acct = self.account(brand)
        if acct.host != "instagram":
            raise IGError("Token refresh here supports Instagram Login tokens only. "
                          "Facebook Login tokens are exchanged with fb_exchange_token in the App Dashboard.")
        url = f"{HOSTS['instagram']}/refresh_access_token"
        res = self.transport("GET", url, {"grant_type": "ig_refresh_token", "access_token": acct.token}, None, None)
        return res
