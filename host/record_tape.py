#!/usr/bin/env python3
"""S-4 — 장면 대본을 실제 VLM 에게 한 번 물어 기록한다.

    ./host/record_tape.py                      # 모든 대본, 실물 서버
    ./host/record_tape.py --scenario dusk
    ./host/record_tape.py --client sim         # 서버 없이 (모양만 확인할 때)

**실습 전에 강사가 한 번** 돌린다. 그 뒤로는 수강생 노트북이 `tapes/*.json` 만
읽으면 되고, 서버도 GPU 도 필요 없다.

`/health` 가 ok 를 돌려주는 것은 작동의 증거가 아니므로, 기록을 시작하기 전에
실제 요청을 한 번 보내 본다.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control.vlm import VlmClient, VlmError
from sim import build_rig
from sim.replay import RecordingVlmClient, Tape
from sim.paths import SCENARIOS, TAPES
from sim.scenario import ScenarioError, load_all


def main() -> None:
    p = argparse.ArgumentParser(description="VLM 응답 기록")
    p.add_argument("--dir", default=SCENARIOS)
    p.add_argument("--out", default=TAPES)
    p.add_argument("--scenario")
    p.add_argument("--client", choices=["real", "sim"], default="real")
    p.add_argument("--endpoint", default="http://127.0.0.1:8080/v1/chat/completions")
    p.add_argument("--every", type=float, default=1.0, help="몇 초마다 한 번 물을지")
    args = p.parse_args()

    try:
        scenarios = load_all(args.dir)
    except ScenarioError as e:
        sys.exit(f"대본 오류: {e}")
    if args.scenario:
        if args.scenario not in scenarios:
            sys.exit(f"모르는 대본: {args.scenario}")
        scenarios = {args.scenario: scenarios[args.scenario]}

    out = Path(args.out)
    total = 0
    for name, sc in scenarios.items():
        rig = build_rig(seed=0)
        now = 0.0
        rig.world.clock = lambda: now

        if args.client == "sim":
            from sim.vlm import SimVlmClient
            inner: VlmClient = SimVlmClient(rig.world, latency_ms=900.0)
            model = "sim-qwen2.5-vl-3b"
        else:
            inner = VlmClient(args.endpoint)
            model = "Qwen2.5-VL-3B-Instruct-Q4_K_M"

        tape = Tape(source=f"{name} ({args.dir})", model=model)
        rec = RecordingVlmClient(inner, tape, note=name)

        print(f"\n{sc.describe()}  →  {out / (name + '.json')}")
        with rig.source as src:
            t = 0.0
            while t <= sc.seconds:
                now = t
                sc.apply(rig.world, t)
                obs = src.read()
                try:
                    decision, latency, _ = rec.ask(obs.image)
                except VlmError as e:
                    sys.exit(f"\n기록 실패 (t={t:.1f}): {e}\n"
                             f"서버가 떠 있어도 요청이 죽을 수 있습니다 — "
                             f"docs/tech/notes/vlm-on-orin-nano.md")
                print(f"  {t:5.1f}초  {decision['action']:5s} "
                      f"{str(decision['colour']):7s} {latency:6.0f}ms")
                t += args.every

        tape.save(out / f"{name}.json")
        total += len(tape.entries)
        print(f"  저장: {tape.describe()}")

    print(f"\n{total}건 기록. 이제 서버 없이 재생할 수 있습니다:")
    print("  ./host/scenario_check.py --policy tape")


if __name__ == "__main__":
    main()
