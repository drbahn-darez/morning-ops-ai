---
name: insta-growth
description: |
  브랜드 인스타그램(EGA, adro) 릴스 1편 10만 조회를 반복 달성하기 위한 기획·제작·검수·게시·분석 운영 스킬.
  전략가/제작자/검수자/분석가 서브에이전트와 instagram-graph 커넥터, 캐러셀 렌더러, 컴플라이언스 게이트를 묶어 실행한다.

  다음 상황에서 반드시 이 스킬을 사용하라:
  - "인스타", "인스타그램", "릴스", "캐러셀", "피드 게시물", "Trial Reels" 언급
  - "10만 조회", "조회수 올리기", "바이럴", "도달 늘리기", "알고리즘" 관련 요청
  - "이번 주 인스타 플랜", "콘텐츠 캘린더", "훅 만들어줘", "캡션 써줘", "캐러셀 만들어줘"
  - "인스타 성과 봐줘", "왜 안 터졌어", "주간 인스타 리포트"
  - "인스타 올려줘", "게시해줘", "예약해줘"
  - EGA 브레인 사우나·NMN 콘텐츠, adro 바디킷·AOX·탑기어 콘텐츠를 인스타용으로 만들 때
---

# insta-growth — 릴스 10만 조회 운영 시스템

**목표 정의.** "10만 조회"는 인스타그램 **Views**(재생 시작·재시청 포함, 최소 시청 시간 없음) 기준 **단일 릴스 100,000회**다. 노출(impressions)·plays는 2025-04-21부로 API에서 폐기되어 쓰지 않는다. → 상세 `references/kpi.md`

**현실 인식.** 10만은 평균이 아니라 **비팔로워 추천에서 나오는 상위 꼬리값**이다. Socialinsider(벤더, 2026 H1, 미검증) 기준 팔로워 10~50K 브랜드의 릴스 평균 조회는 약 2,460회다. 그래서 이 시스템은 소수의 완벽한 게시물이 아니라 **시도 횟수(N) × 편당 히트 확률(p)** 을 동시에 올리는 구조로 설계되어 있다. → `references/playbook.md`

## 구성 요소

| 구성 | 위치 | 역할 |
|---|---|---|
| 전략가 | `.claude/agents/insta-strategist.md` | 주간 브리프 5~7개 (가설·훅·실험 변수) |
| 제작자 | `.claude/agents/insta-producer.md` | 브리프 → 캐러셀 JPEG / 릴스 스크립트·샷리스트·커버 / 캡션 패키지 |
| 검수자 | `.claude/agents/insta-reviewer.md` | 훅·가독성·브랜드·규제 채점 → APPROVE/REVISE/REJECT |
| 분석가 | `.claude/agents/insta-analyst.md` | 게시 후 시점별 스냅샷 진단, 훅 리더보드, Kill/Scale |
| 커넥터 | `connectors/instagram-graph/` (MCP `instagram-graph`) | 성과 조회, 경쟁 계정, 컨테이너 업로드, 게이트된 게시 |
| 보조 데이터 | Supermetrics `instagram_insights` (IGI / IGPD2) | 커넥터 토큰이 없을 때 분석 대체 |
| 렌더러 | `tools/carousel/render.mjs` | 캐러셀 스펙 JSON → 1080×1350 JPEG + PNG 콘택트시트, 9:16 릴스 커버 |
| 규제 게이트 | `tools/compliance/check.py` + `rules.json` | REJECT/FLAG 자동 판정 |
| 기록 | `data/insta/content-log.jsonl`, `data/insta/hooks.json` | 게시물·훅 성과 누적 → 학습 루프 |
| EGA 릴스 렌더 | `ega-shorts` 스킬 | 정보형 릴스(9:16) 제작 파이프라인 재사용 |

## 모드 판별

