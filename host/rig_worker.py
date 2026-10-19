#!/usr/bin/env python3
"""S-5 — 제출된 작업을 **하나씩** 돌린다. 장비가 하나이기 때문이다.

    ./host/rig_worker.py                 # 시뮬레이션 장비로 (기본)
    ./host/rig_worker.py --real          # 실물: 카메라 + /dev/ttyACM0
    ./host/rig_worker.py --once          # 한 건만 처리하고 끝

결과는 `runs/<작업 id>/` 에 떨어진다.

    report.json    요약 · 채점 · 지연
    timings.csv    스텝별 단계 지연
    commands.log   실제로 나간 명령만
    frames/        몇 장의 프레임

## 경계에 대해

제출된 정책은 **이 프로세스 안에서 그대로 실행된다. 격리가 아니다.** 신뢰하는
참가자의 코드를 돌리는 교실용 도구이고, 샌드박스인 척하지 않는다.

하드웨어 쪽 경계는 따로 있다. 명령은 `LedCommand` 계약을 통과해야 하고 범위
제한은 **펌웨어가** 강제한다 — 호스트 검사는 편의일 뿐이다(ADR-0003). 제출된
코드가 넘을 수 없는 선은 거기 하나뿐이고, 그래서 거기에 두었다.
"""

import argparse
import csv
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control.commands import LedCommand
from control.loop import ControlLoop, summarize
from perception.health import FrameHealthError
from sim.queue import QUEUE, RUNS, claim, finish
from sim.submission import load_policy
from sim.paths import SCENARIOS
from sim.scenario import ScenarioError, check, load_all, observe

FRAME_EVERY = 20
"""몇 스텝마다 프레임 한 장을 남길지. 영상 대신 이것으로 본다 (ffmpeg 없음)."""


def build_rig(real: bool, port: str, source_spec: str):
    """실물이면 카메라와 시리얼, 아니면 가상 현장."""
    from sim import SimActuator, SimSource, SimWorld

    world = SimWorld()
    if not real:
        return world, SimSource(world), SimActuator(world)

    from control.actuator import SerialLedActuator
    from perception import open_source

    return world, open_source(source_spec, wbmode=1, awblock=True, aelock=True), \
        SerialLedActuator(port)


def run_job(spec: dict, *, real: bool, port: str, source_spec: str,
            runs_dir: str = RUNS) -> dict:
    """작업 하나. 예외가 나도 보고서를 남기고 돌아온다."""
    out = Path(runs_dir) / spec["id"]
    (out / "frames").mkdir(parents=True, exist_ok=True)
    report = {"id": spec["id"], "team": spec["team"], "scenario": spec["scenario"],
              "note": spec.get("note", ""), "real": real, "error": None}

    scenarios = load_all(SCENARIOS)
    if spec["scenario"] not in scenarios:
        report["error"] = f"모르는 대본: {spec['scenario']}"
        (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
        return report

    sc = scenarios[spec["scenario"]]
    world, source, actuator = build_rig(real, port, source_spec)
    now = 0.0
    if hasattr(world, "clock") and not real:
        world.clock = lambda: now

    rows, commands, passed, failed = [], [], 0, 0
    try:
        policy = load_policy(spec["policy"])
        report["policy_name"] = policy.name

        with source:
            loop = ControlLoop(source, policy, actuator)
            fps = float(spec.get("fps", 10.0))
            steps = int(min(float(spec["seconds"]), sc.seconds) * fps)
            prev_cmd = None
            for i in range(steps):
                prev, now = now, i / fps
                sc.apply(world, now)
                r = loop.step()
                rows.append({"step": i, "t": round(now, 2), **
                             {k: round(v, 2) for k, v in r.timings_ms.items()}})
                if r.changed:
                    commands.append(f"{now:7.2f}  {r.command.describe()}")
                    prev_cmd = r.command
                for exp in sc.due(prev, now):
                    ok = check(exp, observe(r, policy))
                    passed, failed = passed + ok, failed + (not ok)
                if i % FRAME_EVERY == 0 and not real:
                    _save_frame(world.render(i), out / "frames" / f"{i:04d}.png")
    except FrameHealthError as e:
        report["error"] = f"건전성 검사: {e}"
    except Exception as e:                      # 제출 코드가 터져도 작업자는 산다
        report["error"] = f"{type(e).__name__}: {e}"
        report["traceback"] = traceback.format_exc()[-1200:]
    finally:
        if real:
            try:
                actuator.apply(LedCommand("off"))   # 남의 작업에 불을 켜둔 채 넘기지 않는다
            except Exception:
                pass
        actuator.close()

    results = []
    report["steps"] = len(rows)
    report["score"] = {"passed": passed, "failed": failed,
                       "total": len(sc.expect)}
    report["commands"] = len(commands)
    if rows:
        stage = {k: sum(r[k] for r in rows) / len(rows)
                 for k in rows[0] if k not in ("step", "t")}
        report["latency_ms"] = {k: round(v, 2) for k, v in stage.items()}

    with (out / "timings.csv").open("w", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    (out / "commands.log").write_text("\n".join(commands) + "\n")
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return report


def _save_frame(frame, path: Path) -> None:
    try:
        import cv2

        cv2.imwrite(str(path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    except Exception:
        pass


def main() -> None:
    p = argparse.ArgumentParser(description="제출 큐 작업자")
    p.add_argument("--queue", default=QUEUE)
    p.add_argument("--runs", default=RUNS)
    p.add_argument("--real", action="store_true", help="실물 카메라와 LED 를 쓴다")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--source", default="argus:0")
    p.add_argument("--once", action="store_true")
    p.add_argument("--poll", type=float, default=2.0)
    args = p.parse_args()

    where = "실물 장비" if args.real else "시뮬레이션 장비"
    print(f"작업자 시작 — {where} · 큐 {args.queue}/ · 결과 {args.runs}/")
    print("작업은 하나씩 돕니다. 장비가 하나이기 때문입니다.\n")

    while True:
        job = claim(args.queue)
        if job is None:
            if args.once:
                print("대기 중인 작업 없음")
                return
            time.sleep(args.poll)
            continue

        spec = json.loads(job.read_text())
        print(f"▶ {spec['id']}  팀 {spec['team']}  대본 {spec['scenario']}")
        t0 = time.perf_counter()
        report = run_job(spec, real=args.real, port=args.port,
                         source_spec=args.source, runs_dir=args.runs)
        dt = time.perf_counter() - t0
        finish(job, args.queue)

        if report["error"]:
            print(f"  실패 ({dt:.1f}초): {report['error']}")
        else:
            sc = report["score"]
            print(f"  완료 ({dt:.1f}초)  채점 {sc['passed']}/{sc['total']}  "
                  f"명령 {report['commands']}회  → {args.runs}/{spec['id']}/")
        if args.once:
            return


if __name__ == "__main__":
    main()
