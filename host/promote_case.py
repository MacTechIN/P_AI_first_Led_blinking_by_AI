#!/usr/bin/env python3
"""모듈 6 §4 — 결정 로그의 한 순간을 **골든셋 사례로 승격**한다.

    ./host/promote_case.py --list                     # 기록된 사건 보기
    ./host/promote_case.py --seq 42 --to golden/field # 그 순간을 사례로
    ./host/promote_case.py --changed --to golden/field  # 명령이 바뀐 순간만

현장에서 "LED 가 이상했다" 는 신고를 받았을 때 할 일이 이것이다. 그 순간의
프레임과 모델의 답이 남아 있으면, 고치기 전에 **먼저 사례로 고정**한다.
고치고 나서 만들면 무엇을 고쳤는지 증명할 수 없다.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control.decisionlog import DEFAULT_DIR, DecisionLog, promote


def main() -> None:
    p = argparse.ArgumentParser(description="결정 로그 → 골든셋")
    p.add_argument("--dir", default=DEFAULT_DIR)
    p.add_argument("--to", default="golden/field")
    p.add_argument("--seq", type=int, action="append", help="승격할 순번 (여러 번)")
    p.add_argument("--changed", action="store_true", help="명령이 바뀐 순간만")
    p.add_argument("--fields", default="action,colour",
                   help="무엇을 고정할지. 적지 않은 것은 조용히 통과한다")
    p.add_argument("--list", action="store_true")
    args = p.parse_args()

    log = DecisionLog(args.dir)
    entries = log.entries()
    if not entries:
        sys.exit(f"기록이 없다: {log.path}")

    if args.list:
        print(f"{len(entries)}건\n")
        for e in entries:
            d = e.get("decision")
            mark = "*" if e["changed"] else " "
            lag = f"  지연 {e['lag_frames']}프레임" if "lag_frames" in e else ""
            print(f" {mark}[{e['seq']:5d}] {e['command']:28s} "
                  + (f"모델 {d['action']}/{d['colour']}{lag}" if d else "모델 없음")
                  + ("" if "frame" in e else "   (프레임 없음 — 승격 불가)"))
        return

    picked = entries
    if args.seq:
        picked = [e for e in entries if e["seq"] in set(args.seq)]
    elif args.changed:
        picked = [e for e in entries if e["changed"]]

    fields = tuple(f.strip() for f in args.fields.split(",") if f.strip())
    cases = promote(picked, args.dir, args.to, fields=fields)
    if not cases:
        sys.exit("승격할 사례가 없다 (프레임이나 모델 판단이 빠져 있다)")

    print(f"{len(cases)}개 사례를 {args.to}/ 에 만들었습니다. 고정한 필드: {', '.join(fields)}")
    print("\n이제 회귀로 돌릴 수 있습니다:")
    print(f"  ./host/evaluate.py --golden {args.to}")
    print("\n적지 않은 필드의 회귀는 조용히 통과합니다 — 무엇을 고정할지가 선언입니다.")


if __name__ == "__main__":
    main()
