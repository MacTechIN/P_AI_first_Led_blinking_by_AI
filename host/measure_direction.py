#!/usr/bin/env python3
"""예제 1 측정 — 공간 판단에서 규칙과 VLM 중 무엇이 나은가.

정답이 확실한 합성 이미지로 양쪽을 같은 자로 잰다. 사각형을 넣은 위치가
정답이므로 채점에 논란의 여지가 없다.

    ./host/measure_direction.py
    ./host/measure_direction.py --positions 9
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control import extract, zone_of
from control.vlm import VlmClient, VlmError
from perception import SyntheticSource, patch

VLM_PROMPT = (
    "A coloured rectangle sits somewhere in this image. Ignoring everything "
    "else, is it on the LEFT third, the CENTRE third, or the RIGHT third of "
    "the frame? Reply with exactly one word: left, centre, or right."
)

ZONE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["on"]},
        "colour": {"type": "string", "enum": ["blue", "green", "red"]},
        "reason": {"type": "string", "maxLength": 40},
    },
    "required": ["action", "colour", "reason"],
    "additionalProperties": False,
}
# 모델에게 방향 어휘를 새로 가르치는 대신, 이미 쓰던 색 어휘에 실어 보낸다.
# 스키마를 하나 더 만들면 계약이 또 갈라진다 (ADR-0009).
COLOUR_TO_ZONE = {"blue": "left", "green": "centre", "red": "right"}
ZONE_PROMPT = (
    "A coloured rectangle sits somewhere in this image. Reply 'blue' if it is "
    "on the left third of the frame, 'green' if in the centre third, 'red' if "
    "on the right third. Set action to 'on'."
)


def scene(x_centre: float, size=(640, 480)) -> np.ndarray:
    """정답이 x_centre 인 장면을 만든다. 사각형 폭은 화면의 16%."""
    half = 0.08
    box = (max(0.0, x_centre - half), 0.35, min(1.0, x_centre + half), 0.65)
    painter = patch(fg=(235, 225, 40), bg=(24, 24, 28), box=box)
    return SyntheticSource(painter).open().read().image


def main() -> None:
    p = argparse.ArgumentParser(description="방향 판단: 규칙 vs VLM")
    p.add_argument("--positions", type=int, default=9)
    p.add_argument("--endpoint", default="http://127.0.0.1:8080/v1/chat/completions")
    p.add_argument("--json", default=None)
    p.add_argument("--skip-vlm", action="store_true")
    args = p.parse_args()

    xs = [round(0.10 + i * (0.80 / (args.positions - 1)), 3)
          for i in range(args.positions)]
    # max_tokens 가 모자라면 스키마를 강제해도 JSON 이 도중에 끊긴다. 잘린 JSON 은
    # 유효하지 않은 JSON 이고, 증상은 "모델이 이상한 답을 한다" 로 보인다.
    # 실측: 24 토큰에서 9개 전부 실패, reason 필드 중간에서 끊겼다.
    client = None if args.skip_vlm else VlmClient(
        args.endpoint, prompt=ZONE_PROMPT, max_tokens=80)
    if client:
        import control.vlm as V
        V.RESPONSE_SCHEMA.clear(); V.RESPONSE_SCHEMA.update(ZONE_SCHEMA)

    rows = []
    print(f"{'정답 x':>7s} {'정답 구역':9s} {'규칙':9s} {'ms':>6s}   "
          f"{'VLM':9s} {'ms':>7s}")
    print("-" * 58)

    for x in xs:
        img = scene(x)
        truth = zone_of(x)

        t0 = time.perf_counter()
        # 방향 판단은 가장자리도 봐야 한다. 색 판별의 기본 ROI(가운데 60%)는
        # 화면 끝의 물체를 아예 보지 못한다.
        f = extract(img, roi=(0.02, 0.15, 0.98, 0.85))
        rule = zone_of(f.centroid_x) if f.centroid_x is not None else "none"
        rule_ms = (time.perf_counter() - t0) * 1000

        vlm, vlm_ms = "-", 0.0
        if client:
            try:
                ans, vlm_ms, _ = client.ask(img)
                vlm = COLOUR_TO_ZONE.get(str(ans.get("colour")), "?")
            except VlmError as e:
                vlm = f"err"
        rows.append({"x": x, "truth": truth, "rule": rule,
                     "rule_ms": round(rule_ms, 2), "vlm": vlm,
                     "vlm_ms": round(vlm_ms)})
        print(f"{x:7.2f} {truth:9s} {rule:9s} {rule_ms:6.1f}   "
              f"{vlm:9s} {vlm_ms:6.0f}" + ("  OK" if vlm == truth else
                                           ("" if not client else "  MISS")))

    print("-" * 58)
    rh = sum(r["rule"] == r["truth"] for r in rows)
    print(f"규칙 {rh}/{len(rows)}   평균 {sum(r['rule_ms'] for r in rows)/len(rows):.2f} ms")
    if client:
        vh = sum(r["vlm"] == r["truth"] for r in rows)
        vm = [r["vlm_ms"] for r in rows if r["vlm_ms"]]
        print(f"VLM  {vh}/{len(rows)}   평균 {sum(vm)/len(vm):.0f} ms"
              if vm else "VLM  측정 실패")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2))
        print(f"저장: {args.json}")


if __name__ == "__main__":
    main()
