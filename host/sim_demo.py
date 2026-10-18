#!/usr/bin/env python3
"""S-1/S-3 데모 — 장비 하나 없이 제어 루프를 닫고, 거기에 결함을 넣는다.

    ./host/sim_demo.py                     # 색지가 바뀌고 LED 가 따라간다
    ./host/sim_demo.py --no-preview        # 터미널 그림 없이 로그만
    ./host/sim_demo.py --scenario dusk     # 장면 대본대로 움직인다 (S-2)
    ./host/sim_demo.py --fault list        # 넣을 수 있는 결함 목록
    ./host/sim_demo.py --fault random --seed 7    # 무엇이 켜졌는지 알려주지 않는다
    ./host/sim_demo.py --fault random --seed 7 --reveal   # 정답
    ./host/sim_demo.py --led-in-roi --led-radius 70 --cards green,none
                                           # 색지를 치워도 초록이라고 우긴다
    ./host/sim_demo.py --per-channel-resistor   # 올바른 배선이었다면
    ./host/sim_demo.py --policy rule       # 색을 점멸 주기로 부호화

왼쪽의 색지가 카메라가 보는 것, 오른쪽의 불빛이 정책이 켠 LED 다. 둘 다 같은
장면에 있으므로 **명령이 다음 프레임에 보인다** — 이것이 S-1 의 전부다.

LED 색이 명령과 달라 보이면 그것이 맞다. 공통 저항을 셋이 나눠 쓰는 실물의
성질을 그대로 재현하고 있다 (`docs/tech/notes/sim-led-model.md`).
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from control import ColorRulePolicy, MirrorColorPolicy, summarize
from control.vlm import VlmPolicy
from perception.health import FrameHealthError
from sim import FAULTS, LedPanel, SimActuator, SimSource, SimWorld, build_rig

CARDS: dict[str, tuple[int, int, int]] = {
    "red": (220, 40, 40),
    "orange": (230, 130, 30),
    "yellow": (225, 215, 50),
    "green": (40, 190, 70),
    "cyan": (40, 200, 200),
    "blue": (50, 70, 215),
    "purple": (150, 60, 200),
    "none": (30, 30, 34),
}


def preview(img: np.ndarray, cols: int = 56) -> str:
    """프레임을 터미널에 그린다. 반블록 한 글자가 세로 두 화소다."""
    h, w = img.shape[:2]
    rows = max(2, int(cols * h / w / 2) * 2)
    ys = (np.linspace(0, h - 1, rows)).astype(int)
    xs = (np.linspace(0, w - 1, cols)).astype(int)
    small = img[np.ix_(ys, xs)]

    out = []
    for y in range(0, rows - 1, 2):
        line = []
        for x in range(cols):
            tr, tg, tb = small[y, x]
            br, bg, bb = small[y + 1, x]
            line.append(f"\x1b[38;2;{tr};{tg};{tb}m\x1b[48;2;{br};{bg};{bb}m▀")
        out.append("".join(line) + "\x1b[0m")
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description="S-1: 장비 없는 닫힌 제어 루프")
    p.add_argument("--steps", type=int, default=60)
    p.add_argument("--cards", default="red,green,blue,yellow,none")
    p.add_argument("--dwell", type=int, default=12, help="색지 한 장을 몇 스텝 유지할지")
    p.add_argument("--policy", choices=["mirror", "rule", "vlm"], default="mirror")
    p.add_argument("--scenario", metavar="NAME",
                   help="scenarios/*.json 대본을 재생한다 (--cards 대신)")
    p.add_argument("--fault", metavar="NAME",
                   help="결함을 하나 넣는다. 'list' 로 목록, 'random' 으로 무작위")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--reveal", action="store_true", help="끝나고 정답을 보여준다")
    p.add_argument("--still", action="store_true",
                   help="색지를 바꾸지 않는다 — 정지 장면에서 전송 빈도를 센다")
    p.add_argument("--fps", type=float, default=12.0)
    p.add_argument("--no-preview", action="store_true")
    p.add_argument("--led-in-roi", action="store_true",
                   help="LED 를 ROI 안으로 옮긴다 (--led-radius 와 함께 써야 효과가 보인다)")
    p.add_argument("--led-radius", type=int, default=24,
                   help="LED 반경(px). 60 이상 + ROI 안이면 루프가 자기 출력을 먹는다")
    p.add_argument("--per-channel-resistor", action="store_true",
                   help="채널마다 저항이 있는 올바른 배선을 가정한다")
    p.add_argument("--save", metavar="DIR", help="프레임을 PNG 로 저장")
    args = p.parse_args()

    if args.fault == "list":
        print("넣을 수 있는 결함:\n")
        for f in FAULTS.values():
            print(f"  {f.name:16s} [{f.layer}]  {f.symptom}")
        print("\n--fault random --seed N 으로 무작위 주입. 정답은 --reveal.")
        return

    scenario = None
    if args.scenario:
        from sim.scenario import ScenarioError, load_all
        try:
            found = load_all()
        except ScenarioError as e:
            p.error(str(e))
        if args.scenario not in found:
            p.error(f"모르는 대본: {args.scenario}  (가능: {', '.join(found)})")
        scenario = found[args.scenario]
        args.steps = int(scenario.seconds * (args.fps or 10.0))

    cards = [c.strip() for c in args.cards.split(",") if c.strip()]
    unknown = [c for c in cards if c not in CARDS]
    if unknown:
        p.error(f"모르는 색지: {', '.join(unknown)}  (가능: {', '.join(CARDS)})")

    fault = args.fault
    if fault == "random":
        import random
        fault = random.Random(args.seed).choice(sorted(FAULTS))
    if fault is not None and fault not in FAULTS:
        p.error(f"모르는 결함: {fault}  (목록: --fault list)")

    panel = LedPanel(shared_resistor=not args.per_channel_resistor)
    world = SimWorld(panel=panel, led_radius_px=args.led_radius)
    if args.led_in_roi:
        world.led_at = (0.5, 0.5)
    world.set_card(CARDS[cards[0]])

    rig = build_rig(fault, policy=args.policy, world=world, seed=args.seed)
    if fault is None and args.policy == "rule":
        rig.policy = ColorRulePolicy()
    policy, actuator = rig.policy, rig.actuator

    save_dir = Path(args.save) if args.save else None
    if save_dir:
        save_dir.mkdir(parents=True, exist_ok=True)

    show = not args.no_preview and sys.stdout.isatty()
    wiring = "채널별 저항" if args.per_channel_resistor else "공통 저항 (실물)"
    print(f"정책 {policy.name}   배선 {wiring}   "
          f"LED {'ROI 안' if args.led_in_roi else 'ROI 밖'}   {args.steps} 스텝")
    if scenario is not None:
        print(f"대본 {scenario.describe()}\n  {scenario.note}")
    if rig.fault is not None:
        print(f"\n이 장비에는 문제가 하나 있다고 신고됐습니다.\n  {rig.briefing()}\n"
              f"  어느 계층인지, 무엇 때문인지 측정으로 밝히십시오.")
    if not show:
        print("(미리보기 꺼짐)")
    print()

    results = []
    health_error: str | None = None
    rig.source._fps = args.fps
    with rig.source as src:
        loop = rig.loop()
        if isinstance(policy, VlmPolicy):
            policy.start()
        for i in range(args.steps):
            if scenario is not None:
                card = scenario.name
                scenario.apply(world, i / (args.fps or 10.0))
            else:
                card = cards[0] if args.still else cards[(i // max(1, args.dwell)) % len(cards)]
                world.set_card(CARDS[card])

            try:
                r = loop.step()
            except FrameHealthError as e:
                health_error = str(e)
                break
            results.append(r)

            if save_dir:
                import cv2
                frame = world.render(i)
                cv2.imwrite(str(save_dir / f"{i:04d}.png"),
                            cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            if show:
                frame = world.render(i)
                sys.stdout.write("\x1b[H\x1b[J" if i else "")
                print(preview(frame))
                print(f"\n색지 {card:8s} → {r.features.describe()}")
                print(f"명령      {r.command.describe()}"
                      f"{'   ← 전송' if r.changed else ''}")
                print(f"LED 발광  {world.emitted()}   "
                      f"(명령 {len(actuator.history)}회, "
                      f"시리얼 {actuator.wire_lines}줄)")
                time.sleep(0.0)
            else:
                print(r.describe())

    if isinstance(policy, VlmPolicy):
        policy.stop()

    if health_error:
        print(f"\n건전성 검사가 프레임을 막았습니다 ({len(results)} 스텝에서 중단)")
        print(f"  {health_error}")
        print("\n장치가 열리고 프레임도 왔다는 것은 작동한다는 증거가 아닙니다.")
        if args.reveal:
            print("\n" + rig.reveal())
        return

    s = summarize(results)
    print(f"\n{len(results)} 스텝 · 평균 {s['total_ms']:.1f}ms "
          f"(촬영 {s['capture_ms']:.1f} + 특징 {s['extract_ms']:.1f} "
          f"+ 판단 {s['decide_ms']:.1f} + 구동 {s['actuate_ms']:.1f})")
    print(f"명령 전송 {len(actuator.history)}회 / {len(results)} 스텝  "
          f"— 시리얼이었다면 {actuator.wire_lines}줄")

    if not args.per_channel_resistor:
        print("\n혼합색을 명령하면 발광이 강한 다이 쪽으로 밀립니다. 공통 저항 하나를"
              "\n셋이 나눠 쓰기 때문이며, 실물도 그랬습니다. 모델의 한계와 실물과의"
              "\n차이는 docs/tech/notes/sim-led-model.md 에 적어 두었습니다.")
    if isinstance(policy, VlmPolicy):
        st = policy.stats
        print(f"VLM  요청 {st['requests']}  성공 {st['ok']}  "
              f"거부 {st['invalid']}  실패 {st['failed']}  판단없음 {st['none']}")
        d = policy.last_decision
        print(f"     마지막 판단 {d.describe() if d else '아직 없음'}")

    if save_dir:
        print(f"프레임 저장: {save_dir}/")

    if args.reveal:
        print("\n" + rig.reveal())
    elif rig.fault is not None:
        print("\n정답은 --reveal 로 확인합니다.")


if __name__ == "__main__":
    main()
