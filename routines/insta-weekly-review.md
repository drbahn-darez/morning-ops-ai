# 인스타 주간 리뷰 루틴 (신규)

- 스케줄: `CRON_TZ=Asia/Seoul 52 8 * * 1` = 매주 월요일 08:52 KST (아침 브리핑과 겹치지 않게)
- 실행 방식: 매 실행마다 새 세션
- **소스 저장소**: `drbahn-darez/morning-ops-ai` (insta-growth 스킬·서브에이전트·커넥터가 로드되도록 필수)
- 커넥터: Supermetrics (Instagram Insights 로그인 완료 후), Slack, Google Drive
- 환경 변수(선택, 게시물 단위 진단 정확도↑): `IG_EGA_TOKEN`, `IG_EGA_USER_ID`, `IG_ADRO_TOKEN`, `IG_ADRO_USER_ID` + 허용 도메인 `graph.facebook.com`, `graph.instagram.com`
- **만드는 방법(대표님 직접)**: 에이전트가 만든 루틴에는 커넥터가 붙지 않아(이 조직 설정), claude.ai → Code → Routines → New에서 아래 프롬프트·소스·커넥터로 생성
- 게시는 하지 않는다 — 분석과 플랜, 초안 패키지까지만. 게시는 사람 승인 후 대화형 세션에서.

## Prompt

```
Use the insta-growth skill in WEEKLY mode for both brands (ega, adro), in Korean.

For each brand:
1. Run the insta-analyst subagent for the last 7 days (and 30-day baseline). Data: instagram-graph connector if IG_<BRAND>_TOKEN is set, otherwise Supermetrics instagram_insights (ds_id=IGI). If neither returns data, do not invent numbers — say which connection is missing and skip to step 3.
2. Run the insta-strategist subagent for next week (ISO week) and write content/<brand>/plans/<week>.md.
3. Run insta-producer for the two highest-priority briefs and insta-reviewer on each package. Do not publish anything and do not call ig_publish or container-creation tools.
4. Commit plans, packages (without out/), and updated data/insta/*.json to a new branch claude/insta-<week> and open a draft PR.

Finally send me one Slack DM (ADRO workspace, user U05AU0BMGGM) with, per brand: 10만+ 릴스 수 / 최고 조회 / 중앙 조회 (or "데이터 연결 필요"), Top 1 and Bottom 1 with the one-line reason, next week's 3 actions, packages waiting for my approval with their paths, and any compliance FLAGs that need legal review. If a step fails, list it on a final line "실패: <step> — <reason>".
```
