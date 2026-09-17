#!/usr/bin/env python3
"""RGB LED 폐루프 색상 검증.

명령한 색과 **카메라가 실제로 찍은 색**이 일치하는지 대조한다.
LED 자체가 피사체이므로 사람이 물체를 들고 있을 필요가 없다.

절차
  1. LED 를 끈 상태와 흰색으로 켠 상태를 차분해 화면에서 LED 위치를 찾는다.
  2. 색마다: 명령 → 안정화 대기 → 여러 프레임 평균 → LED 영역의 색조 측정.
  3. 명령 색조와 측정 색조를 원형 거리로 비교한다.

    ./host/verify_rgb.py
    ./host/verify_rgb.py --level 120 --tolerance 25
"""

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from blink import Arduino
from perception import open_source

# 파랑이 PWM 이 아닌 배선에서도 재현 가능한 색만 고른다. 채널을 켜거나 끄는
# 조합이라 pin 12 의 2단계 동작에 영향받지 않는다.
COLORS: list[tuple[str, tuple[int, int, int]]] = [
    ("red", (255, 0, 0)),
    ("yellow", (255, 255, 0)),
    ("green", (0, 255, 0)),
    ("cyan", (0, 255, 255)),
    ("blue", (0, 0, 255)),
    ("magenta", (255, 0, 255)),
]


def rgb_to_hue(rgb: tuple[int, int, int]) -> float:
    """OpenCV 색조 0-179."""
    px = np.uint8([[list(rgb)]])
    return float(cv2.cvtColor(px, cv2.COLOR_RGB2HSV)[0, 0, 0])


def hue_distance(a: float, b: float) -> float:
    """색조는 원형이다. 179 와 0 은 1 만큼 떨어져 있지 실제로 179 가 아니다."""
    d = abs(a - b) % 180
    return min(d, 180 - d)


def average_frames(cam, n: int) -> np.ndarray:
    return np.mean([cam.read().image.astype(np.float32) for _ in range(n)], axis=0)


def locate_led(ard: Arduino, cam, *, level: int, samples: int, settle: float):
    """LED 의 화면상 위치를 차분으로 찾는다."""
    ard.send("OFF")
    time.sleep(settle)
    off = average_frames(cam, samples)

    ard.send("RGB 255 255 255")
    ard.send(f"LEVEL {level}")
    ard.send("ON")
    time.sleep(settle)
    on = average_frames(cam, samples)
    ard.send("OFF")

    diff = cv2.GaussianBlur(on.mean(axis=2) - off.mean(axis=2), (21, 21), 0)
    _, vmax, _, loc = cv2.minMaxLoc(diff)
    return loc, float(vmax), float(diff.std())


SATURATED = 250.0
"""이 값 이상인 화소는 포화된 것으로 보고 색조 측정에서 뺀다."""


def crop(frame: np.ndarray, centre, half: int) -> np.ndarray:
    x, y = centre
    h, w = frame.shape[:2]
    return frame[max(0, y - half) : min(h, y + half),
                 max(0, x - half) : min(w, x + half)]


def measure_hue(frame: np.ndarray, baseline: np.ndarray, centre, half: int):
    """LED 가 **더한 빛**의 색조를 잰다.

    절대 프레임의 색조를 재면 실패한다 — ROI 면적의 대부분은 배경이고,
    배경은 명령한 색과 무관하므로 측정값이 명령과 상관없이 한 값에 고정된다.
    실측에서 여섯 색 모두 색조 ~95 로 읽혔다.

    그래서 소등 상태를 기준으로 차분한다. 남는 것은 LED 가 기여한 빛뿐이다.
    이는 LED 검출 실측에서 자동노출이 전역 밝기를 상쇄하던 것과 같은 이유로,
    차분이 유일하게 신뢰할 수 있는 관측이다.
    """
    lit = crop(frame, centre, half).astype(np.float32)
    dark = crop(baseline, centre, half).astype(np.float32)
    delta = np.clip(lit - dark, 0, 255)

    # 화소별 증가량으로 가중해 밝아진 곳(=LED)만 반영한다.
    weight = delta.sum(axis=2)

    # 포화 화소는 제외한다. LED 코어는 어떤 색이든 카메라를 포화시켜 흰색이
    # 되므로 색조 정보가 없다. 색은 주변부(halo)에만 남아 있다.
    weight = weight * (lit.max(axis=2) < SATURATED)
    if weight.sum() < 1:
        return None, 0.0, delta.astype(np.uint8)

    mean_rgb = (delta * weight[..., None]).sum(axis=(0, 1)) / weight.sum()
    px = np.uint8([[np.clip(mean_rgb, 0, 255)]])
    hsv = cv2.cvtColor(px, cv2.COLOR_RGB2HSV)[0, 0]
    return float(hsv[0]), float(hsv[1]), delta.astype(np.uint8)


