"""실습서에 적힌 예제가 실제로 동작하는지 고정한다.

교재는 재현되지 않으면 무의미하다. 코드가 바뀌었는데 실습서가 그대로면
학습자는 첫 단계에서 막히고, 그것이 교재 신뢰를 무너뜨린다.

여기 있는 것은 `docs/labs/*.md` 에 **그대로 적혀 있는** 예제들이다.
하드웨어가 필요한 예제는 제외했다 — 실습서 본문의 예상 출력이 그 역할을 한다.
"""

import json

import numpy as np
import pytest

from control import classify_hue, extract
from control.capability import ContractActuator, ContractError, Registry
from perception import FrameHealthError, assert_frame_sane, open_source
from perception import SyntheticSource, patch


def _copy_capabilities(dst):
    from pathlib import Path

    for f in Path("capabilities").glob("*.json"):
        (dst / f.name).write_text(f.read_text())


# --- 모듈 2 (labs/03-perception.md) ---


def test_lab03_synthetic_source_describe():
    with open_source("synthetic") as src:
        assert src.read().describe()["size"] == "640x480"


def test_lab03_flat_frame_is_caught():
    with pytest.raises(FrameHealthError, match="constant frame"):
        assert_frame_sane(np.full((480, 640, 3), 16, dtype=np.uint8))


def test_lab03_dark_but_real_scene_passes():
    rng = np.random.default_rng(1)
    dark = np.clip(rng.normal(8, 3, (240, 320, 3)), 0, 255).astype(np.uint8)
    assert_frame_sane(dark)


# --- 모듈 3 (labs/04-rule-loop.md) ---


def test_lab04_extract_finds_red():
    img = SyntheticSource(patch(fg=(230, 20, 20))).open().read().image
    assert extract(img).color == "red"


def test_lab04_hue_wraparound_example():
    assert classify_hue(2) == "red" and classify_hue(175) == "red"


# --- 모듈 5 (labs/06-capability-contract.md) ---


def test_lab06_led_wire_rendering_matches_the_guide():
    reg = Registry.load()
    call = reg.validate({"device": "led_main", "command": "on",
                         "args": {"r": 255, "g": 0, "b": 0, "level": 200}})
    assert reg.render(call) == ["RGB 255 0 0", "LEVEL 200", "ON"]


def test_lab06_buzzer_can_be_added_with_no_code(tmp_path):
    """실습서의 buzzer 예제. 스키마 옵션 수까지 본문과 일치해야 한다."""
    _copy_capabilities(tmp_path)
    (tmp_path / "buzzer.json").write_text(json.dumps({
        "id": "buzzer", "kind": "buzzer", "description": "Piezo buzzer",
        "status": "planned", "transport": {"type": "null"},
        "commands": {"beep": {
            "description": "Beep at a frequency for a duration",
            "wire": "BEEP {hz} {ms}",
            "args": {"hz": {"type": "int", "min": 100, "max": 5000},
                     "ms": {"type": "int", "min": 10, "max": 2000, "default": 200}},
        }},
    }))
    reg = Registry.load(tmp_path)
    assert len(reg.tool_schema()["oneOf"]) == 6, "실습서가 6옵션이라고 적고 있다"
    call = reg.validate({"device": "buzzer", "command": "beep", "args": {"hz": 1000}})
    assert ContractActuator(reg).apply(call) == ["BEEP 1000 200"]


def test_lab06_planned_device_with_real_transport_is_refused(tmp_path):
    (tmp_path / "ghost.json").write_text(json.dumps({
        "id": "ghost", "kind": "servo", "status": "planned",
        "transport": {"type": "serial", "port": "/dev/ttyACM0"},
        "commands": {"go": {"wire": "GO", "args": {}}},
    }))
    with pytest.raises(ContractError):
        Registry.load(tmp_path)


# --- 실습서 자체의 정합성 ---


def test_every_module_has_a_lab_guide():
    from pathlib import Path

    labs = {p.name for p in Path("docs/labs").glob("*.md")}
    expected = {"00-setup.md", "01-hardware-truth.md", "02-actuator-timing.md",
                "03-perception.md", "04-rule-loop.md", "05-ondevice-ai.md",
                "06-capability-contract.md"}
    assert expected <= labs


def test_curriculum_links_resolve():
    """커리큘럼이 가리키는 실습서가 실제로 존재해야 한다."""
    import re
    from pathlib import Path

    text = Path("docs/curriculum.md").read_text()
    for link in re.findall(r"\]\((labs/[^)]+)\)", text):
        assert (Path("docs") / link).exists(), f"끊긴 링크: {link}"


# --- 강사용 해설서 정합성 ---


def _exercise_count(path):
    import re

    text = path.read_text()
    if "## 연습 문제" not in text:
        return 0
    block = text.split("## 연습 문제")[1].split("## 교훈")[0]
    return len(re.findall(r"^\d+\. ", block, re.M))


def test_every_exercise_has_an_answer():
    """해답 없는 문제가 남으면 강사가 수업 중에 발견한다. 여기서 잡는다."""
    import re
    from pathlib import Path

    labs = sorted(Path("docs/labs").glob("0[1-6]*.md"))
    asked = sum(_exercise_count(f) for f in labs)
    answered = len(re.findall(
        r"^\*\*\d+\. ", Path("docs/labs/INSTRUCTOR.md").read_text(), re.M))
    assert asked > 0
    assert answered == asked, f"문제 {asked}개, 해답 {answered}개"


def test_instructor_guide_covers_every_module():
    from pathlib import Path

    text = Path("docs/labs/INSTRUCTOR.md").read_text()
    for module in ("모듈 0", "모듈 1", "모듈 2", "모듈 3", "모듈 4", "모듈 5"):
        assert f"### {module}" in text, f"{module} 해설이 없다"


def test_instructor_guide_references_resolve():
    """해설서가 가리키는 원자료가 실제로 존재해야 한다."""
    import re
    from pathlib import Path

    text = Path("docs/labs/INSTRUCTOR.md").read_text()
    for ref in re.findall(r"`(docs/tech/notes/[\w-]+\.md)`", text):
        assert Path(ref).exists(), f"없는 문서: {ref}"
