# 인스타 보조 루틴 (선택)

주간 리뷰(`insta-weekly-review.md`)를 보완하는 루틴. 모두 **게시 권한 없음**. 에이전트가 만든 루틴에는 커넥터가 붙지 않으므로(이 조직 설정) claude.ai → Code → Routines에서 직접 생성. 소스 저장소 `drbahn-darez/morning-ops-ai`, 커넥터 Supermetrics·Slack.

| 루틴 | 스케줄 | 목적 |
|---|---|---|
| 일일 스냅샷 | `CRON_TZ=Asia/Seoul 47 9 * * *` | 게시 후 ~24h·~72h·~7d가 된 게시물의 인사이트를 경과 시간과 함께 기록하고 Kill/Scale 후보 알림. 인사이트는 최대 48h 늦게 반영되므로 72h·7d가 확정치 |
| 토큰 점검 | `CRON_TZ=Asia/Seoul 41 9 * * 1` | Instagram Login 토큰만 해당: 45일 넘으면 `ig_refresh_token`. 60일 지나 만료되면 갱신 불가(재로그인) |
| 월간 플랫폼 점검 | `CRON_TZ=Asia/Seoul 43 9 1 * *` | Instagram Platform changelog, Graph API 버전 표, 추천 가이드라인 변경 확인 → 바뀐 점을 PR로 제안 |

## 일일 스냅샷 Prompt
```
Use the insta-growth skill. For brands ega and adro, find posts in data/insta/content-log.jsonl with status "published" whose age is about 24h, 72h or 7d (±12h) and that have no snapshot near that age yet. For each, call ig_media_insights (instagram-graph) or Supermetrics instagram_insights (IGI) and append {measured_at, age_hours, metrics, derived} to that row's snapshots. Apply playbook.md §4 (Kill/Scale) and commit the updated log to branch claude/insta-snapshots with a draft PR. Never publish anything. Send one Slack DM (ADRO workspace, user U05AU0BMGGM) only if there is a KILL, SCALE or 10만 후보 decision, listing post, decision and the two numbers behind it. If data access fails, DM "인스타 스냅샷 실패: <reason>".
```

## 월간 플랫폼 점검 Prompt
```
Check for changes that affect connectors/instagram-graph and .claude/skills/insta-growth: the Instagram Platform changelog, the Graph API versions table (current version, expiry of the pinned IG_API_VERSION), deprecated or new insights metrics, content-publishing limits, Trial Reels parameters, and Instagram's recommendation and originality guidelines. Also re-check the [미검증] items listed in references/playbook.md against primary pages. Open a draft PR with concrete edits (and tests for code changes). Never publish anything. Send one Slack DM (ADRO workspace, user U05AU0BMGGM) with a 3-line summary and the PR link.
```
