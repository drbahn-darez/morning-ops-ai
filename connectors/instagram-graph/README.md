# instagram-graph — Instagram Platform API MCP 커넥터

브랜드 인스타그램(EGA, adro)의 성과 조회·경쟁 분석·업로드·게시를 Claude에 연결합니다. 표준 라이브러리 + `mcp` 패키지만 사용합니다.

> 스펙 기준일 2026-10-04 (Graph API **v26.0**, 2026-07-29 출시). 리서치 환경에서 developers.facebook.com 직접 열람이 막혀 Meta 공식 SDK(v26.0)와 문서 사본으로 확인했습니다. 운영 전 아래 "미확정 항목"을 실제 계정으로 한 번 검증하세요.

## 도구

| 도구 | 종류 | 설명 |
|---|---|---|
| `ig_list_accounts` | 읽기 | 설정된 브랜드, 호스트, 마스킹된 토큰, 게시 허용 여부 |
| `ig_profile` | 읽기 | 팔로워·게시물 수 |
| `ig_list_media` | 읽기 | 최근 게시물 (since_days 필터) |
| `ig_media_insights` | 읽기 | 게시물 인사이트 + 파생 지표(공유/도달, 저장/도달, 평균 시청 초, 스킵률, 10만 진척) |
| `ig_recent_performance` | 읽기 | 최근 게시물 성과표 한 번에 (분석가용) |
| `ig_account_insights` | 읽기 | 계정 지표. `metrics=["reach"], breakdown="follow_type"` 로 비팔로워 도달 |
| `ig_competitor` | 읽기 | Business Discovery — 경쟁 계정 공개 지표 (Facebook 로그인만) |
| `ig_hashtag_top_media` | 읽기 | 해시태그 인기/최신 게시물 (Facebook 로그인만, 7일 30개 해시태그) |
| `ig_publishing_limit` | 읽기 | 24시간 게시 쿼터 |
| `ig_create_reel_container` | 업로드(비공개) | 릴스 컨테이너. 로컬 파일 업로드, Trial Reels, AI 표시, 유료 파트너십 |
| `ig_create_carousel_container` | 업로드(비공개) | 캐러셀 2~10장 (JPEG 공개 URL) |
| `ig_container_status` | 읽기 | 처리 상태 (wait=true면 1분 간격 최대 5분) |
| `ig_publish` | **공개 게시** | 이중 게이트: `IG_PUBLISH_ENABLED=1` + Claude Code 권한 확인(ask) |
| `ig_refresh_token` | 토큰 | Instagram 로그인 토큰 60일 연장 |

## 설정 (대표님/담당자)

### 1. 어떤 로그인 경로를 쓸까 — **Facebook 로그인 권장**

| | Facebook Login for Business (권장) | Instagram Login |
|---|---|---|
| 호스트 | graph.facebook.com | graph.instagram.com |
| 필요 조건 | 인스타 프로페셔널 계정이 Facebook 페이지에 연결 | 프로페셔널 계정만 |
| 경쟁 계정(Business Discovery) | ✅ | ❌ |
| 해시태그 검색 | ✅ (Instagram Public Content Access 기능 필요) | ❌ |
| 로컬 파일 업로드(resumable) | ✅ 문서화 | 문서 상충 — 공개 URL 권장 |
| 토큰 수명 | 시스템 사용자 토큰은 만료 없음 가능 | 60일, 갱신 필요 |
| 권한 | instagram_basic, instagram_content_publish, instagram_manage_insights, pages_show_list, pages_read_engagement (+ Business Manager 경유 시 ads_read) | instagram_business_basic, instagram_business_content_publish, instagram_business_manage_insights |

자사 계정만 쓰면 **Standard Access**로 충분합니다(앱 검수 불필요). 해시태그 검색은 앱 검수가 필요합니다.

