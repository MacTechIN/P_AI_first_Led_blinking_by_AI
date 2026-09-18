#!/usr/bin/env python3
"""무지개를 돌리면서 VLM 이 그 색을 알아보는지 본다.

LED → 빛 → 카메라 → VLM → 답변까지 **전 경로를 한 번에 검증**한다.
명령한 색을 알고 있으므로 VLM 의 답을 채점할 수 있다.
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from blink import Arduino
from control import hue_to_rgb
from control.vlm import VlmClient, VlmError
from perception import open_source

WHEEL = [(0, "red"), (15, "orange"), (30, "yellow"), (45, "yellow"),
         (60, "green"), (75, "green"), (90, "cyan"), (105, "cyan"),
         (120, "blue"), (135, "purple"), (150, "purple"), (165, "red")]

# 색상환에서 이웃한 이름은 맞은 것으로 본다. 경계는 사람도 갈린다.
NEIGHBOURS = {
    "red": {"red", "orange", "purple", "magenta", "pink"},
    "orange": {"orange", "red", "yellow"},
    "yellow": {"yellow", "orange", "green"},
    "green": {"green", "yellow", "cyan"},
    "cyan": {"cyan", "green", "blue"},
    "blue": {"blue", "cyan", "purple"},
    "purple": {"purple", "blue", "red", "magenta", "pink"},
}

PROMPT = ("A small LED lamp is glowing in this image. What colour is the LED "
          "glowing? Answer with one word.")


def main() -> None:
    p = argparse.ArgumentParser(description="무지개 + VLM 인식 대조")
    p.add_argument("--port", default="/dev/ttyACM0")
    p.add_argument("--source", default="argus:0")
    p.add_argument("--steps", type=int, default=12)
    p.add_argument("--level", type=int, default=90)
    p.add_argument("--settle", type=float, default=1.2)
    p.add_argument("--json", default=None, help="결과를 JSON 으로 저장")
    args = p.parse_args()

    step = max(1, len(WHEEL) // args.steps)
    wheel = WHEEL[::step][: args.steps]
    client = VlmClient(prompt=PROMPT)
    cam = open_source(args.source, width=1280, height=720,
                      wbmode=1, awblock=True, aelock=True)

    rows = []
    print(f"{'명령한 색':10s} {'RGB':10s} {'VLM 답변':12s} {'지연':>9s}  판정")
    print("-" * 56)

    with Arduino(args.port, verbose=False) as ard, cam:
        ard.send(f"LEVEL {args.level}")
        ard.send("ON")
        try:
            for hue, name in wheel:
                r, g, b = hue_to_rgb(hue)
                ard.send(f"RGB {r} {g} {b}")
                time.sleep(args.settle)
                for _ in range(3):
                    cam.read()
                try:
                    ans, ms, _ = client.ask(cam.read().image)
                    said = str(ans.get("colour") or ans.get("action"))
                except VlmError as e:
                    print(f"{name:10s} #{r:02x}{g:02x}{b:02x}   {'실패':12s}"
                          f"          {str(e)[:20]}")
                    continue
                ok = said.lower() in NEIGHBOURS.get(name, {name})
                rows.append({"hue": hue, "commanded": name,
                             "rgb": f"#{r:02x}{g:02x}{b:02x}",
                             "vlm": said, "ms": round(ms), "ok": ok})
                print(f"{name:10s} #{r:02x}{g:02x}{b:02x}   {said:12s} "
                      f"{ms:6.0f}ms  {'OK' if ok else 'MISS'}")
        finally:
            ard.send("OFF")

    print("-" * 56)
    if rows:
        hits = sum(r["ok"] for r in rows)
        avg = sum(r["ms"] for r in rows) / len(rows)
        print(f"일치 {hits}/{len(rows)} ({100*hits/len(rows):.0f}%)  평균 {avg:.0f}ms")
        if args.json:
            Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=2))
            print(f"저장: {args.json}")


if __name__ == "__main__":
    main()
