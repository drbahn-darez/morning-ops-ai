# morning-ops-ai

아침 운영 업무를 자동화하는 AI 프로젝트.

## Claude 프로덕트 개발 자동화

이 리포지토리는 Claude Code 기반 개발 자동화가 세팅되어 있습니다.

| 구성 요소 | 위치 | 역할 |
|---|---|---|
| 프로젝트 메모리 | `CLAUDE.md` | Claude가 매 세션 자동으로 읽는 프로젝트 규칙·컨벤션 |
| 권한 설정 | `.claude/settings.json` | 자주 쓰는 명령 자동 허용, 비밀 파일 접근 차단 |
| 커스텀 커맨드 | `.claude/commands/` | `/plan-feature`, `/fix-issue`, `/ship` 워크플로우 커맨드 |
| @claude 멘션 봇 | `.github/workflows/claude.yml` | 이슈·PR에서 `@claude` 멘션 시 분석·구현·답변 |
| PR 자동 리뷰 | `.github/workflows/claude-code-review.yml` | PR 생성/업데이트 시 자동 코드 리뷰 |

### 시작하기

1. GitHub 리포 설정에서 `ANTHROPIC_API_KEY` 시크릿을 등록합니다 (또는 로컬 Claude Code에서 `/install-github-app` 실행)
2. 이슈를 만들고 본문에 `@claude 이 기능 구현해줘` 라고 멘션해 보세요
3. 로컬에서는 `claude` 실행 후 `/plan-feature 기능설명` → 승인 → 구현 → `/ship` 순서로 개발합니다

상세 가이드: [docs/claude-automation-guide.md](docs/claude-automation-guide.md)
