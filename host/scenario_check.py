#!/usr/bin/env python3
"""S-2 — 장면 대본을 돌리고 기대와 대조한다. 장면이 곧 골든셋이다.

    ./host/scenario_check.py                # 대본 전부
    ./host/scenario_check.py --scenario dusk
    ./host/scenario_check.py --fault stale-roi   # 결함을 넣고 돌린다

종료코드가 0 이 아니면 기대를 못 맞춘 것이다. 골든셋과 같은 규칙으로
**부분 일치**만 본다 — 적어둔 필드만 검사한다.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control.direction import zone_of
from perception.health import FrameHealthError
from sim import build_rig
from sim.scenario import ScenarioError, check, load_all

DEFAULT_FPS = 10.0


def observed(result) -> dict:
    """기대와 맞춰 볼 한 스텝의 요약."""
    f = result.features
    return {
        "color": f.color,
        "zone": zone_of(f.centroid_x) if f.centroid_x is not None else None,
        "action": result.command.mode,
    }


def play(scenario, *, fault=None, fps=DEFAULT_FPS, seed=0, verbose=True):
    """대본을 **가상 시계**로 돌린다. 24초짜리가 순식간에 끝난다."""
    rig = build_rig(fault, seed=seed)
    now = 0.0
    rig.world.clock = lambda: now
    passed = failed = 0

    with rig.source:
        loop = rig.loop()
        steps = int(scenario.seconds * fps)
        for i in range(steps):
            prev, now = now, i / fps
            scenario.apply(rig.world, now)
            try:
                result = loop.step()
            except FrameHealthError as e:
                print(f"  건전성 검사가 막았다: {str(e)[:60]}")
                return 0, len(scenario.expect)

            for exp in scenario.due(prev, now):
                got = observed(result)
                ok = check(exp, got)
                passed, failed = passed + ok, failed + (not ok)
                if verbose or not ok:
                    diff = ", ".join(f"{k}={got.get(k)!r}(기대 {v!r})"
                                     for k, v in exp.expect.items()
                                     if got.get(k) != v)
                    print(f"  {'PASS' if ok else 'FAIL'}  {exp.at:5.1f}초  "
                          f"{diff or exp.note or '일치'}")
    return passed, failed


def main() -> None:
    p = argparse.ArgumentParser(description="장면 대본 검사")
    p.add_argument("--dir", default="scenarios")
    p.add_argument("--scenario", help="이름 하나만 돌린다")
    p.add_argument("--fault", help="결함을 하나 넣고 돌린다")
    p.add_argument("--fps", type=float, default=DEFAULT_FPS)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    try:
        scenarios = load_all(args.dir)
    except ScenarioError as e:
        sys.exit(f"대본 오류: {e}")

    if args.scenario:
        if args.scenario not in scenarios:
            sys.exit(f"모르는 대본: {args.scenario}  (가능: {', '.join(scenarios)})")
        scenarios = {args.scenario: scenarios[args.scenario]}

    total_p = total_f = 0
    for name, s in scenarios.items():
        print(f"\n{s.describe()}")
        if s.note:
            print(f"  {s.note}")
        pa, fa = play(s, fault=args.fault, fps=args.fps, verbose=not args.quiet)
        total_p, total_f = total_p + pa, total_f + fa

    print(f"\n{total_p}/{total_p + total_f} 통과"
          + (f"   (결함 {args.fault} 주입됨)" if args.fault else ""))
    sys.exit(0 if total_f == 0 else 1)


if __name__ == "__main__":
    main()
