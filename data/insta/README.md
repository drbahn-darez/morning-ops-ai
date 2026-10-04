# data/insta — 학습 루프 데이터

## content-log.jsonl (게시물 1개 = 1줄, append-only; 같은 media_id 행은 analyst가 갱신)
```json
{"id": "ega-2026-10-07-sauna-myth", "brand": "ega", "date": "2026-10-07", "format": "REELS|CAROUSEL",
 "pillar": "1", "hook_id": "ega-h01", "hypothesis": "...", "experiment": "hook|first_frame|length|format",
 "trial": "SS_PERFORMANCE|MANUAL|null", "paid": false, "status": "planned|produced|approved|published|dropped",
 "media_id": null, "permalink": null, "published_at": null,
 "metrics_24h": {}, "metrics_72h": {}, "metrics_7d": {}, "diagnosis": null}
```
- metrics_* 에는 `ig_media_insights` 의 `metrics` + `derived` 를 그대로 저장 (views, reach, shares, saved, reels_skip_rate, avg_watch_time_s …)
- 계정 지표는 Meta가 90일만 보관하므로 이 파일이 장기 기록이다.

## hooks.json
훅 라이브러리와 성과. id 규칙 `<brand>-h<번호>`. analyst가 uses / total_views / best_views / hits_100k / last_used / media_ids 갱신.
