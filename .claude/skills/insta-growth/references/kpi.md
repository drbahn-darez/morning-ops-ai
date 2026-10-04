# KPI 정의

## North Star
**월간 10만+ 조회 릴스 수 (브랜드별)**
- 1단계 목표: 운영 시작 8주 안에 첫 10만 릴스 1편
- 2단계 목표: 월 2편 이상을 3개월 연속
- 조회 = Instagram **Views** (재생 시작·재시청 포함). 유니크 기준이 아니다. 유니크는 `reach`(일부 화면에서는 'Viewers').

## 선행지표 (매주)
| 지표 | 정의 | API 소스 | 방향 |
|---|---|---|---|
| 발행 수 | 정식 릴스 + Trial 수 | content-log | 월 20+ |
| 스킵률 | 첫 3초 안에 넘긴 **시청자** 비율 (조회수 아님) | `reels_skip_rate` | ↓ |
| 평균 시청 시간 | 초 단위, 영상 길이 대비 % | `ig_reels_avg_watch_time` (ms) | ↑ |
| 공유/도달 | sends per reach (DM 공유) | `shares` / `reach` | ↑ 비팔로워 확산 핵심 |
| 좋아요/도달 | | `likes` / `reach` | ↑ 팔로워 노출 핵심 |
| 저장/도달 | | `saved` / `reach` | ↑ 캐러셀 핵심 |
| 재노출 배수 | 조회 / 도달 | `views` / `reach` | 캐러셀 재노출·재시청 신호 |
| 검수 승인율 | 첫 검수 APPROVE 비율 | review.md | ↑ 제작 품질 |
| 추천 적격성 | 계정 상태 '추천 가능' | 앱에서 수동 확인 | 항상 유지 |

**임계값은 절대값이 아니라 자체 기준선(최근 30일 중앙값) 대비로 판단한다** — playbook.md §4. 벤더 수치는 참고용이며 [벤더]로 표기한다.

[벤더·미검증] 참고 — Socialinsider 2026 H1 브랜드 릴스 평균 조회와 도달률 (표본 규모 표기가 보도마다 다름, 기준선으로 쓰지 말 것):
| 팔로워 | 평균 조회 | 도달률 |
|---|---|---|
| 1~5K | 580 | 9.78% |
| 5~10K | 1,000 | 7.55% |
| 10~50K | 2,460 | 7.10% |
| 50~100K | 6,095 | 5.60% |
| 100K~1M | 16,035 | 5.00% |
출처: socialinsider.io/blog/instagram-reels-statistics

## 비즈니스 연결 지표 (월간)
- **EGA**: 프로필 링크 탭(`profile_links_taps`), 브레인 사우나 예약 중 인스타 유입(UTM `utm_source=instagram`), DM 문의 수. 3개월 소셜 누적 조회 목표 438만(런칭 기획안) 대비 진척.
- **adro**: 프로필 방문, 웹사이트 클릭, AOX 출시 알림/가입 중 인스타 유입(UTM), 해외(영문) 댓글·DM 비중.

## 데이터 연결 방법
1. **Supermetrics (분석만, 지금 바로)** — claude.ai에 연결된 Supermetrics에서 Instagram Insights(IGI) 로그인, 경쟁 계정·해시태그는 Instagram Public Data(IGPD2) 로그인. 스킵률·리포스트 지원 [2차 보도].
2. **instagram-graph 커넥터 (성과 + 경쟁 + 게시)** — 상세 절차는 `connectors/instagram-graph/README.md`. 요약:
   - **기본 경로: Facebook Login for Business** (graph.facebook.com). 인스타 프로페셔널 계정을 페이지에 연결 → 비즈니스 설정의 **시스템 사용자 토큰**(만료 없음 가능) → Business Discovery(경쟁 계정)·해시태그 검색·로컬 영상 업로드까지 가능
   - 대안: Instagram Login (graph.instagram.com, 60일 토큰) — 경쟁 계정·해시태그 조회 불가, 로컬 영상 업로드 미확정(공개 URL 사용)
   - 클라우드 환경 변수: `IG_EGA_TOKEN`, `IG_EGA_USER_ID`, `IG_ADRO_TOKEN`, `IG_ADRO_USER_ID` (채팅에 토큰을 붙여넣지 않는다)
   - 네트워크 허용 도메인: `graph.facebook.com`, `graph.instagram.com`, `rupload.facebook.com`
   - 게시까지 허용할 때만 `IG_PUBLISH_ENABLED=1` (그래도 매번 사람 확인)
