---
name: ega-campaign
description: |
  EGA 에이징 스피드 체크 캠페인 랜딩 페이지 업데이트 전용 스킬.
  개발 업무(질문/선택지 수정, 카피 변경, UI/결과 화면 수정, Netlify 배포)와
  마케팅 업무(Supabase 리드 성과 조회, 마케팅 플레이북 업데이트, 채널별 콘텐츠 생성)를 모두 커버한다.

  다음 상황에서 반드시 이 스킬을 사용하라:
  - "에이징 체크 질문 바꿔줘", "선택지 수정", "결과 화면 바꾸고 싶어" 같은 퀴즈/UI 변경 요청
  - "배포해줘", "deploy", "사이트 업데이트" 등 캠페인 페이지 배포 요청
  - "리드 몇 명이야?", "성과 리포트", "어제 신청자 수" 같은 캠페인 데이터 조회 요청
  - "플레이북 업데이트", "마케팅 자료 수정", "카카오 채널 콘텐츠 써줘" 등 마케팅 팀 산출물 요청
  - "카피 바꿔줘", "문구 수정", "에이징 캠페인" 언급이 있는 모든 요청
---

# EGA 에이징 스피드 체크 캠페인 스킬

## 프로젝트 전체 컨텍스트

작업 전에 항상 아래 파일을 읽어라:
```
/Users/bahn/Desktop/Ega/ega-aging-check/CLAUDE.md
```
이 파일에 인프라 설정값(Supabase URL/Key, Netlify Site ID/Token, 카카오 JS Key), 파일 구조, 주요 함수 가이드, 배포 방법이 모두 담겨 있다.

---

## 모드 판별

요청을 받으면 먼저 어떤 모드에 해당하는지 파악하라. 두 모드가 동시에 요청될 수 있으니 함께 처리해도 된다.

| 요청 유형 | 모드 |
|-----------|------|
| 질문/선택지/점수 수정 | 개발 |
| 결과 화면 카피, 공유 문구 변경 | 개발 |
| UI 스타일, 버튼, 레이아웃 변경 | 개발 |
| Netlify 배포 | 개발 |
| 리드 수/신청자 데이터 조회 | 마케팅 |
| 마케팅 플레이북 업데이트 | 마케팅 |
| SNS·카카오·블로그 콘텐츠 생성 | 마케팅 |
| 성과 리포트 작성 | 마케팅 |

---

## 개발 모드

### 핵심 파일 위치

```
/Users/bahn/Desktop/Ega/ega-aging-check/
├── js/questions.js   ← 질문·선택지·점수·결과타입 카피
├── js/app.js         ← 퀴즈 로직·결과·공유·리드 수집 전체
├── index.html        ← 화면 구조 (버튼, 텍스트, 레이아웃)
├── css/styles.css    ← 스타일 (색상, 폰트, 애니메이션)
└── deploy-site.sh    ← Netlify 배포 스크립트
```

### 질문/선택지 수정 (`questions.js`)

`QUESTIONS` 배열에서 수정한다. 각 항목 구조:
```javascript
{
  id: "q1",
  text: "질문 내용",
  options: [
    { key: "a", label: "선택지 텍스트", score: 4 },
    // score: 4=매우 좋음, 3=좋음, 2=보통, 1=나쁨
  ],
  strength: "간략 결과 - 좋은 신호 텍스트",
  weakness: "간략 결과 - 개선 필요 신호 텍스트",
  tip: "상세 결과에 표시되는 개선 팁"
}
```

### 결과 카피 수정 (`questions.js`)

`RESULT_TYPES` 객체에서 수정한다. 키: `"slow"`, `"normal"`, `"fast"`.
각 타입별 `label`, `title`, `subtitle`, `color`, `shareText` 등.

### 공유 문구·기타 카피 수정 (`app.js`)

- 카카오 공유 문구: `shareKakao()` 함수 내 `kakaoTitle`, `kakaoDesc`
- 랜딩 훅 카피: `index.html` 내 S1 섹션
- 리드 폼 카피: `index.html` 내 S4(리드 수집) 섹션

