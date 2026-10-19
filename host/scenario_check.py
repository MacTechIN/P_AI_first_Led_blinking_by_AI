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

from perception.health import FrameHealthError
from sim import build_rig
from sim.scenario import ScenarioError, check, load_all, observe

DEFAULT_FPS = 10.0


def play(scenario, *, fault=None, fps=DEFAULT_FPS, seed=0, verbose=True,
         policy="mirror", tape_dir="tapes", tape_speed=0.0):
    """대본을 **가상 시계**로 돌린다. 24초짜리가 순식간에 끝난다."""
    kw = {}
    if policy == "tape":
        kw = {"tape": f"{tape_dir}/{scenario.name}.json", "tape_speed": tape_speed}
    rig = build_rig(fault, seed=seed, policy=policy, **kw)
    now = 0.0
    rig.world.clock = lambda: now
    passed = failed = 0

    from control.vlm import VlmPolicy

    with rig.source:
        loop = rig.loop()
        if isinstance(rig.policy, VlmPolicy):
            rig.policy.start()
        steps = int(scenario.seconds * fps)
        for i in range(steps):
            prev, now = now, i / fps
            scenario.apply(rig.world, now)
            try:
                result = loop.step()
            except FrameHealthError as e:
                print(f"  건전성 검사가 막았다: {str(e)[:60]}")
                return 0, len(scenario.expect)

            due = list(scenario.due(prev, now))
            if policy == "tape":
                due += scenario.due_tape(prev, now)
            for exp in due:
                got = observe(result, rig.policy)
                ok = check(exp, got)
                passed, failed = passed + ok, failed + (not ok)
                if verbose or not ok:
                    diff = ", ".join(f"{k}={got.get(k)!r}(기대 {v!r})"
                                     for k, v in exp.expect.items()
                                     if got.get(k) != v)
                    print(f"  {'PASS' if ok else 'FAIL'}  {exp.at:5.1f}초  "
                          f"{diff or exp.note or '일치'}")
        if isinstance(rig.policy, VlmPolicy):
            rig.policy.stop()
            if verbose and hasattr(rig.policy.client, "stats"):
                st = rig.policy.client.stats
                print(f"  기록 재생: 적중 {st['hits']}  빗나감 {st['misses']}")
    return passed, failed


def main() -> None:
    p = argparse.ArgumentParser(description="장면 대본 검사")
    p.add_argument("--dir", default="scenarios")
    p.add_argument("--scenario", help="이름 하나만 돌린다")
    p.add_argument("--fault", help="결함을 하나 넣고 돌린다")
    p.add_argument("--policy", choices=["mirror", "tape"], default="mirror",
                   help="tape 는 기록해 둔 실제 VLM 응답을 재생한다 (S-4)")
    p.add_argument("--tape-dir", default="tapes")
    p.add_argument("--tape-speed", type=float, default=0.0,
                   help="지연 배속. 0 이면 즉시, 1 이면 기록된 그대로")
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
        pa, fa = play(s, fault=args.fault, fps=args.fps, verbose=not args.quiet,
                      policy=args.policy, tape_dir=args.tape_dir,
                      tape_speed=args.tape_speed)
        total_p, total_f = total_p + pa, total_f + fa

    print(f"\n{total_p}/{total_p + total_f} 통과"
          + (f"   (결함 {args.fault} 주입됨)" if args.fault else ""))
    sys.exit(0 if total_f == 0 else 1)


if __name__ == "__main__":
    main()
