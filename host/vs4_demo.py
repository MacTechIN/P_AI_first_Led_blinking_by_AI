#!/usr/bin/env python3
"""VS-4 데모 — 카메라 → VLM → **역량 계약** → 장치.

모델이 보는 명령 목록, 강제되는 JSON 스키마, 출력 검증, 전송 문자열이 전부
`capabilities/*.json` 한 곳에서 나온다. 장치를 추가해도 이 파일은 바뀌지 않는다.

    ./host/vs4_demo.py                 # 실물
    ./host/vs4_demo.py --dry-run       # 전송 없이 판단만
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control.capability import ContractActuator, ContractError, Registry
from control.vlm import ContractVlmClient, VlmError
from perception import open_source


def main() -> None:
    p = argparse.ArgumentParser(description="VS-4: 역량 계약 위의 VLM 제어")
    p.add_argument("--capabilities", default=None, help="선언 디렉터리")
    p.add_argument("--source", default="argus:0")
    p.add_argument("--rounds", type=int, default=5)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    registry = Registry.load(args.capabilities) if args.capabilities else Registry.load()
    print("=== 선언된 역량 (모델이 보는 그대로) ===")
    print(registry.describe())
    print(f"\n스키마 옵션 {len(registry.tool_schema()['oneOf'])}개, "
          f"장치 {len(registry.devices)}개\n")

    client = ContractVlmClient(registry)
    actuator = None if args.dry_run else ContractActuator(registry)
    cam = open_source(args.source, width=1280, height=720,
                      wbmode=1, awblock=True, aelock=True)

    stats = {"ok": 0, "violation": 0, "failed": 0}
    try:
        with cam:
            for i in range(args.rounds):
                img = cam.read().image
                t0 = time.perf_counter()
                try:
                    call, ms, _ = client.ask(img)
                except VlmError as e:
                    kind = "violation" if "계약 위반" in str(e) else "failed"
                    stats[kind] += 1
                    print(f"  [{i}] ❌ {e}")
                    continue

                lines = actuator.apply(call) if actuator else registry.render(call)
                stats["ok"] += 1
                print(f"  [{i}] {call.describe():46s} {ms:6.0f}ms  → {lines}")
                time.sleep(0.3)
    finally:
        if actuator:
            actuator.close()

    print(f"\n결과: {stats}")


if __name__ == "__main__":
    main()
