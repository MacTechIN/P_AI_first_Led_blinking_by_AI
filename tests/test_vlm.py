"""VS-3 시험. 실제 VLM 서버 없이 정책 로직 전부를 검증한다."""

import json
import threading
import time

import numpy as np
import pytest

from control import (
    ColorRulePolicy,
    ControlLoop,
    LedCommand,
    MirrorColorPolicy,
    NullActuator,
    SceneFeatures,
    VlmClient,
    VlmError,
    VlmPolicy,
    to_command,
    validate,
)
from perception import SyntheticSource, patch


def fake_opener(payload: dict, *, delay: float = 0.0, fail: bool = False):
    """VlmClient 에 끼울 가짜 전송. 서버 없이 응답을 만든다."""

    def opener(req, timeout):
        if delay:
            time.sleep(delay)
        if fail:
            raise OSError("연결 실패")
        return json.dumps(
            {"choices": [{"message": {"content": json.dumps(payload)}}]}
        ).encode()

    return opener


def client_returning(payload, **kw):
    return VlmClient(opener=fake_opener(payload, **kw))


# --- 검증기 (µ3.5) ---


def test_validate_accepts_well_formed():
    out = validate({"action": "on", "colour": "green", "reason": "a green cup"})
    assert out["action"] == "on" and out["colour"] == "green"


def test_validate_rejects_unknown_action():
    with pytest.raises(VlmError, match="action"):
        validate({"action": "strobe", "colour": "red", "reason": ""})


def test_validate_rejects_colour_outside_the_contract():
    """모델이 없는 색을 지어내면 막는다 — 환각 차단."""
    with pytest.raises(VlmError, match="colour"):
        validate({"action": "on", "colour": "chartreuse", "reason": ""})


def test_validate_requires_colour_when_lighting():
    with pytest.raises(VlmError, match="colour"):
        validate({"action": "blink", "reason": "warning"})


def test_validate_allows_missing_colour_for_off_and_none():
    assert validate({"action": "off", "reason": "empty"})["colour"] is None
    assert validate({"action": "none", "reason": "too dark"})["colour"] is None


def test_validate_rejects_non_object():
    with pytest.raises(VlmError, match="객체"):
        validate(["on", "red"])


def test_reason_is_truncated_not_trusted():
    long = "x" * 500
    assert len(validate({"action": "off", "reason": long})["reason"]) == 80


# --- 명령 변환 ---


def test_none_yields_no_command_so_the_last_one_holds():
    """'모르겠다' 와 '꺼라' 는 다르다."""
    assert to_command({"action": "none", "colour": None, "reason": ""}) is None


def test_off_yields_an_off_command():
    assert to_command({"action": "off", "colour": None, "reason": ""}).mode == "off"


def test_colour_maps_to_the_right_channel():
    for colour, ch in [("red", 0), ("green", 1), ("blue", 2)]:
        cmd = to_command({"action": "on", "colour": colour, "reason": ""})
        assert cmd.rgb[ch] == max(cmd.rgb)


def test_red_blink_is_within_the_firmware_contract():
    cmd = to_command({"action": "blink", "colour": "red", "reason": "warning"})
    assert 10 <= cmd.interval_ms <= 5000 and 0 <= cmd.level <= 255


# --- 클라이언트 ---


def test_client_raises_on_transport_failure():
    c = VlmClient(opener=fake_opener({}, fail=True))
    with pytest.raises(VlmError, match="호출 실패"):
        c.ask(np.zeros((64, 64, 3), dtype=np.uint8))


def test_client_raises_on_non_json_content():
    def opener(req, timeout):
        return json.dumps({"choices": [{"message": {"content": "sure thing!"}}]}).encode()

    with pytest.raises(VlmError, match="JSON"):
        VlmClient(opener=opener).ask(np.zeros((64, 64, 3), dtype=np.uint8))


# --- 비동기 정책 (ADR-0008) ---


def _features(colour="green", hue=60):
    from control import hue_to_rgb

    return SceneFeatures(colour, hue, 0.4, 200, 120, 0.5, hue_to_rgb(hue))


def test_decide_never_blocks_even_when_inference_is_slow():
    """이게 VS-3 의 핵심 요구다. 추론이 느려도 루프는 멈추지 않는다."""
    slow = client_returning({"action": "on", "colour": "red", "reason": "x"}, delay=2.0)
    with VlmPolicy(slow, min_interval_s=0.0) as p:
        src = SyntheticSource(patch((0, 220, 0))).open()
        obs = src.read()
        t0 = time.perf_counter()
        for _ in range(5):
            p.decide(_features(), obs)
        elapsed = (time.perf_counter() - t0) * 1000
    assert elapsed < 200, f"decide 가 블로킹했다: {elapsed:.0f}ms"