### 배포

파일 수정 후 반드시 배포까지 완료하라:
```bash
cd /Users/bahn/Desktop/Ega/ega-aging-check
bash deploy-site.sh
```
배포 완료 후 라이브 URL `https://ega-aging-check.netlify.app` 을 알려줘라.

---

## 마케팅 모드

### 리드 데이터 조회

현재 리드(신청자) 수 확인:
```bash
curl -s -X POST "https://idluqbwpoyinxbshqsky.supabase.co/rest/v1/rpc/get_lead_count" \
  -H "apikey: sb_publishable_LrOX3nb_MQ1KHsP00Vepbw_I1_coGZw" \
  -H "Content-Type: application/json" -d "{}"
```

최근 리드 목록(최신 20건):
```bash
curl -s "https://idluqbwpoyinxbshqsky.supabase.co/rest/v1/leads?select=name,contact_type,score,result_type,created_at&order=created_at.desc&limit=20" \
  -H "apikey: sb_publishable_LrOX3nb_MQ1KHsP00Vepbw_I1_coGZw" \
  -H "Authorization: Bearer sb_publishable_LrOX3nb_MQ1KHsP00Vepbw_I1_coGZw"
```

결과타입별 분포:
```bash
curl -s "https://idluqbwpoyinxbshqsky.supabase.co/rest/v1/leads?select=result_type" \
  -H "apikey: sb_publishable_LrOX3nb_MQ1KHsP00Vepbw_I1_coGZw" \
  -H "Authorization: Bearer sb_publishable_LrOX3nb_MQ1KHsP00Vepbw_I1_coGZw"
```

### 마케팅 플레이북 업데이트

플레이북 파일: `/Users/bahn/Desktop/Ega/docs/marketing-playbook.html`
라이브 URL: `https://comforting-puppy-543a50.netlify.app`

수정 후 Netlify에 배포해야 한다. 플레이북 사이트 배포 스크립트가 없으면 Netlify CLI 또는 API로 배포할 것.

플레이북에는 다음 항목이 포함되어야 한다:
- 캠페인 현황 지표 (리드 수, 전환율 등)
- 채널별 배포 상태
- 운영 체크리스트
- A/B 테스트 결과 (있을 경우)

### 채널별 콘텐츠 생성

콘텐츠 생성 시 EGA 브랜드 톤을 유지하라: 전문적이되 친근함, 과학적 근거, 50+ 타겟.

**카카오 채널 포스트**: 300자 내외, 이모지 절제, CTA 포함
**인스타그램 피드**: 훅 문장 + 본문 3-5줄 + 해시태그 10-15개
**인스타그램 스토리**: 3-5장 스와이프 구성, 각 장 1문장
**블로그/뉴스레터**: 800-1500자, 정보성 + 캠페인 연계

### 성과 리포트 구조

마케팅팀에 전달할 리포트를 작성할 때는 이 구조를 따르라:

```
# EGA 에이징 스피드 체크 성과 리포트
## 기간: [기간]

### 핵심 지표
- 총 참여자 수:
- 리드 전환율 (참여 → 정보 입력):
- 카카오 공유 추정 수:

### 결과 타입 분포
- 느린 노화 (slow):
- 보통 (normal):
- 빠른 노화 (fast):

### 채널별 유입 (UTM 데이터)
(GA4 연동 전이면 '미집계'로 표기)

### 주요 인사이트
- 
### 다음 액션
- 
```

---

## 작업 완료 체크리스트

개발 작업 후:
- [ ] 수정 내용 요약 (어느 파일, 어느 항목)
- [ ] `bash deploy-site.sh` 실행 완료
- [ ] 라이브 URL 확인 `https://ega-aging-check.netlify.app`

마케팅 작업 후:
- [ ] 데이터 출처 명시 (Supabase 조회 시각)
- [ ] 콘텐츠는 마케팅팀이 바로 사용할 수 있는 형태로 제공
- [ ] 플레이북 수정 시 배포 완료 여부 확인
