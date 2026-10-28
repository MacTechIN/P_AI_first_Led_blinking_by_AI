#!/usr/bin/env python3
"""S-5 — 실물 장비에 작업을 제출한다. 큐는 직렬이다.

    ./host/submit.py --team A --policy teams/example/policy.py
    ./host/submit.py --team B --scenario dusk --seconds 24
    ./host/submit.py --list

카메라도 시리얼 포트도 VLM 도 **하나뿐이고 동시에 쓸 수 없다.** 그 제약이
그대로 구조가 된다 — 제출하고, 차례를 기다리고, 결과를 받는다.

제출한 정책은 `tapes/`·`scenarios/` 를 그대로 쓰고, 끝나면 `runs/` 아래에
단계별 지연·전송 기록·프레임·채점 결과가 떨어진다.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sim.queue import PENDING, QUEUE, job_id, pending_jobs


def main() -> None:
    p = argparse.ArgumentParser(description="실물 장비 작업 제출")
    p.add_argument("--team", default="anon")
    p.add_argument("--policy", default="teams/example/policy.py")
    p.add_argument("--scenario", default="basics")
    p.add_argument("--seconds", type=float, default=24.0)
    p.add_argument("--fps", type=float, default=10.0)
    p.add_argument("--note", default="")
    p.add_argument("--queue", default=QUEUE)
    p.add_argument("--list", action="store_true", help="대기 중인 작업만 보여준다")
    args = p.parse_args()

    pending = PENDING(args.queue)
    pending.mkdir(parents=True, exist_ok=True)

    if args.list:
        jobs = pending_jobs(args.queue)
        if not jobs:
            print("대기 중인 작업 없음")
            return
        print(f"대기 {len(jobs)}건")
        for i, j in enumerate(jobs, 1):
            spec = json.loads(j.read_text(encoding="utf-8"))
            print(f"  {i}. {spec['team']:8s} {spec['scenario']:8s} "
                  f"{spec['seconds']:.0f}초  {spec['submitted']}")
        return

    policy = Path(args.policy)
    if not policy.is_file():
        sys.exit(f"정책 파일이 없다: {policy}")

    jid = job_id(args.team)
    spec = {
        "id": jid,
        "team": args.team,
        "policy": str(policy.resolve()),
        "scenario": args.scenario,
        "seconds": args.seconds,
        "fps": args.fps,
        "note": args.note,
        "submitted": datetime.now().isoformat(timespec="seconds"),
    }
    path = pending / f"{jid}.json"
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")

    ahead = len(pending_jobs(args.queue)) - 1
    print(f"제출됨: {jid}")
    print(f"앞에 {ahead}건 대기" if ahead else "다음 차례입니다")
    print(f"\n결과는 runs/{jid}/ 에 떨어집니다. 작업자가 돌고 있어야 합니다:")
    print("  ./host/rig_worker.py")


if __name__ == "__main__":
    main()
