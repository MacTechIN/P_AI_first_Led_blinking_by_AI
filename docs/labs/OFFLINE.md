# 강사용 — 네트워크 없는 교실에 시뮬레이터 배포하기

각자의 PC에는 인터넷이 없다. 그러므로 **USB 하나로 끝나야 한다.**

## 꾸러미 만들기 (네트워크 있는 곳에서 미리)

```bash
# 1. numpy 휠을 모은다 — 학생들의 파이썬 버전·운영체제에 맞춰
mkdir -p /tmp/wheels
for plat in win_amd64 macosx_11_0_arm64 macosx_10_9_x86_64 manylinux2014_x86_64; do
  for pv in 311 312 313; do
    pip download numpy --no-deps --only-binary=:all: \
        --platform $plat --python-version $pv -d /tmp/wheels
  done
done

# 2. 꾸러미를 만든다
./tools/make_bundle.py --wheels /tmp/wheels --out dist
```

→ `dist/pai-sim.zip` (약 162MB, 휠 11개 포함). USB 에 넣어 돌린다.

**OpenCV 는 넣지 않는다.** 플랫폼마다 50MB 가 넘는데, 우리가 쓰는 것은 색 공간
변환뿐이라 `control/colour.py` 가 numpy 로 대신한다. 두 구현이 같은 답을 내는지
`tests/test_colour.py` 가 고정한다 — 학생과 강사가 다른 점수를 보면 실습이
성립하지 않는다.

## 학생이 하는 일

폴더를 복사하고 그 안에서 한 줄:

```
python3 START.py
```

처음 한 번 numpy 를 USB 안의 휠로 설치하고(인터넷 쓰지 않음), 시뮬레이터가
실제로 도는지 확인한 뒤 다음 안내를 띄운다.

```
python3 START.py 1          루프가 닫혀 있다          (5분)
python3 START.py 2          환경이 변하면 무너진다     (5분)
python3 START.py 3          대본이 곧 골든셋          (5분)
python3 START.py 4 <팀번호>  결함 진단                (10분)
```

**팀마다 다른 번호를 준다.** 같은 번호면 같은 결함이 나와 답이 새어 나간다.

## 미리 확인할 것

| | 확인 방법 |
|---|---|
| 파이썬이 깔려 있나 | `python3 --version` — 3.10 이상 |
| 휠이 맞나 | 학생 PC 중 한 대에서 `START.py` 를 먼저 돌려 본다 |
| 터미널 색이 되나 | 안 되면 글자만 나온다. 실습에는 지장 없다 |

휠이 맞지 않으면 `START.py` 가 **그 PC의 파이썬 버전과 운영체제를 화면에
찍어 준다.** 그 조합의 휠을 미리 받아 두면 된다.

## 무엇이 꾸러미에 들어가나

| 들어감 | 빠짐 |
|---|---|
| `sim/` `control/` `perception/` | `arduino/` (펌웨어) |
| `scenarios/` `tapes/` `teams/` | `host/rig_worker.py` `host/submit.py` (실물 장비용) |
| `host/sim_demo.py` 등 4개 | `docs/lecture/` (강의 덱) |
| `wheels/` `START.py` `README.md` | `golden/scene/` (실측 사진) |

## 왜 이렇게까지 하나

이 교재는 "되는 것을 보여주는" 교재가 아니다. **학생이 직접 재 보는** 교재이고,
재려면 각자의 기계에서 돌아야 한다. 강사 화면만 보는 실습은 4-2 에서 말한
PoC 와 같다 — 잘 되는 조건에서 본 것이다.
