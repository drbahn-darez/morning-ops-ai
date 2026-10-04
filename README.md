# morning-ops-ai

윤반석(Bahn) 운영 에이전트 저장소 — 스킬, 서브에이전트, 커넥터, 루틴 정의를 버전 관리합니다. 이 저장소로 Claude Code 세션을 열면 `.claude/skills`, `.claude/agents`, `.mcp.json`이 자동으로 로드됩니다.

## 전체 구조

```
                               ┌──────────────────────────────┐
                               │       윤반석 (Claude 계정)      │
                               └──────────────┬───────────────┘
        ┌───────────────────────┬─────────────┴──────────┬────────────────────────────┐
        ▼                       ▼                        ▼                            ▼
 ⏰ 루틴(자동)              🏢 사업별 스킬            📊 경영 공통 스킬          📸 인스타 성장 시스템 (신규)
 매일 아침 브리핑           [adro] aox-launch-       weekly-report              insta-growth 스킬 (오케스트레이터)
 09:10 KST                  expansion                okr-kpi-generator          │
 Gmail·Calendar·Drive       [EGA] ega-campaign                                  ├─ insta-strategist  주간 플랜
 → Slack DM                 [EGA] ega-shorts ───────────────────────────┐       ├─ insta-producer    제작 패키지
 (v02 스펙:                                                              │       ├─ insta-reviewer    검수 게이트
  routines/)                                                             │       └─ insta-analyst     성과·학습
                                                                         │                │
                                                     EGA 정보형 릴스 렌더 재사용 ◄─────────┤
                                                                                          ▼
                                     ┌──────────────────────────────────────────────────────────────┐
                                     │ 도구 / 커넥터                                                  │
                                     │ instagram-graph MCP  성과·경쟁·업로드·게시(이중 게이트)          │
                                     │ Supermetrics (IGI/IGPD2)  분석 대체 경로                        │
                                     │ tools/carousel  스펙 JSON → 1080×1350 JPEG + 콘택트시트          │
                                     │ tools/reels/prepare.sh  릴스 업로드 규격 정규화                  │
                                     │ tools/compliance  REJECT/FLAG 규제 게이트                       │
                                     │ data/insta  content-log · hooks 리더보드 (학습 루프)             │
                                     └──────────────────────────────────────────────────────────────┘
```

## 인스타 10만 조회 루프

```
 분석가 ──► 전략가 ──► 제작자 ──► 검수자 ──► [사람 승인] ──► 게시(Trial 먼저) ──► 24h/72h/7d 스냅샷 ──┐
   ▲   주간 진단   브리프 5~7   패키지     APPROVE/REVISE/REJECT        비팔로워 테스트               │
   └────────────────────────────────── hooks.json · content-log.jsonl 갱신 ◄─────────────────────────┘
```

- 목표: 단일 릴스 Views 100,000 (`.claude/skills/insta-growth/references/kpi.md`)
- 운영 모델·확률 모델·Kill/Scale 규칙: `references/playbook.md`
- 브랜드 팩: `references/brands/ega.md`, `references/brands/adro.md`

## 디렉터리

| 경로 | 내용 |
|---|---|
| `.claude/skills/` | aox-launch-expansion, ega-campaign, ega-shorts, okr-kpi-generator, weekly-report, **insta-growth** |
| `.claude/agents/` | insta-strategist, insta-producer, insta-reviewer, insta-analyst |
| `connectors/instagram-graph/` | Instagram Platform API MCP 서버 (Graph API v26.0) + 오프라인 테스트 |
| `tools/carousel/` | 헤드리스 캐러셀 렌더러 (EGA·adro 테마) |
| `tools/reels/` | 릴스 업로드 규격 정규화 (ffmpeg) |
| `tools/compliance/` | 규제·브랜드 보이스 자동 게이트 |
| `routines/` | 루틴 프롬프트 사양 (claude.ai 루틴 UI에 적용) |
| `data/insta/` | 게시물 로그, 훅 리더보드 |
| `content/<brand>/` | 주간 플랜, 게시물 패키지 (렌더 결과 `out/`은 git 제외) |

## 시작하기 (대표님이 할 일)
1. **Supermetrics 인스타 연결** (분석 즉시 가능): claude.ai Supermetrics 커넥터에서 Instagram Insights 로그인
2. **instagram-graph 토큰** (게시까지): `connectors/instagram-graph/README.md` 의 설정 절차 → 환경 변수 `IG_EGA_TOKEN`, `IG_EGA_USER_ID`, `IG_ADRO_TOKEN`, `IG_ADRO_USER_ID`, 네트워크 허용 도메인 3개
3. **아침 브리핑 v02 적용**: `routines/morning-brief-v02.md`
4. 이 저장소로 새 세션 → "EGA 이번 주 인스타 플랜 짜줘"

## 테스트
```bash
python3 -m unittest connectors/instagram-graph/test_ig_client.py
python3 -m unittest tools/compliance/test_check.py
node tools/carousel/render.mjs tools/carousel/examples/ega-sample.json /tmp/ega
```