### 2. 토큰 발급 (Facebook 로그인, 무인 자동화용)
1. business.facebook.com → 비즈니스 설정 → 시스템 사용자 생성 → EGA/adro 페이지와 인스타 계정 자산 할당
2. developers.facebook.com에서 비즈니스 앱 생성 → Instagram 제품 추가
3. 시스템 사용자 → 토큰 생성 → 위 권한 선택
4. 인스타 비즈니스 계정 ID 확인: `GET /me/accounts?fields=instagram_business_account`

### 3. 클라우드 환경에 등록
세션 제목 표시줄의 환경 메뉴 → Edit:
- **환경 변수** (채팅에 토큰을 붙여넣지 마세요)
  ```
  IG_EGA_TOKEN=...      IG_EGA_USER_ID=1784...
  IG_ADRO_TOKEN=...     IG_ADRO_USER_ID=1784...
  # 선택: IG_EGA_HOST=facebook|instagram (기본: 토큰이 IG로 시작하면 instagram, 아니면 facebook)
  # 선택: IG_API_VERSION=v26.0
  # 게시까지 허용할 때만: IG_PUBLISH_ENABLED=1
  ```
- **네트워크 → Custom → 허용 도메인**: `graph.facebook.com`, `graph.instagram.com`, `rupload.facebook.com` (기본 패키지 매니저 목록 유지)
- 새 세션부터 적용됩니다.

맥에서 Claude Code로 쓸 때: `pip install mcp` 후 같은 환경 변수를 셸에 설정. 저장소 루트의 `.mcp.json`이 서버를 자동 등록합니다.

## 안전장치
- 컨테이너 생성은 **비공개**입니다(24시간 후 만료). 공개는 `ig_publish`만 합니다.
- `ig_publish`: 환경 변수 `IG_PUBLISH_ENABLED=1`이 아니면 dry run. 게다가 `.claude/settings.json`에서 `ask` 권한이라 매번 사람 확인을 받습니다. 컨테이너가 `FINISHED`가 아니면 거부합니다.
- 캡션: 2,200자, **해시태그 5개 초과 시 거부**(2025-12 인스타 정책; API 문서는 아직 30개라고 함).
- 캐러셀: API는 **2~10장**(앱은 20장), **JPEG만**(sRGB, 8MB 이하, 4:5~1.91:1). 렌더러 기본 출력이 JPEG입니다.
- 릴스: MP4/MOV, H.264/HEVC, AAC 48kHz, 3초~15분, 300MB 이하, moov atom 선두 → `tools/reels/prepare.sh`로 정규화. **3분 초과는 비팔로워 추천 제외.**

## 지표 메모
- 릴스 유효 지표: views, reach, likes, comments, shares, saved, total_interactions, ig_reels_avg_watch_time, ig_reels_video_view_total_time, reels_skip_rate, reposts, crossposted_views, facebook_views
- 릴스에 follows / profile_visits / profile_activity 요청 시 에러 100 → 요청하지 않음
- 폐기: impressions, plays, clips_replays_count, ig_reels_aggregated_all_plays_count (2025-04-21), video_views (2025-01-08)
- 지원 안 되는 지표는 자동으로 건너뛰고 `unsupported_metrics`로 보고합니다.
- 계정 지표는 90일만 보관 → 분석가가 24h/72h/7d 스냅샷을 `data/insta/content-log.jsonl`에 저장합니다.

## 미확정 항목 (첫 실계정 연결 시 확인)
- Instagram 로그인 토큰으로 resumable 업로드가 되는지 (문서 상충)
- `content_publishing_limit`의 실제 quota_total (문서상 100 vs 50)
- `reels_skip_rate`가 값이 나오는 최소 조회 수
- Trial Reel의 졸업(팔로워 공개) 상태를 API로 읽을 수 있는지 — 현재 확인된 필드 없음

## 테스트
```bash
python3 -m unittest connectors/instagram-graph/test_ig_client.py   # 가짜 API로 25개 테스트
```
