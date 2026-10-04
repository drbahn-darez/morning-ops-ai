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
| 스킵률 | 첫 3초 안에 이탈한 조회 비율 | `reels_skip_rate` | ↓ |
| 평균 시청 시간 | 초 단위, 영상 길이 대비 % | `ig_reels_avg_watch_time` (ms) | ↑ |
| 공유/도달 | sends per reach (DM 공유) | `shares` / `reach` | ↑ 비팔로워 확산 핵심 |
| 좋아요/도달 | | `likes` / `reach` | ↑ 팔로워 노출 핵심 |
| 저장/도달 | | `saved` / `reach` | ↑ 캐러셀 핵심 |
| 재노출 배수 | 조회 / 도달 | `views` / `reach` | 캐러셀 재노출·재시청 신호 |
| 검수 승인율 | 첫 검수 APPROVE 비율 | review.md | ↑ 제작 품질 |
| 추천 적격성 | 계정 상태 '추천 가능' | 앱에서 수동 확인 | 항상 유지 |

**임계값은 절대값이 아니라 자체 기준선(최근 30일 중앙값) 대비로 판단한다** — playbook.md §4. 벤더 수치는 참고용이며 [벤더]로 표기한다.

[벤더] 참고 — Socialinsider 2026 H1 브랜드 릴스 평균 조회와 도달률:
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
1. **instagram-graph 커넥터 (권장, 게시까지 가능)**
   - Meta 개발자 앱 → Instagram 제품 → "Instagram 로그인을 사용한 API 설정" → 비즈니스/크리에이터 계정 연결 → 장기 토큰(60일) 발급
   - 클라우드 환경 설정 → 환경 변수 `IG_EGA_TOKEN`, `IG_EGA_USER_ID` (adro는 `IG_ADRO_…`) 추가
   - 네트워크 허용 도메인: `graph.instagram.com`, `graph.facebook.com`, `rupload.facebook.com`
   - 경쟁 계정·해시태그 조회가 필요하면 Facebook 로그인 경로 토큰 + `IG_<BRAND>_HOST=facebook`
   - 상세: `connectors/instagram-graph/README.md`
2. **Supermetrics (분석만, 바로 가능)** — claude.ai에 이미 연결된 Supermetrics에서 Instagram Insights(IGI)·Instagram Public Data(IGPD2) 로그인. 2026-04부터 스킵률·리포스트 지원 [2차 보도].
