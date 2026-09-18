#!/usr/bin/env python3
"""골든셋으로 정책을 평가한다 (µ6.3).

    ./host/evaluate.py                    # 기본 골든셋, VLM 정책
    ./host/evaluate.py --golden golden2   # 다른 골든셋
    ./host/evaluate.py --quiet            # 실패만 출력

종료코드가 0 이 아니면 회귀다. CI 에 그대로 걸 수 있다.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control import GoldenError, load_cases, run_golden
from control.vlm import VlmClient, VlmError


def main() -> None:
    p = argparse.ArgumentParser(description="골든셋 평가")
    p.add_argument("--golden", default="golden")
    p.add_argument("--endpoint", default="http://127.0.0.1:8080/v1/chat/completions")
    p.add_argument("--quiet", action="store_true", help="실패만 출력")
    args = p.parse_args()

    try:
        cases = load_cases(args.golden)
    except GoldenError as e:
        sys.exit(f"골든셋 오류: {e}")

    client = VlmClient(args.endpoint)

    def ask(image):
        decision, _, _ = client.ask(image)
        return decision

    print(f"골든셋 {args.golden}: 사례 {len(cases)}개\n")
    report = run_golden(cases, ask)

    for r in report.results:
        if not args.quiet or not r.passed:
            print(r.describe())

    print(f"\n{report.summary()}")
    if report.failures():
        print("\n회귀:")
        for r in report.failures():
            print(f"  - {r.case.name}: {r.case.note or '(설명 없음)'}")
    sys.exit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
