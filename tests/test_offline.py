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
    (stub / "cv2.py").write_text(
        'raise ImportError("cv2 없음")\n', encoding="utf-8")
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
        text = (ROOT / "host" / script).read_text(encoding="utf-8")
        assert "from rig_worker" not in text, f"{script} 가 rig_worker 를 쓴다"
        assert "import rig_worker" not in text


@pytest.mark.parametrize("module", ["gi", "serial"])
def test_hardware_only_imports_stay_lazy(module):
    """`gi`(젯슨 카메라)·`serial`(아두이노) 은 학생 노트북에 없다."""
    for pkg in ("sim", "control", "perception"):
        for path in (ROOT / pkg).rglob("*.py"):
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith((f"import {module}", f"from {module}")):
                    assert line.startswith(" "), f"{path.name}: 최상위 임포트 — {stripped}"


# --- 학생 매뉴얼 ---


def test_the_manual_only_uses_commands_that_exist():
    """매뉴얼이 없는 스크립트를 시키면 학생이 거기서 멈춘다."""
    manual = (ROOT / "docs" / "labs" / "STUDENT.md").read_text(encoding="utf-8")
    import re

    for script in set(re.findall(r"python3? (host/[\w./]+\.py)", manual)):
        assert (ROOT / script).is_file(), f"매뉴얼이 없는 파일을 시킨다: {script}"


def test_the_manual_and_the_bundle_agree_on_the_entry_point():
    manual = (ROOT / "docs" / "labs" / "STUDENT.md").read_text(encoding="utf-8")
    assert "START.py" in manual
    assert (ROOT / "tools" / "START.py").is_file()
    assert (ROOT / "tools" / "START.bat").is_file()


def test_the_bundle_ships_the_manual_and_the_windows_launcher():
    """윈도우 사용자가 터미널을 몰라도 시작할 수 있어야 한다."""
    maker = (ROOT / "tools" / "make_bundle.py").read_text(encoding="utf-8")
    assert "STUDENT.md" in maker and "MANUAL.md" in maker
    assert "START.bat" in maker


def test_the_manual_states_the_measured_step_counts():
    """화면에 나올 숫자를 적어 두면 학생이 '맞게 돌고 있나' 를 스스로 안다.

    288 은 24초 × 12fps 다. 처음에 240 으로 적었다가 실제와 달랐다.
    """
    manual = (ROOT / "docs" / "labs" / "STUDENT.md").read_text(encoding="utf-8")
    assert "288 스텝" in manual
    assert "240 스텝" not in manual


# --- 윈도우 실행기 ---
#
# 이 보드에서는 윈도우를 돌릴 수 없다. 그래서 **형식만** 고정한다 —
# 실제 동작은 윈도우 PC 에서 확인해야 하고, 한 번 깨진 적이 있다.


def test_the_batch_file_is_ascii_only():
    """cmd.exe 는 .bat 을 OEM 코드페이지로 읽는다.

    UTF-8 한글을 넣었다가 학생 PC 에서 `?뚯씠?ъ씠` 로 깨졌고, 깨진 바이트가
    명령 해석까지 망가뜨렸다. 한글 안내는 전부 START.py 가 맡는다.
    """
    raw = (ROOT / "tools" / "START.bat").read_bytes()
    raw.decode("ascii")          # 실패하면 여기서 터진다


def test_the_batch_file_uses_crlf():
    """LF 만 있으면 cmd.exe 가 줄 첫 글자를 먹는다 — `echo.` 이 `cho.` 가 됐다."""
    raw = (ROOT / "tools" / "START.bat").read_bytes()
    assert raw.count(b"\r\n") > 10
    assert raw.count(b"\n") == raw.count(b"\r\n"), "LF 단독 줄이 섞여 있다"


def test_the_batch_file_avoids_errorlevel_inside_parentheses():
    """`if %errorlevel%` 를 괄호 블록 안에 쓰면 구문 분석 시점에 펼쳐져 늘 같은 값이다."""
    text = (ROOT / "tools" / "START.bat").read_text(encoding="utf-8")
    assert "%errorlevel%" not in text
    assert "if not errorlevel 1" in text


def test_the_batch_file_does_not_force_python_io_encoding():
    """`PYTHONIOENCODING` 은 윈도우 콘솔 전용 출력 경로를 **끈다.**

    파이썬은 진짜 콘솔에 쓸 때 WriteConsoleW 를 써서 코드페이지와 무관하게
    유니코드를 바르게 내보낸다. 이 변수를 주면 그 경로 대신 바이트를
    코드페이지로 변환하게 되고, 학생 PC 에서 한글이 `?쒕??젅?댄꽣` 로 깨졌다.
    """
    # 주석(REM)에는 왜 쓰지 않는지가 적혀 있다. **명령 줄만** 본다 —
    # 처음에 전체 본문을 검사했다가 제 주석에 걸려 실패했다.
    lines = [ln.strip() for ln in (ROOT / "tools" / "START.bat").read_text(encoding="utf-8").splitlines()]
    commands = [ln for ln in lines if ln and not ln.upper().startswith("REM")]
    body = "\n".join(commands)
    assert "PYTHONIOENCODING" not in body
    assert "chcp" not in body          # 콘솔 코드페이지도 건드리지 않는다


def test_a_diagnostic_exists_for_encoding_reports():
    """깨짐 신고를 받으면 추측하지 말고 이것부터 돌리게 한다."""
    diag = ROOT / "tools" / "DIAG.bat"
    assert diag.is_file()
    raw = diag.read_bytes()
    raw.decode("ascii")
    assert raw.count(b"\n") == raw.count(b"\r\n")


def test_gitattributes_pins_the_line_endings():
    """고쳐 놓아도 git 이 LF 로 되돌리면 같은 일이 반복된다."""
    assert "*.bat text eol=crlf" in (ROOT / ".gitattributes").read_text(encoding="utf-8")


def test_every_text_file_is_read_and_written_as_utf8():
    """인코딩을 적지 않으면 파이썬은 **그 PC의 지역 인코딩**을 쓴다.

    한국어 윈도우는 cp949 다. 우리 파일은 전부 UTF-8 이라, 학생이 1단계를
    누르는 순간 `'cp949' codec can't decode byte 0x84` 로 멈췄다. 리눅스에서는
    기본이 UTF-8 이라 여기서는 영원히 드러나지 않는다 — 그래서 시험으로 막는다.
    """
    import ast

    bad = []
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in {".venv", "__pycache__", "dist", "node_modules"}
               for part in path.parts):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name) else None)
            if name not in ("read_text", "write_text", "open"):
                continue
            if "encoding" in {kw.arg for kw in node.keywords}:
                continue
            if name == "open":
                if isinstance(func, ast.Attribute) and not node.args and not node.keywords:
                    continue                      # FrameSource.open() 같은 자체 메서드
                if node.args[1:]:
                    mode = node.args[1]
                    if isinstance(mode, ast.Constant) and "b" in str(mode.value):
                        continue                  # 바이너리는 해당 없음
                elif isinstance(func, ast.Name) and not node.args:
                    continue
            bad.append(f"{path.relative_to(ROOT)}:{node.lineno} {name}()")

    assert not bad, "encoding=\"utf-8\" 이 빠졌다:\n  " + "\n  ".join(bad)
