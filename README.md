# Physical AI — 카메라로 보고, 로컬 LLM이 판단하고, LED를 켠다

화면 밖에서 동작하는 AI의 기초를 **한 대의 보드에서 직접 측정하며** 구현하고,
그 과정을 그대로 **교육 커리큘럼**으로 만든 저장소다.

```
카메라 → 특징 추출 → 판단(규칙 또는 로컬 VLM) → 직렬 → 아두이노 → RGB LED
                                                              └→ 다시 카메라로 검증
```

## 이 저장소의 성격

**최종 산출물은 동작하는 코드가 아니라 가르칠 수 있는 자료다.** 그래서 여기서는
**기록된 실패가 핵심 자산**이다. 잘 되는 경우만 보여주는 교재는 학습자가 막히는
순간 쓸모가 없다. `docs/tech/`의 막다른 길과 ADR의 기각 사유가 전부 강의 재료다.

인용된 수치는 **모두 이 보드에서 직접 측정한 값**이다. 출처는 각 문서에 있다.

| 측정 | 값 |
|---|---|
| 제어 루프 한 바퀴 | **34.6 ms** (촬영이 88%) |
| 로컬 VLM 추론 | **~2.9 초** → 그래서 별도 스레드 (ADR-0008) |
| 위치 판단 | 규칙 **9/9 · 7.4ms** vs VLM **3/9 · 2,472ms** |
| 색 판단 (12색) | 규칙 9/12 vs VLM 7/12, 틀린 것도 색상환 한 칸 이내 |
| 움직임 노이즈 바닥 | **0.300** → 임계 0.601, 오경보 0% |
| 정지 화면 20장 전송 | 18회 → 이력 적용 후 **2회** (ADR-0007) |
| LED 색 정확도 | **6/6**, 평균 색조 오차 7.0 |

## 빠르게 돌려보기

### 장비가 없을 때 (학생용 — 이쪽이 기본)

```bash
./host/sim_demo.py                      # 닫힌 제어 루프, 장비 0개
./host/sim_demo.py --scenario dusk      # 조명이 꺼지면 판단이 무너진다
./host/scenario_check.py                # 장면이 곧 골든셋
./host/sim_demo.py --fault random --seed 17   # 고장 진단 실습
```

### 실물 장비가 있을 때

```bash
make flash                              # 펌웨어 업로드
./host/blink.py --on                    # LED 점등
./host/verify_rgb.py --level 60 --lock  # 명령한 색 vs 촬영한 색
./host/vs2_demo.py --policy vlm --lock  # 카메라 → 로컬 VLM → LED
make test                               # 296개 시험
```

## 매뉴얼은 어디 있나

| 읽는 사람 | 문서 |
|---|---|
| **학생** | [`docs/labs/STUDENT.md`](docs/labs/STUDENT.md) — 각자의 PC에서 30분, 화면 출력까지 그대로 |
| **강사 (실습)** | [`docs/labs/INSTRUCTOR.md`](docs/labs/INSTRUCTOR.md) — 해답·막힐 지점·채점 |
| **강사 (발표)** | [`docs/lecture/presenter-script.md`](docs/lecture/presenter-script.md) — 60장 전부, 장별 할 말과 수치 |
| **강사 (배포)** | [`docs/labs/OFFLINE.md`](docs/labs/OFFLINE.md) — 네트워크 없는 교실에 USB로 배포 |
| 처음 만드는 사람 | [`docs/labs/00-setup.md`](docs/labs/00-setup.md) — 부품·배선·함정 |
| 전체 지도 | [`docs/curriculum.md`](docs/curriculum.md) — 모듈 0~7 |

**발표 자료**: [`docs/lecture/deck/pai-deck.pptx`](docs/lecture/deck/) (60장 · 105분, PDF 동봉)

## 교육 과정

| 모듈 | 주제 | 실습서 |
|---|---|---|
| 0 | 환경과 부품의 함정 | `labs/00-setup.md` |
| 1 | 하드웨어의 진실 — 장치가 보여도 동작이 아니다 | `labs/01-hardware-truth.md` |
| 2 | 액추에이터와 타이밍 | `labs/02-actuator-timing.md` |
| 3 | 인지 — 카메라를 믿지 않는 법 | `labs/03-perception.md` |
| 4 | 규칙 기반 제어 루프 | `labs/04-rule-loop.md` |
| 5 | 온디바이스 AI | `labs/05-ondevice-ai.md` |
| 6 | 역량 계약 — 선언으로 장치 추가 | `labs/06-capability-contract.md` |
| 7 | 안전과 평가 | `labs/07-safety-evaluation.md` |
| **7+** | **진단 클리닉 — 장비 0원, 30분** | `labs/08-fault-clinic.md` |

## 저장소 구조

