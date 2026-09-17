#!/usr/bin/env python3
"""VS-2 데모 — 카메라로 색을 보고 LED 를 제어한다. AI 없음, 규칙 기반.

    ./host/vs2_demo.py                    # 실물 카메라 + 실물 LED
    ./host/vs2_demo.py --source synthetic # 하드웨어 없이
    ./host/vs2_demo.py --dry-run          # 카메라만, LED 미구동

색 → 반응:  빨강 100ms · 주황 200 · 노랑 300 · 초록 600 · 청록 800 · 보라 1000
            파랑 상시점등 · 물체 없음 소등.  밝기는 물체가 차지하는 면적에 비례.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control import ColorRulePolicy, ControlLoop, NullActuator, SerialLedActuator, summarize
from perception import open_source


def main() -> None:
    p = argparse.ArgumentParser(description="VS-2: 색 판별 기반 LED 제어")
    p.add_argument("--source", default="argus:0", help="argus:0 | v4l2:0 | synthetic")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--steps", type=int, default=40)
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--dry-run", action="store_true", help="LED 를 구동하지 않는다")
    args = p.parse_args()

    kw = {} if args.source == "synthetic" else {"width": args.width, "height": args.height}
    source = open_source(args.source, **kw)
    actuator = NullActuator() if args.dry_run else SerialLedActuator(args.port)

    print(f"소스 {args.source}  액추에이터 {type(actuator).__name__}  {args.steps} 스텝")
    print("색 있는 물체를 카메라 앞에서 움직여 보세요.\n")

    try:
        with source:
            loop = ControlLoop(source, ColorRulePolicy(), actuator)
            results = loop.run(steps=args.steps, on_step=lambda r: print(r.describe()))
    finally:
        actuator.close()

    s = summarize(results)
    print("\n=== 종단 지연 (µ2.3) ===")
    for k in ("capture", "extract", "decide", "actuate"):
        print(f"  {k:9s} {s[k+'_ms']:7.1f} ms")
    print(f"  {'합계':9s} {s['total_ms']:7.1f} ms   p95 {s['p95_ms']:.1f} ms"
          f"   {s['fps']:.1f} fps")
    changes = sum(1 for r in results if r.changed)
    print(f"  명령 전송 {changes}회 / {len(results)} 스텝")


if __name__ == "__main__":
    main()
