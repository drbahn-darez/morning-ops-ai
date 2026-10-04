---
name: "ega-shorts"
description: "EGA 유튜브 쇼츠 양산 파이프라인 실행 — 쇼츠 만들기, 쇼츠 양산, 스크립트 생성, 이미지 생성, 영상 렌더, 검수, 쇼츠 업로드 요청 시 사용"
---

# EGA 쇼츠 양산 에이전트 v2

정보형 쇼츠(AI 생성 에디토리얼 이미지 배경 + 세리프 타이포 + TTS)을 스크립트 JSON으로 렌더하고 2단계 검수 후 전달하는 파이프라인.
설계서: https://claude.ai/code/artifact/81afc99b-e469-4e1a-844e-051fcac22fb2

## 코드 위치
정본: Bahn 컴퓨터 `/Users/bahn/Documents/Claude/Projects/에가 (Ega) 경영 관리/ega-shorts/`
세션이 컴퓨터에 연결되어 있으면 그 폴더의 파일을 device_stage_files로 작업공간에 가져와 실행하고, 결과물(mp4·새 스크립트·수정 코드·생성 이미지)은 device_commit_files로 같은 폴더에 되써놓는다.

## 실행 순서
1. **환경**: `pip install edge-tts --break-system-packages` 후 클라우드 세션이면 `cat /root/.ccr/ca-bundle.crt >> $(python3 -m certifi)` (프록시 CA 신뢰, 이거 없으면 TTS SSL 오류)
2. **스크립트 생성**: config/brand.json의 insta_style(카드·캐프션 문법: 영문 소제목 + 국문 질문형 헤드라인, 공감 질문→통찰 한 줄→팩트→관점 전환→루틴 CTA)과 hooks.json에서 훅 선택, 보이스 규칙(과장 금지, 저가 포지셔닝 금지, 공포 소구 금지 — empowerment over fear)으로 Claude가 직접 작성. 포맷 5종 로테이션: science / check / routine / review / tip. 훅 씨의 tts는 20자 이내(훅 길이 5.5초 게이트), 총 30~40초 목표
3. **이미지 생성**: Hugging Face 커넥터의 Z-Image Turbo(gr1_z_image_turbo_generate), 해상도 "864x1536 ( 9:16 )". 프롬프트 규칙: editorial/macro photography + premium beauty brand aesthetic + large negative space + no text no watermark, 톤은 코발트 블루 또는 뉴트럴. **훅 이미지는 반드시 딥 코발트 블루 계열**(첫 프레임이 브랜드 팔레트 기준점). 결과는 assets/<id>_<scene>.webp 저장 후 스크립트 씨의 image 필드에 지정. HF 500 에러는 1회 재시도
4. **규제 검사**: `python3 pipeline/compliance.py scripts/<id>.json` — REJECT면 재작성, FLAG면 검수자에게 명시
5. **빌드**: `python3 pipeline/build.py scripts/<id>.json` → out/<id>.mp4 + <id>.meta.json (편당 약 50초)
6. **검수 1단계 — 자동 게이트**: `python3 pipeline/qa.py scripts/<id>.json out/<id>.mp4` — 훅 배치(첫 씨 ≤5.5초)·보이스 톤(평균 음량 -26~-10dB, 클리핑 없음, 발화 속도 2.3~6.0자/초)·이미지 퀄(에지 선명도, 텍스트존 스크림 가독성)·총 길이·금칙어 재검사. FAIL이면 원인 수정 후 재빌드, PASS까지 반복
7. **검수 2단계 — 시각 검수 에이전트**: ffmpeg으로 4프레임 콘택트시트 추출 후 general-purpose 서브에이전트에게 프리미엄 브랜드 크리에이티브 디렉터 역할로 평가를 맡긴다(항목: 훅 스크롤 정지력, 타이포그래피, 이미지 퀄리티, 브랜드 일관성, 전체 완성도 — verdict: APPROVE/APPROVE_WITH_NOTES/REJECT). REJECT면 지적 반영 후 재검수. **두 검수를 모두 통과한 영상만 Bahn에게 SendUserFile로 전달한다**
8. **업로드**: Bahn 승인 후에만 (완전 무인 업로드 금지 원칙). JuzPost 플러그인(juzpost:social-media-scheduler) 또는 Claude in Chrome으로 YouTube Studio 직접 업로드. 제목·설명·태그는 out/<id>.meta.json 사용

## 스크립트 JSON 규칙
- scenes[].type: hook(label/image/title/sub?/tts) | point·check(num/label/image/title/lines[]/tts/disclaimer?) | cta(label/image/title/sub/action/tts)
- label = 상단 영문 소제목(Pill Burden, NMN Science 등 — 인스타 카드 문법), action = CTA 행동 유도 1줄(구독/프로필 링크 안내)
- lines[]는 화면 표시용(짧게), tts는 낭독용(구어체)
- 과학 교육 문장과 제품 효능 문장을 같은 씨에 두지 않는다. 제품은 사용감·루틴 표현만
- 과학 씨엔 disclaimer: true (렌더러가 세이프존 안쪽에 면책 문구 배치)
- 하단 260px은 유튜브 UI 세이프존 — 렌더러가 캐프션·도트·면책을 자동으로 그 위에 배치하므로 임의로 수정하지 말 것
- 동일 템플릿 연속 발행 금지 — 유튜브 비진정성 콘텐츠 정책 대응으로 포맷을 번갈아 쓴다

## TTS
- 기본: edge-tts 무료 (ko-KR-SunHiNeural, rate -4%), brand.json의 tts 섹션
- 업그레이드: ELEVENLABS_API_KEY 받으면 brand.json의 tts.engine을 elevenlabs로

## KPI 기록
발행 후 주간 단위로 Supermetrics(YouTube 소스)에서 조회수·시청지속을 덩어 훅별 성과를 hooks.json 개선에 반영한다. 선행지표는 발행량·검수 승인율·브랜드 검색량이며 조회수는 1차 KPI가 아니다.