"""VS-4 시험. 합격 판정은 test_adding_a_device_needs_no_code 다."""

import json

import pytest

from control.capability import (
    Call,
    ContractActuator,
    ContractError,
    Registry,
)

SERVO = {
    "id": "servo_arm",
    "kind": "servo",
    "description": "Servo that points at things",
    "transport": {"type": "null"},
    "commands": {
        "point": {
            "description": "Move to an angle",
            "wire": "SERVO {angle}",
            "args": {"angle": {"type": "int", "min": 0, "max": 180}},
        },
        "sweep": {
            "description": "Sweep back and forth",
            "wire": "SWEEP {speed}",
            "args": {"speed": {"type": "enum", "choices": ["slow", "fast"]}},
        },
    },
}


@pytest.fixture
def reg(tmp_path):
    (tmp_path / "servo.json").write_text(json.dumps(SERVO))
    return Registry.load(tmp_path)


# --- µ4.4: 합격 판정 ---


def test_adding_a_device_needs_no_code(tmp_path):
    """**VS-4 의 합격 조건.**

    선언 파일 하나를 놓는 것 외에 파이썬을 한 줄도 쓰지 않았는데
    장치가 스키마에 나타나고, 검증을 통과하고, 전송 문장까지 만들어져야 한다.
    """
    (tmp_path / "gripper.json").write_text(json.dumps({
        "id": "gripper",
        "kind": "gripper",
        "description": "Two-finger gripper",
        "transport": {"type": "null"},
        "commands": {"grip": {
            "description": "Close to a force",
            "wire": "GRIP {force}",
            "args": {"force": {"type": "int", "min": 0, "max": 100}},
        }},
    }))
    registry = Registry.load(tmp_path)

    # 1. 모델이 보는 스키마에 나타난다
    assert any(
        o["properties"]["device"]["enum"] == ["gripper"]
        for o in registry.tool_schema()["oneOf"]
    )
    # 2. 프롬프트 요약에 나타난다
    assert "gripper" in registry.describe() and "grip" in registry.describe()
    # 3. 검증을 통과한다
    call = registry.validate({"device": "gripper", "command": "grip",
                              "args": {"force": 40}})
    assert call == Call("gripper", "grip", {"force": 40})
    # 4. 전송 문장이 만들어지고 실제로 나간다
    act = ContractActuator(registry)
    assert act.apply(call) == ["GRIP 40"]
    assert act.sent == [("gripper", "GRIP 40")]
    # 5. 계약 밖 값은 막힌다
    with pytest.raises(ContractError, match="100 이하"):
        registry.validate({"device": "gripper", "command": "grip",
                           "args": {"force": 500}})


# --- µ4.2 스키마 자동 생성 ---


def test_schema_covers_every_command(reg):
    options = reg.tool_schema()["oneOf"]
    assert {o["properties"]["command"]["enum"][0] for o in options} == {"point", "sweep"}


def test_schema_carries_the_declared_ranges(reg):
    point = next(o for o in reg.tool_schema()["oneOf"]
                 if o["properties"]["command"]["enum"] == ["point"])
    angle = point["properties"]["args"]["properties"]["angle"]
    assert angle == {"type": "integer", "minimum": 0, "maximum": 180}


def test_schema_and_validator_come_from_one_declaration(reg):
    """ADR-0009 의 교훈: 계약을 두 번 적으면 갈라진다. 여기서는 한 번만 적는다."""
    point = next(o for o in reg.tool_schema()["oneOf"]
                 if o["properties"]["command"]["enum"] == ["point"])
    hi = point["properties"]["args"]["properties"]["angle"]["maximum"]
    reg.validate({"device": "servo_arm", "command": "point", "args": {"angle": hi}})
    with pytest.raises(ContractError):
        reg.validate({"device": "servo_arm", "command": "point",
                      "args": {"angle": hi + 1}})


# --- µ4.3 검증 (환각 차단) ---


def test_rejects_unknown_device(reg):
    with pytest.raises(ContractError, match="알 수 없는 장치"):
        reg.validate({"device": "laser_cannon", "command": "fire"})


def test_rejects_unknown_command(reg):
    with pytest.raises(ContractError, match="없는 명령"):
        reg.validate({"device": "servo_arm", "command": "explode"})


