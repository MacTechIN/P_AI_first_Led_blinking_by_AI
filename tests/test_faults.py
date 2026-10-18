"""S-3 시험 — 주입한 결함이 **기록된 증상 그대로** 나오는가.

결함이 실제 증상을 내지 못하면 실습은 수수께끼 놀이가 된다. 여기서 재는 것은
"결함이 켜졌다" 가 아니라 "켜진 결함이 기록과 같은 것을 보여준다" 이다.
"""

from pathlib import Path

import numpy as np
import pytest

from control.commands import LedCommand
from control.features import extract
from control.vlm import VlmPolicy
from perception.health import FrameHealthError
from sim import FAULTS, build_rig

ROOT = Path(__file__).resolve().parent.parent


def commands_in(fault, steps=20, **kw):
    rig = build_rig(fault, seed=1, **kw)
    with rig.source:
        rig.loop().run(steps)
    return len(rig.actuator.history)


def hue_of(rgb):
    import cv2

    return int(cv2.cvtColor(np.uint8([[list(rgb)]]), cv2.COLOR_RGB2HSV)[0, 0, 0])


# --- 등록부 자체 ---


def test_unknown_fault_is_refused():
    with pytest.raises(ValueError, match="모르는 결함"):
        build_rig("자동차고장")


def test_briefing_never_leaks_the_cause():
    """수강생에게 주는 것은 증상뿐이다. 원인을 흘리면 실습이 성립하지 않는다."""
    for name, f in FAULTS.items():
        text = build_rig(name).briefing()
        assert f.symptom in text
        assert f.cause not in text
        assert name not in text


def test_every_fault_points_at_a_record_that_exists():
    """원 기록이 없으면 실습 뒤에 읽을 것이 없다."""
    for f in FAULTS.values():
        assert (ROOT / f.record).exists(), f"{f.name}: {f.record} 가 없다"


# --- 센서 계층 ---


def test_flat_frame_is_stopped_by_the_health_check():
    rig = build_rig("flat-frame")
    with rig.source:
        with pytest.raises(FrameHealthError, match="모든 픽셀"):
            rig.loop().step()


def test_flat_frame_without_the_health_check_just_goes_quiet():
    """검사를 끄면 예외 대신 **침묵**이 온다. 이쪽이 더 위험하다.

    아무 오류도 없이 "물체 없음" 만 계속 나온다. 건전성 검사는 이 침묵을
    메시지로 바꾸는 장치다.
    """
    rig = build_rig("flat-frame")
    rig.source.check_health = False
    with rig.source:
        results = rig.loop().run(5)
    assert all(r.features.color is None for r in results)
    assert all(r.command.mode == "off" for r in results)


def test_autoexposure_cancels_the_led_contribution():
    """LED 를 켜도 측정 밝기가 움직이지 않는다 — 실측에서 +0.02 였다."""
    def delta(fault):
        rig = build_rig(fault, seed=1)
        rig.world.led_at, rig.world.led_radius_px = (0.5, 0.5), 70
        with rig.source as src:
            rig.world.apply(LedCommand("off"))
            off = extract(src.read().image).brightness
            rig.world.apply(LedCommand("on", rgb=(255, 255, 255), level=255))
            return extract(src.read().image).brightness - off

    assert delta(None) > 2.0            # 정상이면 밝아진다
    assert abs(delta("autoexposure")) < 1.0


# --- 특징 계층 ---


def test_stale_roi_reports_nothing_while_the_card_is_obvious():
    """장치는 멀쩡한데 고장난 것처럼 보인다."""
    rig = build_rig("stale-roi", seed=1)
    with rig.source as src:
        obs = src.read()
        assert rig.extractor(obs.image).color is None     # 잘못된 ROI
        assert extract(obs.image).color == "red"          # 같은 프레임, 올바른 ROI


# --- 판단 계층 ---


def test_no_hysteresis_floods_the_wire_on_a_still_scene():
    """ADR-0007 의 조건 그대로 — 정지 장면 20 프레임."""
    normal = commands_in(None)
    flooded = commands_in("no-hysteresis")
    assert normal <= 2
    assert flooded >= normal * 5


# --- 구동 계층 ---


@pytest.mark.parametrize("rgb,expect", [
    ((255, 255, 255), "dark"),      # 기록: 흰색 명령 → 꺼짐
    ((0, 0, 0), "lit"),             # 기록: 0 0 0 → 점등
])
def test_polarity_reproduces_the_recorded_observations(rgb, expect):
    rig = build_rig("polarity")
    rig.world.apply(LedCommand("on", rgb=rgb, level=255))
    emitted = rig.world.emitted(0.0)
    assert (max(emitted) == 0) == (expect == "dark")


def test_polarity_turns_a_red_command_into_green_and_blue():
    """기록: `RGB 255 0 0` → 청록 (R 만 꺼지고 G+B 점등)."""
    rig = build_rig("polarity")
    rig.world.apply(LedCommand("on", rgb=(255, 0, 0), level=255))
    r, g, b = rig.world.emitted(0.0)
    assert r == 0 and (g + b) > 0


# --- 모델 계층 ---


def run_vlm(fault, steps=8):
    rig = build_rig(fault, policy="vlm", seed=1, vlm_latency_ms=1.0)
    with rig.source:
        loop = rig.loop()
        rig.policy.start()
        for _ in range(steps):
            loop.step()
        rig.policy.stop()               # 진행 중인 추론을 끝까지 기다린다
    return rig


def test_a_dead_server_fails_every_request_and_the_fallback_hides_it():
    rig = run_vlm("health-ok-dead")
    st = rig.policy.stats
    assert st["requests"] > 0
    assert st["failed"] == st["requests"]        # 전부 실패 = 전송 계층
    assert rig.policy.last_decision is None
    assert len(rig.actuator.history) > 0         # 그래도 LED 는 움직인다


def test_health_says_ok_even_when_nothing_works():
    """`/health` 가 ok 를 돌려주는 것은 작동의 증거가 아니다."""
    rig = build_rig("health-ok-dead", policy="vlm")
    assert rig.policy.client.health()["status"] == "ok"


def test_contract_drift_fails_some_but_not_all():
    """일부만 실패하는 것이 계약 어긋남의 지문이다."""
    rig = run_vlm("schema-drift", steps=12)
    st = rig.policy.stats
    assert 0 < st["failed"] < st["requests"]


def test_slow_inference_does_not_block_the_control_loop():
    """추론이 3초대여도 decide 는 즉시 돌아온다 (ADR-0008)."""
    rig = build_rig("slow-vlm", policy="vlm", seed=1)
    with rig.source:
        loop = rig.loop()
        rig.policy.start()
        results = loop.run(5)
        rig.policy.stop()
    assert max(r.timings_ms["decide"] for r in results) < 50.0
    assert rig.policy.client.latency_ms > 3000.0
