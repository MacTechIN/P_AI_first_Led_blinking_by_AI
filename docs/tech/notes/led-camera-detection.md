# LED 광학 검출 측정 (2026-09-17)

VS-2 폐루프가 물리적으로 성립하는지 확인한 실측.

## 방법
동일 장면에서 LED OFF / ON(level 255) 각각 10프레임을 평균해 차분.
가우시안 블러(21×21)로 노이즈를 억제한 뒤 국소 최대를 찾았다.
카메라 argus:0 @1280×720, LED 는 Arduino pin 9.

## 결과

| 항목 | 값 |
|---|---|
| OFF 평균 밝기 | 125.80 |
| ON 평균 밝기 | 125.81 |
| **전역 차이** | **+0.02** |
| 국소 최대 증가 | **+57.52** @ (497, 393) |
| 노이즈 (diff std) | 10.72 |
| 신호/노이즈 | **5.4×** |

판정: **검출 가능.**

## 가장 중요한 발견 — 전역 밝기로는 검출되지 않는다

전역 평균 차이가 **+0.02** 로 사실상 0 이다. LED 를 최대 밝기로 켰는데도
화면 전체 평균은 변하지 않았다. **Argus 자동노출이 보상하기 때문이다.**

반면 국소적으로는 +57.5 로 뚜렷하다. 차분 맵에서 LED 위치에 명확한 광점이
나타난다.

### VS-2 설계에 미치는 제약

- **전체 프레임 평균 밝기를 LED 피드백에 쓰면 안 된다.** AE 가 상쇄한다.
- 국소 검출(관심영역 또는 차분)을 써야 한다.
- 같은 이유로 "장면이 어두우면 LED 를 밝게" 같은 야간등 규칙은 **발진 위험이
  없다** — LED 를 켜도 AE 때문에 측정 밝기가 거의 변하지 않으므로 양의 되먹임이
  생기지 않는다. 다만 이는 우연한 안전이며 의존해서는 안 된다.
- VS-6 폐루프에서는 AE 를 고정(exposure lock)하는 선택지를 검토할 것.

## 재현

```bash
python3 - <<'PY'
import sys, time; sys.path.insert(0,'host')
import numpy as np, cv2
from blink import Arduino
from perception import open_source
def average(src, n=10):
    return np.mean([src.read().image.astype(np.float32) for _ in range(n)], axis=0)
with Arduino('/dev/ttyACM0', verbose=False) as a, \
     open_source("argus:0", width=1280, height=720) as cam:
    a.send("OFF"); a.send("LEVEL 255"); time.sleep(2.0); off = average(cam)
    a.send("ON"); time.sleep(2.0); on = average(cam); a.send("OFF")
diff = on.mean(axis=2) - off.mean(axis=2)
k = cv2.GaussianBlur(diff, (21,21), 0)
print(cv2.minMaxLoc(k), diff.std())
PY
```