def test_rejects_unknown_argument(reg):
    with pytest.raises(ContractError, match="없는 인자"):
        reg.validate({"device": "servo_arm", "command": "point",
                      "args": {"angle": 90, "torque": 9000}})


def test_rejects_missing_argument(reg):
    with pytest.raises(ContractError, match="빠졌다"):
        reg.validate({"device": "servo_arm", "command": "point", "args": {}})


def test_rejects_out_of_range(reg):
    for bad in (-1, 181):
        with pytest.raises(ContractError):
            reg.validate({"device": "servo_arm", "command": "point",
                          "args": {"angle": bad}})


def test_rejects_wrong_type(reg):
    with pytest.raises(ContractError, match="숫자"):
        reg.validate({"device": "servo_arm", "command": "point",
                      "args": {"angle": "ninety"}})


def test_rejects_enum_outside_choices(reg):
    with pytest.raises(ContractError, match="중 하나"):
        reg.validate({"device": "servo_arm", "command": "sweep",
                      "args": {"speed": "ludicrous"}})


def test_bool_is_not_a_number(reg):
    """True 는 파이썬에서 1 이지만 계약상 정수가 아니다."""
    with pytest.raises(ContractError, match="숫자"):
        reg.validate({"device": "servo_arm", "command": "point",
                      "args": {"angle": True}})


def test_defaults_fill_in(tmp_path):
    (tmp_path / "d.json").write_text(json.dumps({
        "id": "d", "kind": "k", "transport": {"type": "null"},
        "commands": {"go": {"wire": "GO {speed}",
                            "args": {"speed": {"type": "int", "min": 0, "max": 9,
                                               "default": 3}}}},
    }))
    r = Registry.load(tmp_path)
    assert r.validate({"device": "d", "command": "go"}).args == {"speed": 3}


# --- 실제 LED 선언 ---


def test_shipped_led_declaration_matches_the_firmware():
    """선언된 범위가 펌웨어 상수와 일치해야 한다 (ADR-0003)."""
    reg = Registry.load()
    blink = reg.devices["led_main"].commands["blink"]
    assert (blink.args["interval_ms"].minimum, blink.args["interval_ms"].maximum) == (10, 5000)
    assert blink.args["level"].maximum == 255
    for ch in "rgb":
        assert reg.devices["led_main"].commands["on"].args[ch].maximum == 255


def test_led_renders_the_wire_protocol_in_order():
    """색·밝기가 모드 전환보다 먼저 나가야 첫 점멸부터 올바르다."""
    reg = Registry.load()
    call = reg.validate({"device": "led_main", "command": "blink",
                         "args": {"r": 255, "g": 0, "b": 0,
                                  "interval_ms": 150, "level": 200}})
    lines = reg.render(call)
    assert lines == ["RGB 255 0 0", "LEVEL 200", "INT 150", "BLINK"]
    assert lines.index("BLINK") == len(lines) - 1


# --- 선언 자체의 오류 ---


def test_declaration_without_wire_is_rejected(tmp_path):
    (tmp_path / "bad.json").write_text(json.dumps({
        "id": "b", "kind": "k", "transport": {"type": "null"},
        "commands": {"go": {"args": {}}},
    }))
    with pytest.raises(ContractError, match="wire"):
        Registry.load(tmp_path)


def test_enum_without_choices_is_rejected(tmp_path):
    (tmp_path / "bad.json").write_text(json.dumps({
        "id": "b", "kind": "k", "transport": {"type": "null"},
        "commands": {"go": {"wire": "GO {m}",
                            "args": {"m": {"type": "enum"}}}},
    }))
    with pytest.raises(ContractError, match="choices"):
        Registry.load(tmp_path)


def test_empty_directory_is_an_error(tmp_path):
    with pytest.raises(ContractError, match="선언이 하나도"):
        Registry.load(tmp_path)


def test_unsupported_transport_is_rejected(tmp_path):
    (tmp_path / "d.json").write_text(json.dumps({
        "id": "d", "kind": "k", "transport": {"type": "carrier-pigeon"},
        "commands": {"go": {"wire": "GO", "args": {}}},
    }))
    r = Registry.load(tmp_path)
    with pytest.raises(ContractError, match="전송 방식"):
        ContractActuator(r).apply(r.validate({"device": "d", "command": "go"}))
