#!/usr/bin/env python3
"""P-AI 시뮬레이터 — 학생용 실행기. **네트워크 없이 돕니다.**

    python3 START.py          점검하고 무엇을 할 수 있는지 보여줍니다
    python3 START.py 1        1단계 — 루프가 닫혀 있다
    python3 START.py 2        2단계 — 환경이 변하면 무너진다
    python3 START.py 3        3단계 — 대본이 곧 골든셋
    python3 START.py 4 17     4단계 — 결함 진단 (17 은 강사가 주는 팀 번호)

막히면 화면에 나오는 대로 하시면 됩니다.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable or "python3"
WINDOWS = sys.platform == "win32"


def say(*lines):
    for line in lines:
        print(line)
    sys.stdout.flush()


def check_python():
    if sys.version_info < (3, 10):
        say(f"✕ 파이썬이 너무 낮습니다: {sys.version.split()[0]}",
            "  3.10 이상이 필요합니다. 강사에게 알려 주세요.")
        return False
    return True


def cmd_name() -> str:
    """안내문에 쓸 명령 이름. 윈도우는 보통 `python` 이다."""
    return "python" if WINDOWS else "python3"


def ensure_numpy():
    try:
        import numpy  # noqa: F401
        return True
    except ImportError:
        pass

    say("· numpy 가 없어 USB 안의 것으로 설치합니다 (인터넷 쓰지 않습니다)")
    wheels = ROOT / "wheels"
    if not wheels.is_dir():
        say("✕ wheels 폴더가 없습니다. USB 에서 폴더 전체를 복사했는지 보세요.")
        return False
    cmd = [PY, "-m", "pip", "install", "--no-index",
           "--find-links", str(wheels), "numpy"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        say("  설치했습니다.")
        return True

    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    have = sorted({w.name.split("-")[2] for w in wheels.glob("*.whl")
                   if len(w.name.split("-")) > 2})
    say("✕ numpy 를 설치하지 못했습니다.",
        f"  이 PC: 파이썬 {sys.version_info.major}.{sys.version_info.minor}"
        f" ({tag}) · {sys.platform}",
        f"  USB 에 있는 것: {', '.join(have) or '(없음)'}",
        "",
        "  이 두 줄을 강사에게 그대로 보여 주세요.",
        "  맞는 파일이 USB 에 없다는 뜻이고, 강사가 받아 두면 됩니다.",
        "", (r.stderr or r.stdout)[-300:])
    return False


def selfcheck():
    """시뮬레이터가 실제로 도는지 한 번 돌려 본다."""
    sys.path.insert(0, str(ROOT))
    from control.loop import ControlLoop
    from control.policy import MirrorColorPolicy
    from sim import SimActuator, SimSource, SimWorld
    from sim.scenario import load_all

    world = SimWorld(clock=lambda: 0.0)
    with SimSource(world) as src:
        loop = ControlLoop(src, MirrorColorPolicy(), SimActuator(world))
        result = loop.run(3)[-1]
    names = list(load_all())
    import control.colour as colour

    say(f"· 루프 동작: {result.features.describe()}",
        f"· 장면 대본 {len(names)}개: {', '.join(names)}",
        f"· OpenCV: {'있음 (빠름)' if colour.HAVE_CV2 else '없음 — numpy 로 대체합니다'}")
    return True


def run(args):
    script = ROOT / "host" / args[0]
    # 하위 프로세스가 바로 쓰기 시작하므로, 우리 안내문을 먼저 내보낸다.
    # 비우지 않으면 안내가 결과 **뒤에** 찍힌다 — 파이프로 넘길 때 실제로 그랬다.
    sys.stdout.flush()
    subprocess.run([PY, str(script), *args[1:]])


MENU = {
    "1": ("루프가 닫혀 있다", ["sim_demo.py", "--scenario", "basics"]),
    "2": ("환경이 변하면 무너진다", ["sim_demo.py", "--scenario", "dusk"]),
    "3": ("대본이 곧 골든셋", ["scenario_check.py"]),
}


def main():
    say("", "P-AI 시뮬레이터 — 장비 없이 제어 루프를 돌립니다", "=" * 46)
    if not check_python() or not ensure_numpy():
        return 1
    selfcheck()

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg in MENU:
        title, cmd = MENU[arg]
        say("", f"── {arg}단계 · {title} ──", "")
        run(cmd)
        return 0
    if arg == "4":
        seed = sys.argv[2] if len(sys.argv) > 2 else "1"
        say("", "── 4단계 · 결함 진단 ──",
            "이 장비에는 문제가 하나 있습니다. 증상만 보고 원인을 찾으세요.",
            f"정답은 `{cmd_name()} START.py 4 {seed} --reveal` 로 봅니다.", "")
        extra = sys.argv[3:]
        run(["sim_demo.py", "--fault", "random", "--seed", seed,
             "--steps", "60", *extra])
        return 0

    c = cmd_name()
    say("", "준비됐습니다. 아래 순서대로 해 보세요.", "",
        f"  {c} START.py 1      루프가 닫혀 있다 (5분)",
        f"  {c} START.py 2      환경이 변하면 무너진다 (5분)",
        f"  {c} START.py 3      대본이 곧 골든셋 (5분)",
        f"  {c} START.py 4 <팀번호>   결함 진단 (10분)", "",
        "자세한 설명: MANUAL.md    실습서: docs/08-fault-clinic.md", "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
