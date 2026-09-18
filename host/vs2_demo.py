#!/usr/bin/env python3
"""VS-2 데모 — 카메라로 색을 보고 LED 를 제어한다. AI 없음, 규칙 기반.

    ./host/vs2_demo.py                    # 실물 카메라 + 실물 LED
    ./host/vs2_demo.py --source synthetic # 하드웨어 없이
    ./host/vs2_demo.py --dry-run          # 카메라만, LED 미구동

기본 정책(mirror): 본 색을 LED 에 그대로 띄운다. 빨강만 경고로 점멸시킨다.
대체 정책(rule)  : 색을 점멸 주기로 부호화한다 (단색 LED 배선용).
어느 쪽이든 밝기는 물체가 차지하는 면적에 비례한다.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control import (
    ColorRulePolicy,
    ControlLoop,
    MirrorColorPolicy,
    NullActuator,
    SerialLedActuator,
    summarize,
)
from perception import open_source


def main() -> None:
    p = argparse.ArgumentParser(description="VS-2: 색 판별 기반 LED 제어")
    p.add_argument("--source", default="argus:0", help="argus:0 | v4l2:0 | synthetic")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--steps", type=int, default=40)
    p.add_argument("--width", type=int, default=640)
    p.add_argument("--height", type=int, default=480)
    p.add_argument("--dry-run", action="store_true", help="LED 를 구동하지 않는다")
    p.add_argument("--policy", choices=["mirror", "rule", "vlm"], default="mirror")
    p.add_argument("--vlm-url", default="http://127.0.0.1:8080/v1/chat/completions")
    p.add_argument("--lock", action="store_true", help="화이트밸런스·노출 고정")
    args = p.parse_args()

    kw = {} if args.source == "synthetic" else {"width": args.width, "height": args.height}
    if args.lock and args.source != "synthetic":
        kw |= {"wbmode": 1, "awblock": True, "aelock": True}
    source = open_source(args.source, **kw)
    if args.policy == "vlm":
        from control import VlmClient, VlmPolicy
        policy = VlmPolicy(VlmClient(args.vlm_url), fallback=MirrorColorPolicy())
    elif args.policy == "mirror":
        policy = MirrorColorPolicy()
    else:
        policy = ColorRulePolicy()
    actuator = NullActuator() if args.dry_run else SerialLedActuator(args.port)

    print(f"소스 {args.source}  정책 {policy.name}  "
          f"액추에이터 {type(actuator).__name__}  {args.steps} 스텝")
    print("색 있는 물체를 카메라 앞에서 움직여 보세요.\n")

    started = getattr(policy, "start", lambda: policy)()
    try:
        with source:
            loop = ControlLoop(source, policy, actuator)
            results = loop.run(steps=args.steps, on_step=lambda r: print(r.describe()))
    finally:
        getattr(policy, "stop", lambda: None)()
        actuator.close()

    s = summarize(results)
    print("\n=== 종단 지연 (µ2.3) ===")
    for k in ("capture", "extract", "decide", "actuate"):
        print(f"  {k:9s} {s[k+'_ms']:7.1f} ms")
    print(f"  {'합계':9s} {s['total_ms']:7.1f} ms   p95 {s['p95_ms']:.1f} ms"
          f"   {s['fps']:.1f} fps")
    changes = sum(1 for r in results if r.changed)
    print(f"  명령 전송 {changes}회 / {len(results)} 스텝")
    if hasattr(policy, "stats"):
        print(f"  VLM {policy.stats}")
        if policy.last_decision:
            print(f"  마지막 판단: {policy.last_decision.describe()}")


if __name__ == "__main__":
    main()