def test_falls_back_until_the_first_decision_arrives():
    """판단이 오기 전에도 LED 는 켜져 있어야 한다."""
    p = VlmPolicy(client_returning({"action": "off", "colour": None, "reason": ""}),
                  fallback=MirrorColorPolicy(alert=None))
    cmd = p.decide(_features("green", 60), None)     # 작업 스레드 미가동
    assert cmd.mode == "on", "폴백이 답해야 한다"


def test_vlm_decision_supersedes_the_fallback():
    payload = {"action": "blink", "colour": "red", "reason": "warning object"}
    with VlmPolicy(client_returning(payload), fallback=ColorRulePolicy(),
                   min_interval_s=0.0) as p:
        obs = SyntheticSource(patch((0, 220, 0))).open().read()
        deadline = time.time() + 5
        while time.time() < deadline:
            cmd = p.decide(_features("green", 60), obs)
            if p.last_decision is not None:
                break
            time.sleep(0.02)
    assert p.last_decision is not None, "판단이 도착하지 않았다"
    assert cmd.mode == "blink" and cmd.rgb[0] == max(cmd.rgb)


def test_transport_failure_holds_the_previous_command():
    """VLM 이 죽어도 LED 가 꺼지지 않는다."""
    p = VlmPolicy(VlmClient(opener=fake_opener({}, fail=True)), min_interval_s=0.0)
    p._command = LedCommand("on", rgb=(0, 255, 0), level=100)
    with p:
        obs = SyntheticSource().open().read()
        deadline = time.time() + 3
        while p.stats["failed"] == 0 and time.time() < deadline:
            p.decide(_features(), obs)
            time.sleep(0.02)
    assert p.stats["failed"] > 0
    assert p.decide(_features(), None).rgb == (0, 255, 0), "직전 명령이 유지돼야"


def test_none_action_holds_rather_than_turning_off():
    p = VlmPolicy(client_returning({"action": "none", "colour": None, "reason": "dark"}),
                  min_interval_s=0.0)
    p._command = LedCommand("on", rgb=(255, 0, 0), level=120)
    with p:
        obs = SyntheticSource().open().read()
        deadline = time.time() + 3
        while p.stats["none"] == 0 and time.time() < deadline:
            p.decide(_features(), obs)
            time.sleep(0.02)
    assert p.stats["none"] > 0
    assert p.decide(_features(), None).mode == "on", "'모르겠다' 가 LED 를 끄면 안 된다"


def test_only_the_latest_observation_is_processed():
    """추론이 관측보다 느리므로 밀린 프레임은 버려야 한다 (ADR-0008)."""
    p = VlmPolicy(client_returning({"action": "off", "colour": None, "reason": ""}))
    src = SyntheticSource().open()
    a, b = src.read(), src.read()
    p.decide(_features(), a)
    p.decide(_features(), b)
    assert p._pending.seq == b.seq


def test_works_inside_the_control_loop_without_stalling_it():
    slow = client_returning({"action": "on", "colour": "blue", "reason": "x"}, delay=1.5)
    act = NullActuator()
    with VlmPolicy(slow, fallback=ColorRulePolicy(), min_interval_s=0.0) as p:
        loop = ControlLoop(SyntheticSource(patch((220, 20, 20))).open(), p, act)
        results = loop.run(steps=10)
    assert len(results) == 10
    assert max(r.timings_ms["decide"] for r in results) < 50, "판단이 루프를 막았다"


def test_schema_and_validator_agree():
    """스키마가 허용하는 것을 검증기가 막으면 전 요청이 실패한다.

    실제로 그렇게 됐다: colour 를 선택으로 두자 모델이 blink 를 내면서 생략했고,
    검증기가 5회 중 4회를 거부했다. 계약의 양쪽이 어긋나지 않게 고정한다.
    """
    from control import RESPONSE_SCHEMA

    required = set(RESPONSE_SCHEMA["required"])
    assert "colour" in required, "검증기가 on/blink 에서 colour 를 요구한다"
    assert "action" in required


def test_colour_is_ignored_for_off_and_none():
    """항상 보내게 했으므로, off/none 에서 값이 와도 무시해야 한다."""
    assert to_command(validate(
        {"action": "off", "colour": "red", "reason": "empty"})).mode == "off"
    assert to_command(validate(
        {"action": "none", "colour": "red", "reason": "dark"})) is None
