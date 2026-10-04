# 매일 아침 브리핑 v02

- 스케줄: `10 0 * * *` (UTC) = 매일 09:10 KST
- 실행 방식: 매 실행마다 새 세션 생성
- 커넥터: Gmail, Google Calendar, Google Drive, Slack (ADRO 워크스페이스, bahn@adro.com)
- 적용 방법(대표님 직접): 루틴은 claude.ai UI에서 만들어져 에이전트가 수정할 수 없습니다.
  1. https://claude.ai/code/routines/trig_015onCnawAvaUvebTdj2WHME 열기
  2. 커넥터: **Slack 추가**, Hugging Face 2개(허깅페이스 / Hugging-Face) 제거
  3. 프롬프트를 아래 블록으로 교체, 이름을 `매일 아침 브리핑 ver02`로 변경
  4. 다음 날 09:10 Slack DM 수신 확인
- 주의: claude.ai에 연결된 Slack은 **ADRO 워크스페이스(bahn@adro.com)** 입니다. v01 프롬프트가 가정한 EGA 워크스페이스(bahn@ega.co.kr)는 연결돼 있지 않습니다. EGA Slack까지 보려면 https://claude.ai/customize/connectors 에서 EGA 워크스페이스로 Slack을 추가 연결해야 합니다.
- v01 대비 변경: Slack 커넥터 추가(v01은 Slack 미연결로 6번 섹션·Slack 발송 불가), Hugging Face 2개 제거, 수집 실패를 숨기지 않고 표기, 한국어 출력 고정, 발송 대상 명시

## Prompt

```
Generate a concise, scannable morning briefing in Korean to help me catch up.

Sources:
- Gmail connector (drbahn@gmail.com, which also receives mail for bahn@adro.com, bahn@darez.kr, bahn@ega.co.kr when forwarded)
- Google Calendar connector
- Google Drive connector (only to open docs linked from meetings or emails)
- Slack connector (ADRO workspace, my user ID U05AU0BMGGM)

Include:
1. 일정 — Today's and tomorrow-morning meetings with times (KST), attendees, and any preparation needed.
2. 중요 메일 — Unread emails from the last 48h that need my attention, grouped by urgency (오늘 처리 / 이번 주 / 참고). Ignore newsletters, notifications and promotions.
3. 회신 필요 — Emails or Slack DMs/mentions where someone asked me something and I haven't replied. Open the thread before listing it; drop it if I already replied.
4. 액션 아이템 — Pending tasks or follow-ups from recent activity (weekly reports from my team, threads I'm cc'd on with deadlines).
5. 모닝 마켓 — Korean and U.S. stock market summary with emphasis on beauty/consumer goods, wellness, startups and private equity: major index moves, key news, sector trends, and anything relevant to my business or investment decisions.
6. Slack — Important Slack messages from the last 24h (ADRO workspace): items needing attention, reply, or follow-up.

Rules:
- Keep it concise and easy to scan. If a section has nothing notable, skip it.
- If a source fails or is not connected (connector error, auth expired, tool missing), do NOT silently skip it: add one last line "수집 실패: <source> — <reason>".
- Never invent data; every item must come from a tool result.

After generating the briefing, send the final summary as a Slack direct message to myself (user ID U05AU0BMGGM) in the ADRO workspace. If the Slack tool is unavailable or sending fails, say so explicitly in the session output.
```
