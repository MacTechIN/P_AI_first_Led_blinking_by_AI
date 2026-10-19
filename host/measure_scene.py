#!/usr/bin/env python3
"""예제 3 실측 — **같은 프레임에 같은 답을 하는가.**

    ./host/measure_scene.py --repeat 10
    ./host/measure_scene.py --dir golden/scene --repeat 5

규칙은 읽어서 검증된다. 모델은 그럴 수 없으므로 **재서** 확인하는 수밖에 없고,
가장 먼저 재야 할 것은 정확도가 아니라 **재현성**이다. 같은 입력에 답이
흔들리면 정확도를 재는 것 자체가 의미가 없다.
"""

import argparse
import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from control.scene import (NO_ABSTAIN_SCHEMA, SCENE_PROMPT, SCENE_SCHEMA, SceneError,
                           validate_scene)
from control.vlm import VlmClient, VlmError


def ask_scene(client: VlmClient, image, *, abstain: bool = True):
    """장면 질문용으로 스키마와 프롬프트를 바꿔 묻는다."""
    import control.vlm as vlm

    saved_schema, saved_prompt = vlm.RESPONSE_SCHEMA, client.prompt
    vlm.RESPONSE_SCHEMA = SCENE_SCHEMA if abstain else NO_ABSTAIN_SCHEMA
    allowed = ("tidy", "cluttered") + (("uncertain",) if abstain else ())
    saved_validate = vlm.validate
    vlm.validate = lambda o: validate_scene(o, allowed)
    client.prompt = SCENE_PROMPT if abstain else SCENE_PROMPT.replace(
        "verdict is one of tidy, cluttered, uncertain. Use uncertain when the "
        "image does not show a work area clearly. ", "verdict is tidy or cluttered. ")
    try:
        return client.ask(image)
    finally:
        vlm.RESPONSE_SCHEMA, vlm.validate = saved_schema, saved_validate
        client.prompt = saved_prompt


def main() -> None:
    p = argparse.ArgumentParser(description="장면 판단 재현성 측정")
    p.add_argument("--dir", default="golden/scene")
    p.add_argument("--repeat", type=int, default=10)
    p.add_argument("--endpoint", default="http://127.0.0.1:8080/v1/chat/completions")
    p.add_argument("--no-abstain", action="store_true",
                   help="기권 선택지를 뺀다 — 모델이 무엇을 하는지 본다")
    args = p.parse_args()

    import cv2

    files = sorted(Path(args.dir).glob("*.jpg"))
    if not files:
        sys.exit(f"이미지가 없다: {args.dir}")

    client = VlmClient(args.endpoint, max_tokens=120)
    mode = "기권 없음 (tidy/cluttered 만)" if args.no_abstain else "기권 허용"
    print(f"{len(files)}개 프레임 × {args.repeat}회 · {mode}\n")

    grand = collections.Counter()
    for f in files:
        img = cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2RGB)
        votes, lats, evidences, errors = collections.Counter(), [], [], 0
        for _ in range(args.repeat):
            try:
                decision, lat, _ = ask_scene(client, img, abstain=not args.no_abstain)
            except (VlmError, SceneError) as e:
                errors += 1
                print(f"  {f.name}: 실패 {str(e)[:60]}")
                continue
            votes[decision["verdict"]] += 1
            evidences.append(decision["evidence"])
            lats.append(lat)

        total = sum(votes.values())
        if not total:
            continue
        top, n = votes.most_common(1)[0]
        grand[top] += 1
        spread = " · ".join(f"{k} {v}" for k, v in votes.most_common())
        print(f"{f.name}  다수 {top} {n}/{total} ({n/total:.0%})   {spread}")
        print(f"   평균 {sum(lats)/len(lats):.0f}ms"
              + (f"   실패 {errors}" if errors else ""))
        uniq = len(set(evidences))
        print(f"   근거 {uniq}가지 — 예: {evidences[0][:60]!r}")

    print("\n재현되지 않는 판단은 정확도를 재기 전에 먼저 고쳐야 합니다.")
    print("고칠 수 없다면, 그 흔들림을 **골든셋에 적어 두는 것**이 다음 단계입니다.")


if __name__ == "__main__":
    main()