```
├── README.md                  이 문서
├── CLAUDE.md                  작업 지침 · 하드웨어 사실관계 · 함정 모음
│
├── arduino/rgb_led/           펌웨어 (RGB 드라이버 + 직렬 명령 파서)
├── perception/                L2 인지 — 프레임 소스, 건전성 검사
│   ├── sources.py             카메라를 갈아끼우는 추상화 (ADR-0004)
│   └── argus.py               Jetson CSI (ADR-0006)
├── control/                   L1/L3 — 특징·정책·액추에이터·제어 루프
│   ├── features.py            ROI 색상 추출 (전역 밝기를 쓰지 않는 이유 포함)
│   ├── policy.py              규칙 정책 + 이력(hysteresis)
│   ├── vlm.py                 비동기 VLM 정책, 스키마, 검증기 (ADR-0008·0009)
│   ├── capability.py          역량 계약 — 선언 하나가 스키마·검증기·전송을 만든다
│   ├── evaluate.py            골든셋 평가 (회귀 탐지)
│   ├── colour.py              OpenCV 없이도 도는 색 변환
│   ├── direction.py           예제 1 — 위치는 산술, 규칙이 이긴다
│   ├── motion.py              예제 2 — 임계값은 재서 정한다
│   └── scene.py               예제 3 — 규칙으로 쓸 수 없는 질문
│
├── sim/                       시뮬레이션 계층 (S-1~S-6) — 장비 없이 전부
│   ├── world.py  panel.py     가상 현장과 가상 LED (실물의 결함을 재현한다)
│   ├── faults.py              결함 주입 8종 — 실제로 겪은 고장들
│   ├── scenario.py            장면 대본 + 기대 출력
│   ├── replay.py              실제 VLM 응답 기록·재생 (서버 불필요)
│   └── queue.py               제출 큐 — 장비가 하나라 직렬이다
│
├── host/                      실행기 (전부 CLI)
│   ├── blink.py               기본 LED 제어
│   ├── sim_demo.py            시뮬레이터 데모 + 결함 주입
│   ├── scenario_check.py      대본 채점 (종료코드로 CI 연결 가능)
│   ├── leaderboard.py         공개·숨은 세트 채점, 네 칸
│   ├── verify_rgb.py          명령한 색 vs 촬영한 색
│   ├── measure_*.py           실측 도구 (방향·움직임·장면)
│   └── rig_worker.py          실물 장비 작업자
│
├── scenarios/                 장면 대본 (*.json) + hidden/ 숨은 세트
├── tapes/                     기록된 실제 VLM 응답 51건
├── teams/                     제출 정책 본보기 (일부러 잘못 만든 것 포함)
├── capabilities/              장치 선언 (*.json) — 추가에 코드가 필요 없다
├── golden/                    골든셋 이미지 + 기대 출력
├── tools/                     학생용 USB 꾸러미 생성기 · START.py
├── tests/                     296개 — 카메라 없이 전부 돈다
│
└── docs/
    ├── curriculum.md          교육 커리큘럼 전체 지도
    ├── development_plan.md    수직 슬라이스 계획
    ├── simulation_plan.md     한 벌의 장비로 여럿이 실습하는 법
    ├── labs/                  모듈별 실습서 + STUDENT/INSTRUCTOR/OFFLINE
    ├── lecture/               발표 덱(60장) + 강사용 스크립트
    └── tech/
        ├── adr/               아키텍처 결정 기록 (기각된 대안 포함)
        └── notes/             실측 기록 — 이 저장소의 근거
```

## 하드웨어

| | |
|---|---|
| 호스트 | NVIDIA Jetson Orin Nano Super (JetPack 6, CUDA 12.6) |
| 카메라 | IMX219 CSI — `argus:0` 로 읽는다, cv2/V4L2 아님 (ADR-0006) |
| MCU | Arduino Uno R3 — USB 직렬 `/dev/ttyACM0`, 115200 |
| LED | 5mm RGB 공통 애노드 · **R=9, G=11, B=10** · **5V** · **220Ω × 3** |
| 로컬 VLM | Qwen2.5-VL-3B (llama.cpp CUDA). **7B는 적재되고 첫 요청에서 죽는다** |

배선 주의사항과 실측 근거는 [`docs/labs/00-setup.md`](docs/labs/00-setup.md) 와
[`docs/tech/notes/rgb-rewire-2026-10-28.md`](docs/tech/notes/rgb-rewire-2026-10-28.md).

## 반복되는 세 가지 교훈

> **① 성공 신호는 작동의 증거가 아니다.**
> `/dev/video0` 가 있는데 모든 픽셀이 같은 값이었고, `/health` 가 ok 인데 요청이
> 전부 죽었고, 스키마를 통과한 응답을 검증기가 거부했다. 셋 다 "성공" 이라고
> 말하고 있었다.
>
> **② 측정 조건이 결론을 만든다.**
> 7B는 단독으로는 올라간다. 카메라와 제어 루프를 함께 돌리면 죽는다.
> 적재 성공은 서비스 가능의 증거가 아니다.
>
> **③ 적어두지 않은 것은 지켜지지 않는다.**
> 골든셋에서 colour만 고정했을 때 5/5였고, action을 함께 고정하자 2/5가 됐다.
> 아무것도 바뀌지 않았는데.

## 기여

이 저장소에 손댈 때는 [`CLAUDE.md`](CLAUDE.md) 를 먼저 읽는다 — 하드웨어 사실관계,
이미 밟은 함정, 바꾸면 안 되는 것들이 거기 있다. **실패를 지우지 않는 것**이
이 저장소의 규칙이다.

```bash
make test        # 296개. 카메라·아두이노 없이 전부 돈다
```
