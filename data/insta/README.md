# data/insta — 학습 루프 데이터

## content-log.jsonl (패키지/게시물 1개 = 1줄, `id`=패키지 폴더명. producer가 제작 시 행 생성, 게시·분석 시 같은 행을 갱신)
```json
{"id": "2026-10-07-sauna-myth", "brand": "ega", "date": "2026-10-07", "format": "REELS|CAROUSEL",
 "pillar": "1", "hook_id": "ega-h01", "hypothesis": "...", "experiment": "hook|first_frame|length|format",
 "trial": "MANUAL|SS_PERFORMANCE|null", "variants": [{"id": "A", "media_id": null}], "paid": false,
 "status": "planned|produced|blocked|approved|published|dropped", "package": "content/<brand>/<id>/",
 "media_id": null, "permalink": null, "published_at": null,
 "snapshots": [{"measured_at": "2026-10-08T19:30:00+09:00", "age_hours": 24, "views": 0, "reach": 0, "...": "ig_media_insights metrics + derived"}],
 "diagnosis": null}
```
- `snapshots`: 측정할 때마다 1개 추가. 인사이트는 측정 시점의 누적값이므로 `age_hours`(게시 후 경과 시간)를 반드시 함께 기록. Kill/Scale의 '24h'·'72h' 판정은 그 시점에 가장 가까운 스냅샷으로 한다.
- 앱에서 수동 게시한 글은 사람이 준 permalink, 또는 캡션 첫 줄·게시일로 패키지 행과 매칭한다.
- 계정 지표는 Meta가 90일만 보관하므로 이 파일이 장기 기록이다.

## hooks.json
훅 라이브러리와 성과. id 규칙 `<brand>-h<번호>`. analyst가 uses / total_views / best_views / hits_100k / last_used / media_ids 갱신.