def main() -> None:
    p = argparse.ArgumentParser(description="RGB LED 폐루프 색상 검증")
    p.add_argument("--source", default="argus:0")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--level", type=int, default=140,
                   help="과노출로 색조가 날아가면 낮춘다")
    p.add_argument("--tolerance", type=float, default=25.0, help="허용 색조 오차")
    p.add_argument("--samples", type=int, default=6)
    p.add_argument("--settle", type=float, default=1.2)
    p.add_argument("--roi", type=int, default=45, help="LED 주변 반경(px)")
    p.add_argument("--rounds", type=int, default=1, help="전체 색 순회 반복 횟수")
    p.add_argument("--out", default="/tmp/rgb_verify.jpg")
    p.add_argument("--lock", action="store_true",
                   help="화이트밸런스·노출을 고정한다 (측정 권장)")
    args = p.parse_args()

    cam_kw = {"width": 1280, "height": 720}
    if args.lock:
        # wbmode=1 은 수동 고정. AWB 가 색을 프레임마다 재해석하지 못하게 한다.
        cam_kw |= {"wbmode": 1, "awblock": True, "aelock": True}
    cam = open_source(args.source, **cam_kw)
    rows: list[tuple] = []

    with Arduino(args.port, verbose=False) as ard, cam:
        print(ard.send("STATE"))
        loc, vmax, noise = locate_led(
            ard, cam, level=args.level, samples=args.samples, settle=args.settle
        )
        print(f"\nLED 위치 {loc}  신호 +{vmax:.1f}  노이즈 {noise:.1f}  "
              f"SNR {vmax/max(noise,1e-6):.1f}x")
        if vmax < 3 * noise:
            print("경고: LED 신호가 약하다. 카메라를 LED 쪽으로 향하게 하라.")

        ard.send(f"LEVEL {args.level}")
        # 색 측정의 기준이 되는 소등 프레임
        ard.send("OFF")
        time.sleep(args.settle)
        baseline = average_frames(cam, args.samples)
        tiles = []
        for rnd in range(args.rounds):
            if args.rounds > 1:
                print(f"\n--- {rnd+1}/{args.rounds} 회차 ---")
            print(f"\n{'명령':9s} {'명령 색조':>9s} {'측정 색조':>9s} "
                  f"{'오차':>6s} {'채도':>6s}  판정")
            for name, rgb in COLORS:
                ard.send(f"RGB {rgb[0]} {rgb[1]} {rgb[2]}")
                ard.send("ON")
                time.sleep(args.settle)
                frame = average_frames(cam, args.samples)

                want = rgb_to_hue(rgb)
                got, sat, roi = measure_hue(frame, baseline, loc, args.roi)
                if got is None:
                    print(f"{name:9s} {want:9.0f} {'측정불가':>9s}")
                    rows.append((name, want, None, None, 0.0, False))
                    continue

                err = hue_distance(want, got)
                ok = err <= args.tolerance
                print(f"{name:9s} {want:9.0f} {got:9.0f} {err:6.1f} {sat:6.0f}  "
                      f"{'✅' if ok else '❌'}")
                rows.append((name, want, got, err, sat, ok))
                if rnd == 0:
                    tiles.append(cv2.resize(roi, (120, 120)))
        ard.send("OFF")

    passed = sum(1 for r in rows if r[5])
    print(f"\n결과: {passed}/{len(rows)} 일치 (허용 오차 {args.tolerance:.0f})")
    errs = [r[3] for r in rows if r[3] is not None]
    if errs:
        print(f"평균 색조 오차 {sum(errs)/len(errs):.1f}  최대 {max(errs):.1f}")

    if tiles:
        sheet = cv2.cvtColor(np.hstack(tiles), cv2.COLOR_RGB2BGR)
        cv2.imwrite(args.out, sheet)
        print(f"LED 촬영 이미지: {args.out}  (순서: "
              f"{', '.join(n for n, _ in COLORS)})")

    sys.exit(0 if passed == len(rows) else 1)


if __name__ == "__main__":
    main()
