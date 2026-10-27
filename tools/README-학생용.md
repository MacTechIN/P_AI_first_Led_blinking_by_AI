# P-AI 시뮬레이터 — 각자의 PC에서 바로 돌립니다

카메라도, 아두이노도, GPU 도, **인터넷도 필요 없습니다.**

## 시작

USB 의 `pai-sim` 폴더를 각자의 PC 아무 데나 복사하고, 그 폴더에서:

```
python3 START.py
```

윈도우에서 `python3` 가 없다고 하면 `python START.py` 로 해 보세요.

처음 한 번은 `numpy` 를 USB 안의 파일로 설치합니다. 인터넷을 쓰지 않습니다.

## 30분 실습

```
python3 START.py 1          루프가 닫혀 있다          (5분)
python3 START.py 2          환경이 변하면 무너진다     (5분)
python3 START.py 3          대본이 곧 골든셋          (5분)
python3 START.py 4 <팀번호>  결함 진단                (10분)
```

실습서는 `docs/08-fault-clinic.md` 에 있습니다.

## 무엇이 들어 있나

| | |
|---|---|
| `sim/` | 가상 LED 와 가상 현장 — 명령한 색이 다음 프레임에 보입니다 |
| `scenarios/` | 장면 대본. 언제 무엇이 일어나고 **그때 무엇이 맞는지** |
| `tapes/` | 실제 모델(Qwen2.5-VL-3B)이 그 장면들에 답한 기록 51건 |
| `teams/` | 제출 정책 본보기. 일부러 잘못 만든 것도 있습니다 |
| `wheels/` | numpy 설치 파일 (오프라인용) |

LED 색이 명령과 달라 보이면 그게 맞습니다. 저항 하나를 세 색이 나눠 쓰는
실물의 성질을 그대로 재현하고 있습니다.

## 잘 안 될 때

**`python3` 를 모른다고 할 때** — 파이썬이 설치되어 있지 않습니다. 강사에게
말씀하세요.

**numpy 설치가 실패할 때** — 화면에 나온 파이썬 버전과 운영체제를 강사에게
보여 주세요. USB 안에 그 조합에 맞는 파일이 없는 경우입니다.

**화면이 알록달록하지 않고 글자만 나올 때** — 터미널이 색을 지원하지 않는
것입니다. 실습에는 지장이 없습니다. `--no-preview` 를 붙인 것과 같습니다.

**그림이 깨져 보일 때** — 창을 넓히거나 글꼴 크기를 줄여 보세요.

## 직접 만져 보기

```
python3 host/sim_demo.py --fault list              어떤 고장이 있는지
python3 host/sim_demo.py --per-channel-resistor    올바른 배선이었다면
python3 host/scenario_check.py --policy tape       실제 모델 응답으로 돌리기
python3 host/leaderboard.py                        공개/숨은 세트 채점
```

`scenarios/` 에 JSON 한 장을 더 넣으면 새 장면이 생깁니다. 코드는 건드리지
않습니다.
