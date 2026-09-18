# 모듈 2 — 인지 계층과 테스트 가능성

**소요** 약 90분   **선행** 모듈 0   **슬라이스** VS-1   **ADR** 0004, 0005, 0006

## 목표

하드웨어 없이 상위 계층을 개발할 수 있는 구조를 만들 수 있다.
그리고 왜 그 구조가 **일정 관리 도구**이기도 한지 이해한다.

## 1. 문제 상황 재현

모듈 0 에서 카메라가 미지원 센서였다고 하자. 새 부품을 주문했고 배송에 일주일이
걸린다. **그동안 아무것도 못 하는가?**

이것이 이 모듈의 동기다. 추상화는 미학이 아니라 **임계 경로를 끊는 도구**다.

## 2. 인지 인터페이스

```python
from perception import open_source

with open_source("synthetic") as src:    # 카메라 없이
    obs = src.read()
    print(obs.describe())
```

**예상:** `{'source': 'synthetic', 'seq': 0, 'size': '640x480', ...}`

```python
with open_source("argus:0", width=1280, height=720) as src:   # 실물 CSI
    obs = src.read()
```

**상위 코드는 두 경우를 구별하지 못한다.** 소스 지정 문자열만 다르다.

## 3. 합성 소스로 상위 계층 개발하기

```python
from perception import SyntheticSource, patch, moving_patch

# 가운데 빨간 사각형 — 색 판별 개발용
with SyntheticSource(patch(fg=(230, 20, 20))) as src:
    img = src.read().image

# 좌우로 움직이는 사각형 — 방향 판단 개발용
with SyntheticSource(moving_patch(fg=(20, 220, 20))) as src:
    frames = [o.image for o in src.stream(limit=10)]
```

```bash
make test
```

**예상:** `103 passed` — **카메라와 아두이노를 모두 뽑고도** 통과해야 한다.

이것이 합격 조건이다. 통과하지 않으면 추상화가 새는 것이다.

## 4. 핵심 실습 — 건전성 검사

모듈 0 에서 본 "픽셀이 전부 같은" 프레임을 **자동으로 잡는다.**

```python
import numpy as np
from perception import assert_frame_sane, FrameHealthError

# IMX708 사례 재현
flat = np.full((480, 640, 3), 16, dtype=np.uint8)
try:
    assert_frame_sane(flat)
except FrameHealthError as e:
    print("잡았다:", e)
```

**예상:** `잡았다: constant frame: 모든 픽셀이 16 — 센서가 설정되지 않았을 가능성`

### 임계값을 왜 std 로 잡는가

정상 장면은 **렌즈 캡을 씌워도** 센서 노이즈로 표준편차가 1을 넘는다.
설정되지 않은 센서는 정확히 0 에 가깝다. 이 차이가 판별의 근거다.

```python
rng = np.random.default_rng(1)
dark = np.clip(rng.normal(8, 3, (240, 320, 3)), 0, 255).astype(np.uint8)
assert_frame_sane(dark)      # 통과해야 한다 — 어두운 것과 평탄한 것은 다르다
```

**어두운 정상 장면이 막히면 임계값이 너무 높은 것이다.** 두 방향 모두 시험해야 한다.

## 5. CSI 는 왜 cv2 로 못 읽는가

```python
from perception import open_source
with open_source("v4l2:0") as src:   # CSI 에 시도하면
    src.read()                       # 멈추거나 실패한다
```

두 가지가 겹친다.

1. **`/dev/video0` 은 RG10(10비트 Bayer) 원시 데이터다.** 디베이어·자동노출·
   화이트밸런스는 Tegra ISP 의 몫이고, 그 경로가 `nvarguscamerasrc`(Argus)다.
2. 이 시스템의 cv2 는 **GStreamer 없이 빌드**되어 있다.
   ```bash
   python3 -c "import cv2; print([l for l in cv2.getBuildInformation().splitlines() if 'GStreamer' in l])"
   ```
   → `GStreamer: NO`

그래서 `ArgusSource` 가 python-gi 의 Gst appsink 로 직접 읽는다.
**USB 웹캠은 `v4l2:0` 으로 그대로 읽힌다** — 인터페이스가 같으므로 상위는 모른다.

## 6. 자동노출 워밍업

```python
with open_source("argus:0", warmup=0) as src:    # 워밍업 끄기
    print(frame_stats(src.read().image))
```

**예상:** `mean` 이 20 대 — 거의 검은 화면.

```python
with open_source("argus:0") as src:              # 기본 warmup=30
    print(frame_stats(src.read().image))
```

**예상:** `mean` 이 80~120 — 정상 노출.

> **워밍업은 건전성 검사를 대신하지 않는다.** 첫 프레임도 **어두울 뿐 평탄하지는
> 않아** 검사를 통과한다. 두 장치는 서로 다른 실패를 막는다 — 검사는 "센서 미설정",
> 워밍업은 "노출 미수렴".

## 의도된 실패 실습

1. **검사 끄기**: `open_source("synthetic", check_health=False)` 에 `flat()` 페인터를
   넣고 평탄 프레임이 그대로 통과하는 것을 확인한다.
2. **임계값 올리기**: `assert_frame_sane(dark, min_std=50)` — 정상 장면이 막힌다.
   오탐이 어떤 모습인지 본다.
3. **추상화 깨기**: 상위 코드에서 `ArgusSource` 를 직접 import 해 쓴다.
   그 뒤 `make test` 를 카메라 없이 돌려 **테스트가 깨지는 것**을 확인한다.

## 연습 문제

1. 합성 소스가 "임계 경로를 끊는다" 는 말을 일정 관점에서 설명하시오.
2. `Observation` 에 `sensors` 슬롯을 처음부터 넣은 이유는? (힌트: 모듈 6)
3. 색 공간을 RGB 로 통일하고 변환을 `V4L2Source`/`ArgusSource` 경계에서만
   하는 이유는? 안 그러면 어떤 버그가 생기는가?

## 교훈

> **픽셀로 검증한다.** 그리고 **추상화는 부품이 없어도 일할 수 있게 해준다.**
> 이 두 가지는 별개가 아니다 — 검증 가능한 인터페이스가 곧 대체 가능한 인터페이스다.
