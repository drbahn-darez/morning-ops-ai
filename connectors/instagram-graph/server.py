"""instagram-graph MCP server.

Exposes Instagram Platform API reads (profile, media, insights, competitor and
hashtag research) and a two-step publishing flow (private container, then a
gated publish) to Claude. Configuration lives in ig_client.py.

Run: python3 connectors/instagram-graph/server.py   (stdio transport)
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import anyio  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

from ig_client import IGClient, IGError, mask, redact, scrub  # noqa: E402

mcp = FastMCP("instagram-graph")
_client: IGClient | None = None


def client() -> IGClient:
    global _client
    if _client is None:
        _client = IGClient()
    return _client


def _run(fn, *args, **kwargs) -> str:
    """Call the client and return JSON. Outputs are scrubbed: no paging URLs, no tokens."""
    try:
        return json.dumps(scrub(fn(*args, **kwargs)), ensure_ascii=False, indent=1)
    except IGError as e:
        return json.dumps({"error": redact(str(e)), "code": e.code, "subcode": e.subcode}, ensure_ascii=False)
    except Exception as e:  # never let an unexpected error echo a URL with the token
        return json.dumps({"error": f"{type(e).__name__}: {redact(str(e))}"}, ensure_ascii=False)


@mcp.tool()
def ig_list_accounts() -> str:
    """List configured Instagram brands (e.g. ega, adro), their API host, masked token and whether publishing is enabled."""
    return _run(client().list_accounts)


@mcp.tool()
def ig_profile(brand: str) -> str:
    """Profile basics for a brand account: username, followers_count, follows_count, media_count."""
    return _run(client().profile, brand)


@mcp.tool()
def ig_list_media(brand: str, limit: int = 25, since_days: int | None = None) -> str:
    """List recent posts (id, caption, media_product_type REELS/FEED, permalink, timestamp, like/comment counts)."""
    return _run(client().list_media, brand, limit, since_days)


@mcp.tool()
def ig_media_insights(brand: str, media_id: str, media_product_type: str | None = None,
                      metrics: list[str] | None = None) -> str:
    """Insights for one post plus derived ratios (shares/saves/likes per reach, avg watch time, progress to 100K views).
    Pass media_product_type=REELS for reels so watch-time metrics are requested. Unsupported metrics are skipped and listed."""
    return _run(client().media_insights, brand, media_id, metrics, media_product_type)


@mcp.tool()
def ig_recent_performance(brand: str, limit: int = 20, since_days: int | None = 30) -> str:
    """One-call performance table for the analyst: recent posts with insights and derived ratios, sorted by views,
    plus a summary (posts, hits_100k, max and median views)."""
    return _run(client().recent_performance, brand, limit, since_days)


@mcp.tool()
def ig_account_insights(brand: str, since: str, until: str, metrics: list[str] | None = None,
                        period: str = "day", metric_type: str = "total_value", breakdown: str | None = None) -> str:
    """Account-level insights between since/until (YYYY-MM-DD or unix time). Defaults: reach, views, accounts_engaged,
    total_interactions, profile_links_taps with metric_type=total_value. For non-follower reach (the main lever for 100K
    views) call metrics=["reach"], breakdown="follow_type". Account metrics are kept only 90 days — snapshot them."""
    return _run(client().account_insights, brand, since, until, metrics, period, metric_type, breakdown)


@mcp.tool()
def ig_competitor(brand: str, username: str, media_limit: int = 12) -> str:
    """Public profile and recent posts of another professional account via Business Discovery (Facebook Login host only).
    Adds engagement_per_follower per post. Use for benchmarking hooks and formats."""
    return _run(client().competitor, brand, username, media_limit)


@mcp.tool()
def ig_hashtag_top_media(brand: str, hashtag: str, edge: str = "top_media", limit: int = 25) -> str:
    """Top or recent public posts for a hashtag (Facebook Login host only; limit 30 unique hashtags per 7 days per account)."""
    return _run(client().hashtag_top_media, brand, hashtag, edge, limit)


@mcp.tool()
def ig_publishing_limit(brand: str) -> str:
    """How many API publishes the account has used in the current 24h window and its quota."""
    return _run(client().publishing_limit, brand)


@mcp.tool()
def ig_create_reel_container(brand: str, caption: str, video_url: str | None = None, video_path: str | None = None,
                             cover_url: str | None = None, thumb_offset_ms: int | None = None,
                             share_to_feed: bool = True, collaborators: list[str] | None = None,
                             audio_name: str | None = None, trial_graduation: str | None = None,
                             is_ai_generated: bool = False, is_paid_partnership: bool = False,
                             branded_content_sponsor_ids: list[str] | None = None, location_id: str | None = None) -> str:
    """Upload a Reel into a PRIVATE container (nothing is posted; containers expire after 24h). Give either a public
    video_url or a local video_path (resumable upload; documented for Facebook Login). trial_graduation=MANUAL or
    SS_PERFORMANCE makes it a Trial Reel shown to non-followers first. Set is_ai_generated for AI imagery and
    is_paid_partnership (+ branded_content_sponsor_ids, max 2) for paid collabs — Korean law still needs '광고' text
    at the start of the caption and in the video. location_id = the venue's Facebook Page ID (tag EGA Brain Sauna).
    Max 5 hashtags, 2,200 chars. Returns container_id."""
    return _run(client().create_reel, brand, caption, video_url, video_path, cover_url, thumb_offset_ms,
                share_to_feed, collaborators, audio_name, trial_graduation, is_ai_generated, is_paid_partnership,
                branded_content_sponsor_ids, location_id)


@mcp.tool()
def ig_create_carousel_container(brand: str, caption: str, items: list[dict],
                                 collaborators: list[str] | None = None, is_ai_generated: bool = False,
                                 is_paid_partnership: bool = False, branded_content_sponsor_ids: list[str] | None = None,
                                 location_id: str | None = None) -> str:
    """Create a PRIVATE carousel container from 2-10 items (API limit), each {"image_url": "<public .jpg>", "alt_text": ...}
    or {"video_url": ...}. Images must be JPEG, sRGB, <= 8 MB. Nothing is posted. Returns container_id."""
    return _run(client().create_carousel, brand, caption, items, collaborators, is_ai_generated, is_paid_partnership,
                branded_content_sponsor_ids, location_id)


@mcp.tool()
async def ig_container_status(brand: str, container_id: str, wait: bool = False) -> str:
    """Processing status of a container: IN_PROGRESS, FINISHED, ERROR, EXPIRED or PUBLISHED. wait=true polls once a minute
    for up to 5 minutes (Meta guidance)."""
    c = client()
    fn = c.wait_until_ready if wait else c.container_status
    # Run in a worker thread so a 5-minute wait does not block other tool calls.
    return await anyio.to_thread.run_sync(lambda: _run(fn, brand, container_id))


@mcp.tool()
def ig_publish(brand: str, container_id: str, human_approval: str) -> str:
    """PUBLIC, IRREVERSIBLE: publish a FINISHED container to the brand's Instagram.
    Only call after the human explicitly approved this exact post in the conversation; put their approval words in
    human_approval. The server refuses unless IG_PUBLISH_ENABLED=1 (otherwise returns a dry run)."""
    if not human_approval or len(human_approval.strip()) < 2:
        return json.dumps({"error": "human_approval is required: quote the user's explicit approval."})
    return _run(client().publish, brand, container_id)


@mcp.tool()
def ig_refresh_token(brand: str, reveal: bool = False) -> str:
    """Refresh a long-lived Instagram Login token (valid 60 days; refresh after it is 24h old). The new token must be
    saved to IG_<BRAND>_TOKEN by the user. reveal=false returns it masked."""
    try:
        res = client().refresh_token(brand)
    except IGError as e:
        return json.dumps({"error": redact(str(e)), "code": e.code}, ensure_ascii=False)
    if not reveal and "access_token" in res:
        res = {**res, "access_token": mask(res["access_token"])}
    return json.dumps(res, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    mcp.run()