| 요청 | 모드 | 실행 |
|---|---|---|
| 플랜, 캘린더, 기획, 전략 | PLAN | `insta-strategist` 서브에이전트 |
| 만들어줘, 캐러셀, 스크립트, 캡션, 훅 | PRODUCE | `insta-producer` → `insta-reviewer` (REVISE면 최대 2회 루프) |
| 검수, 괜찮아? | REVIEW | `insta-reviewer` |
| 올려줘, 게시, 예약 | PUBLISH | 아래 게시 절차 (사람 승인 필수) |
| 성과, 리포트, 왜 안 됐어 | ANALYZE | `insta-analyst` |
| 한 주 통째로 돌려줘 | WEEKLY | ANALYZE → PLAN → PRODUCE×N → REVIEW×N, 게시는 승인 대기 |

여러 브리프를 제작할 때는 제작자 서브에이전트를 브리프별로 병렬 실행하고, 각 결과를 검수자에게 넘긴다.

## 브랜드
- `ega` → `references/brands/ega.md` (웰니스·NMN·브레인 사우나, 국문 중심)
- `adro` → `references/brands/adro.md` (에어로·카본 바디킷·AOX, 국/영문)
브랜드가 불명확하면 한 줄로 묻는다. 두 브랜드 콘텐츠를 섞지 않는다.

## 게시 절차 (PUBLISH) — 사람 승인 없이는 절대 게시하지 않는다
1. 패키지의 `review.md`가 `APPROVE`인지 확인. 아니면 중단.
2. 사람에게 최종 확인 요청: 첫 장/커버 이미지, 캡션 전문, 게시 시간, **컴플라이언스 FLAG 사유 전부**(review.md의 FLAGS), Trial 여부와 **졸업 방식**을 보여준다. Trial 기본값은 `MANUAL`(72시간 후 사람이 앱에서 팔로워 공유 결정). `SS_PERFORMANCE`(인스타가 자동 공유)는 사람이 명시적으로 고른 경우에만.
3. 사람이 명시적으로 승인한 경우에만:
   - 릴스: `ig_create_reel_container`(로컬 파일이면 `video_path`; Trial이면 `trial_graduation`) → `ig_container_status(wait=true)` → `ig_publish(human_approval="<사람의 승인 문구>")`
   - 캐러셀: 이미지가 공개 URL이어야 한다(API 제약). URL이 없으면 사람에게 앱에서 직접 올리도록 패키지 경로를 주고 종료.
4. 게시 후 `data/insta/content-log.jsonl`의 패키지 행(제작 시 producer가 만든 `status: produced` 행)에 `media_id`, `permalink`, `published_at`, `status: published` 기록. 앱에서 수동 게시했다면 사람에게 permalink를 물어 같은 행에 기록한다.
5. 시점별 진단 예약: 세션에서 `send_later`(claude-code-remote)를 쓸 수 있으면 게시 +24h, +72h에 "insta-analyst로 <media_id> 진단" 메시지를 예약한다. 없으면 주간 루틴이 측정 시점의 게시 경과 시간(`age_hours`)과 함께 기록한다.
6. `IG_PUBLISH_ENABLED`가 꺼져 있으면 dry run 결과를 그대로 보고하고, 앱 수동 게시 안내 + permalink 기록 요청으로 마무리.

## 데이터가 없을 때
- instagram-graph 토큰이 없으면 Supermetrics(IGI)로, 그것도 미인증이면 **숫자를 만들지 말고** 연결 방법만 안내한다 (`references/kpi.md` 하단).
- 벤치마크·알고리즘 주장은 `references/playbook.md`의 출처 달린 내용만 인용한다. [미검증] 표시는 그대로 유지한다.

## 산출물 규칙
- 보고는 숫자·결론·다음 액션 순서. 좋은 말보다 원인과 결정.
- 파일: 플랜 `content/<brand>/plans/<YYYY-Www>.md`, 패키지 `content/<brand>/<YYYY-MM-DD>-<slug>/`, 렌더 결과 `…/out/`(git 제외).
