#!/usr/bin/env python3
"""LED 색상을 무지개로 연속 순환시킨다.

**타이밍을 호스트가 쥔다 — 의도적 예외다** (ADR-0001).
펌웨어는 고정 색과 점멸만 알고 색 순환은 모른다. 순환을 펌웨어에 넣으면
패턴을 바꿀 때마다 재플래싱해야 한다. 그리고 부드러운 페이드는 밀리초 정밀도가
필요 없어서, 호스트 지터가 눈에 보이지 않는다. `--pattern sos` 와 같은 경우다.

    ./host/rainbow.py                  # 기본: 6초에 한 바퀴
    ./host/rainbow.py --period 20      # 느리게
    ./host/rainbow.py --level 80       # 어둡게
    ./host/rainbow.py --steps 360      # 더 촘촘하게
"""

import argparse
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from blink import Arduino
from control import hue_to_rgb

_stop = False


def _on_signal(signum, frame):
    global _stop
    _stop = True


def main() -> None:
    p = argparse.ArgumentParser(description="무지개 색상 연속 순환")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--period", type=float, default=6.0, help="한 바퀴 도는 시간(초)")
    p.add_argument("--steps", type=int, default=90, help="한 바퀴의 색 단계 수")
    p.add_argument("--level", type=int, default=160, help="밝기 0-255")
    p.add_argument("--cycles", type=float, default=0, help="0 이면 무한")
    args = p.parse_args()

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    delay = args.period / args.steps
    limit = int(args.cycles * args.steps) if args.cycles else None

    print(f"무지개 순환: {args.period}초/바퀴, {args.steps}단계, 밝기 {args.level}")
    print("멈추려면 Ctrl-C\n")

    with Arduino(args.port, verbose=False) as ard:
        ard.send(f"LEVEL {args.level}")
        ard.send("ON")
        i = 0
        try:
            while not _stop and (limit is None or i < limit):
                # OpenCV 색상환은 0-179. 한 바퀴를 steps 등분해 돈다.
                hue = (i * 180 // args.steps) % 180
                r, g, b = hue_to_rgb(hue)
                ard.send(f"RGB {r} {g} {b}")
                if i % args.steps == 0:
                    print(f"  {i // args.steps + 1}바퀴 시작  hue={hue} "
                          f"#{r:02x}{g:02x}{b:02x}")
                time.sleep(delay)
                i += 1
        finally:
            # 어떤 경로로 끝나든 LED 를 끄고 나간다. 프로세스가 죽었는데
            # LED 가 켜진 채 남으면 다음 사람이 상태를 오해한다.
            ard.send("OFF")
            print(f"\n정지. {i}단계 ({i / args.steps:.1f}바퀴) 수행, LED 소등")


if __name__ == "__main__":
    main()
