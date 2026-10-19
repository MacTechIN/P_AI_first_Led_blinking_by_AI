#!/usr/bin/env python3
"""S-6 — 공개 세트와 **숨은 세트**로 함께 채점한다.

    ./host/leaderboard.py                    # teams/*/policy.py 전부
    ./host/leaderboard.py --team tuned       # 하나만
    ./host/leaderboard.py --detail           # 떨어진 사례를 보여준다

점수를 하나로 합치지 않는다. 정확도만 보면 더 나아 보이는 정책이 전송에서
열 배를 쓰고 있을 수 있고, 공개 세트 만점이 숨은 세트에서 무너질 수 있다.
**각각을 따로 보여주고 순위는 보는 사람이 정한다.**

`모델` 칸은 모델이 **쓸 수 있는 말을 한** 스텝의 비율이다. `action: "none"` 은
세지 않는다 — 판단을 내놓지 않은 것이므로. 규칙 정책은 `—` 로 둔다.

숨은 세트는 개발 중에 돌리지 않는다. 거기에 맞추기 시작하면 그것도 공개
세트가 된다. (저장소에 들어 있는 `scenarios/hidden/` 은 **구조의 본보기**다.
실제 수업에서는 강사가 자기 것을 따로 둔다 — 읽을 수 있는 것은 숨은 것이 아니다.)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control.loop import ControlLoop, summarize
from control.vlm import VlmPolicy
from perception.health import FrameHealthError
from rig_worker import load_policy
from sim import build_rig
from sim.scenario import ScenarioError, check, load_all, observe


def grade(policy_path: Path, directory: str, *, fps: float = 5.0, detail=False):
    """한 정책을 한 세트 전체로 채점한다."""
    policy = load_policy(policy_path)
    passed = failed = commands = steps = 0
    decided = 0
    latencies = []
    misses = []

    for name, sc in load_all(directory).items():
        rig = build_rig(seed=0)
        now = 0.0
        rig.world.clock = lambda: now
        try:
            with rig.source:
                loop = ControlLoop(rig.source, policy, rig.actuator)
                for i in range(int(sc.seconds * fps)):
                    prev, now = now, i / fps
                    sc.apply(rig.world, now)
                    r = loop.step()
                    steps += 1
                    latencies.append(r.total_ms)
                    d = getattr(policy, "last_decision", None)
                    if d is not None and d.action != "none":
                        decided += 1      # 모델이 **실제로 쓸 수 있는 말**을 한 스텝
                    for exp in sc.due(prev, now):
                        got = observe(r, policy)
                        if check(exp, got):
                            passed += 1
                        else:
                            failed += 1
                            misses.append((name, exp, got))
        except FrameHealthError as e:
            misses.append((name, None, str(e)))
            failed += len(sc.expect)
        commands += len(rig.actuator.history)

    is_model = isinstance(policy, VlmPolicy)
    if is_model:
        policy.stop()
    return {
        "passed": passed, "total": passed + failed,
        "commands": commands, "steps": steps,
        "ms": sum(latencies) / len(latencies) if latencies else 0.0,
        "model": (decided / steps) if (is_model and steps) else None,
        "misses": misses if detail else [],
        "name": policy.name,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="공개 · 숨은 세트 채점")
    p.add_argument("--teams", default="teams")
    p.add_argument("--public", default="scenarios")
    p.add_argument("--hidden", default="scenarios/hidden")
    p.add_argument("--team", help="한 팀만")
    p.add_argument("--detail", action="store_true")
    p.add_argument("--fps", type=float, default=5.0)
    args = p.parse_args()

    policies = sorted(Path(args.teams).glob("*/policy.py"))
    if args.team:
        policies = [q for q in policies if q.parent.name == args.team]
    if not policies:
        sys.exit(f"정책이 없다: {args.teams}/*/policy.py")

    rows = []
    for q in policies:
        try:
            pub = grade(q, args.public, fps=args.fps, detail=args.detail)
            hid = grade(q, args.hidden, fps=args.fps, detail=args.detail)
        except (ScenarioError, ValueError) as e:
            print(f"{q.parent.name}: 채점 불가 — {e}")
            continue
        rows.append((q.parent.name, pub, hid))

    print(f"\n{'팀':10s} {'정책':20s} {'공개':>8s} {'숨은':>8s} "
          f"{'지연':>9s} {'전송':>12s} {'모델':>7s}")
    print("─" * 80)
    for team, pub, hid in rows:
        per100 = (pub["commands"] + hid["commands"]) * 100 / max(1, pub["steps"] + hid["steps"])
        md = pub["model"]
        print(f"{team:10s} {pub['name']:20s} "
              f"{pub['passed']:3d}/{pub['total']:<4d} "
              f"{hid['passed']:3d}/{hid['total']:<4d} "
              f"{pub['ms']:7.1f}ms {per100:8.1f}/100 "
              f"{('—' if md is None else f'{md:.0%}'):>7s}")

    print("\n열을 하나씩만 보면 매번 다른 팀이 1등입니다. 그것이 요점입니다.")
    gap = [(t, p, h) for t, p, h in rows
           if p["total"] and h["total"] and
           p["passed"] / p["total"] - h["passed"] / h["total"] > 0.05]
    for team, pub, hid in gap:
        print(f"  ⚠ {team}: 공개 {pub['passed']}/{pub['total']} → "
              f"숨은 {hid['passed']}/{hid['total']}. 공개 세트에 맞췄거나, "
              f"공개 세트에만 있는 것에 기대고 있습니다 — 어느 쪽인지는 --detail 로 봅니다.")

    if args.detail:
        for team, pub, hid in rows:
            for where, res in (("공개", pub), ("숨은", hid)):
                for name, exp, got in res["misses"]:
                    if exp is None:
                        print(f"  {team} {where} {name}: {got}")
                        continue
                    diff = ", ".join(f"{k}={got.get(k)!r}(기대 {v!r})"
                                     for k, v in exp.expect.items() if got.get(k) != v)
                    print(f"  {team} {where} {name} {exp.at:5.1f}초  {diff}")


if __name__ == "__main__":
    main()
