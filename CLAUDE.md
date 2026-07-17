# morning-ops-ai

아침 운영(모닝 옵스) 업무를 자동화하는 AI 프로젝트.

## 프로젝트 개요

- 목적: 반복되는 아침 운영 업무(리포트 확인, 일정 정리, 알림 발송 등)를 AI로 자동화
- 상태: 초기 세팅 단계 — 기술 스택은 첫 기능 구현 시 확정

## 개발 워크플로우

프로덕트 개발은 아래 사이클로 진행한다:

1. **기획** — GitHub 이슈에 요구사항 작성 (또는 `/plan-feature` 커맨드 사용)
2. **구현** — `claude/` 접두사 브랜치에서 개발
3. **검증** — 테스트 작성·실행 후 커밋
4. **리뷰** — PR 생성 시 Claude 자동 코드 리뷰 실행 (`.github/workflows/claude-code-review.yml`)
5. **머지** — 리뷰 반영 후 main에 머지

## 규칙

- 커밋 메시지는 한 줄 요약 + 필요 시 본문. 한국어/영어 모두 허용
- main 브랜치에 직접 푸시하지 않는다 — 항상 브랜치 + PR
- 새 기능에는 테스트를 함께 추가한다
- 비밀키/토큰은 절대 커밋하지 않는다 (GitHub Secrets 사용)

## 자동화 안내

- 이슈나 PR에서 `@claude`를 멘션하면 Claude가 응답·구현한다 (`.github/workflows/claude.yml`)
- 커스텀 슬래시 커맨드는 `.claude/commands/`에 있다
- 상세 가이드: `docs/claude-automation-guide.md`
