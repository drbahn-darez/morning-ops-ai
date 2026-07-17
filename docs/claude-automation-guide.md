# Claude 프로덕트 개발 자동화 가이드

이 문서는 이 리포지토리에 세팅된 Claude 기반 개발 자동화의 구성과 사용법을 설명합니다.

## 전체 그림

Claude 자동화는 두 축으로 동작합니다.

1. **로컬/웹 개발 (Claude Code)** — 터미널·IDE·claude.ai/code에서 대화형으로 개발. `CLAUDE.md`, `.claude/` 설정이 여기에 적용됩니다.
2. **GitHub 자동화 (Claude Code GitHub Actions)** — 이슈·PR에서 `@claude` 멘션에 응답하고, PR을 자동 리뷰합니다. `.github/workflows/`가 여기에 해당합니다.

## 1. 사전 준비

### API 키 등록 (GitHub Actions용)

1. [Anthropic Console](https://console.anthropic.com/)에서 API 키 발급
2. GitHub 리포 → Settings → Secrets and variables → Actions → **New repository secret**
3. 이름 `ANTHROPIC_API_KEY`, 값에 키 입력

가장 쉬운 방법은 로컬 Claude Code에서 `/install-github-app`을 실행하는 것입니다. GitHub App 설치와 시크릿 등록, 워크플로우 생성을 안내에 따라 한 번에 처리해 줍니다. (이 리포에는 워크플로우 파일이 이미 있으므로 App 설치 + 시크릿 등록만 하면 됩니다.)

### 로컬 Claude Code 설치

```bash
npm install -g @anthropic-ai/claude-code
cd morning-ops-ai
claude
```

## 2. 구성 요소별 설명

### CLAUDE.md — 프로젝트 메모리

Claude Code가 세션 시작 시 자동으로 읽는 파일입니다. 프로젝트 규칙, 개발 워크플로우, 컨벤션을 적어두면 매번 설명할 필요가 없습니다. 팀 규칙이 바뀌면 이 파일을 업데이트하세요. 대화 중 `#`로 시작하는 메시지를 보내면 Claude가 CLAUDE.md에 내용을 추가해 줍니다.

### .claude/settings.json — 권한 설정

- `permissions.allow`: 확인 없이 실행을 허용할 도구 목록 (예: `git status`, 테스트 실행). 반복 확인 프롬프트를 줄여줍니다.
- `permissions.deny`: 접근을 차단할 대상 (예: `.env`, `secrets/`). 비밀값 유출을 방지합니다.

개인용 설정은 `.claude/settings.local.json`에 두면 커밋되지 않습니다.

### .claude/commands/ — 커스텀 슬래시 커맨드

자주 쓰는 워크플로우를 커맨드로 만들어 둔 것입니다. Claude Code 안에서 `/커맨드이름`으로 실행합니다.

| 커맨드 | 사용법 | 설명 |
|---|---|---|
| `/plan-feature` | `/plan-feature 아침 리포트 요약 기능` | 스펙 작성 → 승인 후 구현하는 기획 커맨드 |
| `/fix-issue` | `/fix-issue 42` | 이슈 번호를 받아 분석·수정·테스트·커밋 |
| `/ship` | `/ship` | 테스트·린트 → 커밋 → 푸시 → PR 생성 |

새 커맨드는 `.claude/commands/이름.md` 파일을 추가하면 됩니다. 파일 본문이 프롬프트가 되고, `$ARGUMENTS` 자리에 커맨드 뒤에 입력한 인자가 들어갑니다.

### .github/workflows/claude.yml — @claude 멘션 봇

이슈, 이슈 댓글, PR 댓글, PR 리뷰에서 `@claude`를 멘션하면 Claude가 실행됩니다.

사용 예:

- 이슈 본문에: `@claude 이 기능을 구현하고 PR을 만들어줘`
- PR 댓글에: `@claude 이 함수에서 에러 처리를 개선해줘`
- 이슈 댓글에: `@claude 이 버그의 원인이 뭐야?`

Claude가 코드를 분석하고, 필요하면 브랜치를 만들어 커밋하고 PR을 엽니다.

### .github/workflows/claude-code-review.yml — PR 자동 리뷰

PR이 열리거나 새 커밋이 푸시되면 Claude가 자동으로 코드 리뷰를 남깁니다. 버그, 보안 문제, 컨벤션 위반을 중심으로 살펴봅니다.

## 3. 권장 개발 사이클

```
아이디어
  │
  ▼
GitHub 이슈 작성 ──── 또는 로컬에서 /plan-feature
  │                        │
  ▼                        ▼
"@claude 구현해줘"      승인 후 Claude가 구현
  │                        │
  ▼                        ▼
Claude가 PR 생성        /ship 으로 PR 생성
  │                        │
  └────────┬───────────────┘
           ▼
   PR 자동 리뷰 (claude-code-review.yml)
           │
           ▼
   리뷰 반영 ("@claude 리뷰 반영해줘") → 머지
```

## 4. 운영 팁

- **CLAUDE.md를 계속 다듬으세요.** Claude가 같은 실수를 반복하면 규칙으로 적어두는 것이 가장 효과적입니다.
- **작게 나눠 요청하세요.** 하나의 이슈/PR은 하나의 기능·수정에 집중할수록 결과 품질이 좋습니다.
- **자동 리뷰는 보조 수단입니다.** 머지 전 사람의 최종 확인은 유지하세요.
- **비용 관리:** GitHub Actions 실행마다 API 사용량이 발생합니다. 리뷰 워크플로우가 과하면 `paths` 필터나 라벨 조건으로 트리거를 좁히세요.
- **claude.ai/code (웹)에서도 이 리포를 연결해 세션을 시작할 수 있습니다.** 모바일에서 이슈 지시 → 웹 세션에서 구현 확인 같은 흐름도 가능합니다.

## 5. 다음 단계로 확장할 것들

- 테스트/린트 도구가 정해지면 `.claude/settings.json`의 allow 목록과 워크플로우에 반영
- 정기 작업(매일 아침 리포트 등)은 GitHub Actions `schedule` 트리거 + Claude 프롬프트로 자동화 가능
- Slack·Gmail 등 외부 연동은 MCP 서버로 추가 (`claude mcp add`)
