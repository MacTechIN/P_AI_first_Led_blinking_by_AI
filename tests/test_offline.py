"""학생 노트북에서 도는가 — **OpenCV 없이, 저장소 밖에서.**

교실에 네트워크가 없으므로 `pip install` 로 고칠 수 없다. 그래서 "돌 것이다"
가 아니라 **돌려 봐서** 확인한다. cv2 를 막은 하위 프로세스를 띄우는 이유는
막는 일이 전역 상태를 건드려서, 같은 프로세스 안에서 하면 다른 시험에 샌다.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def run_without_cv2(code: str, cwd: Path, tmp_path: Path):
    """cv2 임포트가 실패하는 환경에서 코드를 돌린다."""
    stub = tmp_path / "nocv2"
    stub.mkdir(exist_ok=True)
    (stub / "cv2.py").write_text('raise ImportError("cv2 없음 (학생 노트북)")\n')
    env = {"PYTHONPATH": f"{stub}:{ROOT}", "PATH": "/usr/bin:/bin",
           "HOME": str(tmp_path)}
    return subprocess.run([sys.executable, "-c", textwrap.dedent(code)],
                          cwd=cwd, env=env, capture_output=True, text=True)


def test_the_simulator_runs_with_no_opencv(tmp_path):
    r = run_without_cv2('''
        import control.colour as colour
        assert not colour.HAVE_CV2, "cv2 가 막히지 않았다"
        from control.loop import ControlLoop
        from control.policy import MirrorColorPolicy
        from sim import SimActuator, SimSource, SimWorld
        w = SimWorld(clock=lambda: 0.0)
        with SimSource(w) as s:
            r = ControlLoop(s, MirrorColorPolicy(), SimActuator(w)).run(3)[-1]
        assert r.features.color == "red", r.features.describe()
        print("OK")
    ''', ROOT, tmp_path)
    assert "OK" in r.stdout, r.stderr[-800:]


def test_the_scenarios_score_the_same_without_opencv(tmp_path):
    """학생과 강사가 다른 점수를 보면 실습이 성립하지 않는다."""
    r = run_without_cv2('''
        import sys
        sys.path.insert(0, "host")
        from scenario_check import play
        from sim.scenario import load_all
        total = [0, 0]
        for s in load_all().values():
            p, f = play(s, verbose=False, fps=5)
            total[0] += p; total[1] += f
        print("SCORE", total[0], total[1])
    ''', ROOT, tmp_path)
    assert "SCORE 9 0" in r.stdout, r.stdout + r.stderr[-800:]


def test_data_is_found_from_any_directory(tmp_path):
    """학생은 자기 홈에서 친다. 현재 디렉터리 기준이면 '대본이 없다' 로 끝난다."""
    r = run_without_cv2('''
        from sim.scenario import load_all
        from sim.replay import Tape
        from sim.paths import TAPES
        assert set(load_all()) >= {"basics", "dusk", "sweep"}
        assert Tape.load(f"{TAPES}/basics.json").entries
        print("OK")
    ''', tmp_path, tmp_path)
    assert "OK" in r.stdout, r.stderr[-800:]


def test_the_student_scripts_do_not_need_the_instructor_only_modules(tmp_path):
    """꾸러미에는 실물 장비용 스크립트가 빠진다. 그걸 임포트하면 깨진다."""
    for script in ("sim_demo.py", "scenario_check.py", "leaderboard.py"):
        text = (ROOT / "host" / script).read_text()
        assert "from rig_worker" not in text, f"{script} 가 rig_worker 를 쓴다"
        assert "import rig_worker" not in text


@pytest.mark.parametrize("module", ["gi", "serial"])
def test_hardware_only_imports_stay_lazy(module):
    """`gi`(젯슨 카메라)·`serial`(아두이노) 은 학생 노트북에 없다."""
    for pkg in ("sim", "control", "perception"):
        for path in (ROOT / pkg).rglob("*.py"):
            for line in path.read_text().splitlines():
                stripped = line.strip()
                if stripped.startswith((f"import {module}", f"from {module}")):
                    assert line.startswith(" "), f"{path.name}: 최상위 임포트 — {stripped}"


# --- 학생 매뉴얼 ---


def test_the_manual_only_uses_commands_that_exist():
    """매뉴얼이 없는 스크립트를 시키면 학생이 거기서 멈춘다."""
    manual = (ROOT / "docs" / "labs" / "STUDENT.md").read_text()
    import re

    for script in set(re.findall(r"python3? (host/[\w./]+\.py)", manual)):
        assert (ROOT / script).is_file(), f"매뉴얼이 없는 파일을 시킨다: {script}"


def test_the_manual_and_the_bundle_agree_on_the_entry_point():
    manual = (ROOT / "docs" / "labs" / "STUDENT.md").read_text()
    assert "START.py" in manual
    assert (ROOT / "tools" / "START.py").is_file()
    assert (ROOT / "tools" / "START.bat").is_file()


def test_the_bundle_ships_the_manual_and_the_windows_launcher():
    """윈도우 사용자가 터미널을 몰라도 시작할 수 있어야 한다."""
    maker = (ROOT / "tools" / "make_bundle.py").read_text()
    assert "STUDENT.md" in maker and "MANUAL.md" in maker
    assert "START.bat" in maker


def test_the_manual_states_the_measured_step_counts():
    """화면에 나올 숫자를 적어 두면 학생이 '맞게 돌고 있나' 를 스스로 안다.

    288 은 24초 × 12fps 다. 처음에 240 으로 적었다가 실제와 달랐다.
    """
    manual = (ROOT / "docs" / "labs" / "STUDENT.md").read_text()
    assert "288 스텝" in manual
    assert "240 스텝" not in manual
