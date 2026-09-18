#!/usr/bin/env python3
"""예제 2 측정 — 노이즈 바닥을 재고 그 위에서 임계값을 정한다.

임계값을 추측으로 정하면 오경보가 나거나 진짜 변화를 놓친다. 순서는 하나뿐이다:
**정지 장면의 노이즈를 먼저 재고**, 알려진 변화에 대한 반응을 재고, 둘을 가르는
값을 고른다.

    ./host/measure_motion.py
    ./host/measure_motion.py --no-lock    # 자동보정을 켜고 비교
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from blink import Arduino
from control import MotionDetector
from perception import open_source


def sample(cam, det, n):
    out = []
    for _ in range(n):
        s = det.score(cam.read().image)
        if s is not None:
            out.append(s)
    return np.array(out)


def stat(label, a):
    if a.size == 0:
        print(f"  {label:22s} (표본 없음)")
        return
    print(f"  {label:22s} 평균 {a.mean():6.3f}  p95 {np.percentile(a,95):6.3f}"
          f"  최대 {a.max():6.3f}  n={a.size}")


def main() -> None:
    p = argparse.ArgumentParser(description="움직임 임계값 측정")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--source", default="argus:0")
    p.add_argument("--frames", type=int, default=60)
    p.add_argument("--no-lock", action="store_true",
                   help="자동노출·화이트밸런스를 켠 채로 잰다")
    args = p.parse_args()

    kw = {"width": 1280, "height": 720}
    if not args.no_lock:
        kw |= {"wbmode": 1, "awblock": True, "aelock": True}
    det = MotionDetector()

    print(f"자동보정 {'켜짐 (비교용)' if args.no_lock else '고정'}\n")

    with Arduino(args.port, verbose=False) as ard, open_source(args.source, **kw) as cam:
        ard.send("OFF"); time.sleep(1.5)
        det.reset(); cam.read()

        print("1) 정지 장면의 노이즈 바닥")
        noise = sample(cam, det, args.frames)
        stat("정지 (LED 소등)", noise)

        print("\n2) 알려진 변화 — LED 점등/소등")
        changes = []
        for i in range(6):
            ard.send("RGB 255 255 255"); ard.send("LEVEL 200"); ard.send("ON")
            time.sleep(0.5); cam.read()
            s = det.score(cam.read().image)
            if s is not None: changes.append(s)
            ard.send("OFF"); time.sleep(0.5); cam.read()
            s = det.score(cam.read().image)
            if s is not None: changes.append(s)
        stat("LED 상태 전환", np.array(changes))
        ard.send("OFF")

    if noise.size and changes:
        ch = np.array(changes)
        floor, signal = np.percentile(noise, 95), ch.mean()
        print(f"\n3) 임계값 후보")
        print(f"  노이즈 p95 {floor:.3f} · 신호 평균 {signal:.3f}"
              f" · 여유 {signal/max(floor,1e-6):.1f}배")
        for k in (2, 3, 5):
            t = floor * k
            fp = (noise >= t).mean() * 100
            tp = (ch >= t).mean() * 100
            print(f"  임계 {t:6.3f} (p95×{k})   오경보 {fp:5.1f}%   검출 {tp:5.1f}%")
        print("\n  오경보 0% 를 유지하는 가장 낮은 값을 고른다 — 낮을수록 민감하다.")


if __name__ == "__main__":
    main()
