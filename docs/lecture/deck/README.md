# 세미나 덱 (60장)

`pai-deck.pptx` — 「Physical AI: 챗봇을 넘어 격전지로」 교안 전체.
실습(Chapter 5)은 **30분**이다. 개념을 한 번 만져 보는 것이 목적이고, 안전 설계와
골든셋 양식은 실습 시간에 쓰지 않고 "가져가는 양식" 으로 넘긴다.
포맷은 `docs/31.AX컨설팅방법론_통합교재(실습포함)-최종본.pdf` 의 마스터를 따른다.
구성 계획은 `docs/lecture/ppt-outline.md`.

## 구성

| 범위 | 장수 | 내용 |
|---|---|---|
| 표지 | 1 | |
| Chapter 1 | 10 | 패러다임 시프트 — 챗봇을 넘어 격전지로 |
| Chapter 2 | 14 | P-AI 아키텍처 해부 — 핵심 뼈대 셋 |
| Chapter 3 | 15 | 실습 — 로컬 VLM 으로 LED 색상 조절 |
| Chapter 4 | 11 | 실전 적용 — 5 Phase 로드맵, 무엇부터 |
| Chapter 5 | 8 | 30분 실습 — 관측·과제 선택, 규칙/AI 판정, 한 줄 발표 |
| 부록 | 2 | 실측 데이터 색인 · 시연 대본과 축약판 |

## 빌드

생성기는 `pptxgenjs` 스크립트다. 장을 고칠 때는 `.pptx` 를 직접 열어 고치지 말고
해당 `ch*.js` 를 고친 뒤 다시 생성한다 — 그래야 다음 수정이 덮어쓰이지 않는다.

```bash
cd docs/lecture/deck
npm install pptxgenjs                    # 최초 1회
NODE_PATH=$PWD/node_modules node main.js # pai-deck.pptx 생성
```

`full.js` 상단의 `applyTheme` 경로는 pptx 스킬의 `scripts/apply_theme.js` 를 가리킨다.
이것이 없으면 테마 색이 Office 기본 팔레트로 떨어지므로, 환경이 바뀌면 경로를 고친다.

| 파일 | 역할 |
|---|---|
| `full.js` | 테마·색상 상수와 마스터 헬퍼 (`m2` 간지, `m3` 개념, `m4` 산출물, `m5` 워크시트) |
| `deck.js` | 표지 + Chapter 1 |
| `ch2.js` `ch3.js` `ch45.js` | Chapter 2 / 3 / 4·5·부록 |
| `main.js` | 전부 묶어 `pai-deck.pptx` 를 쓰고 테마를 입힌다 |

## 검수

슬라이드가 넘치거나 겹치는 것은 생성 시점에 드러나지 않는다. 표의 행 수를 늘리면
아래 박스를 조용히 덮는다 — 실제로 Chapter 4·5 초안에서 표 6개가 마지막 행을
가렸고, 이미지로 렌더해 보기 전까지 아무 오류도 나지 않았다. 반드시 렌더해서 본다.

```bash
python <pptx-skill>/scripts/office/validate.py pai-deck.pptx
python <pptx-skill>/scripts/office/soffice.py --headless --convert-to pdf pai-deck.pptx
pdftoppm -r 110 -jpeg pai-deck.pdf s      # s-01.jpg … 눈으로 확인
```

이모지(💡 등)는 LibreOffice 렌더에서 사라진다. 기호는 `◆` `⚠` `○ △ ×` 처럼
글꼴에 있는 것만 쓴다.

## 수치의 출처

덱에 실린 숫자는 모두 이 저장소의 측정 기록에서 왔다. 부록 A 가 색인이다.
숫자를 고칠 일이 생기면 `docs/tech/notes/` 의 원본을 먼저 고치고 덱을 맞춘다.
