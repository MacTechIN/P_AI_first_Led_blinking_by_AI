"""VS-2 시험. 합성 소스(µ1.4) 덕분에 카메라와 아두이노 없이 전 경로를 검증한다."""

import numpy as np
import pytest

from control import (
    ColorRulePolicy,
    CommandError,
    ControlLoop,
    LedCommand,
    NullActuator,
    SceneFeatures,
    classify_hue,
    extract,
    summarize,
)
from perception import SyntheticSource, patch, solid

# --- 명령 계약 (ADR-0003 의 호스트 측 절반) ---


def test_command_rejects_out_of_range_interval():
    with pytest.raises(CommandError, match="interval_ms"):
        LedCommand("blink", interval_ms=5)      # 펌웨어 MIN_INTERVAL = 10
    with pytest.raises(CommandError, match="interval_ms"):
        LedCommand("blink", interval_ms=99999)


def test_command_rejects_out_of_range_level():
    with pytest.raises(CommandError, match="level"):
        LedCommand("on", level=256)             # 펌웨어 MAX_LEVEL = 255
    with pytest.raises(CommandError, match="level"):
        LedCommand("on", level=-1)


def test_command_rejects_unknown_mode():
    with pytest.raises(CommandError, match="mode"):
        LedCommand("strobe")


def test_wire_sets_parameters_before_mode():
    """LEVEL/INT 이 BLINK 보다 먼저 가야 첫 점멸부터 올바른 값으로 켜진다."""
    wire = LedCommand("blink", interval_ms=250, level=100).to_wire()
    assert wire == ["LEVEL 100", "INT 250", "BLINK"]
    assert wire.index("LEVEL 100") < wire.index("BLINK")


# --- 특징 추출 (µ2.1) ---


def test_detects_red_patch():
    img = SyntheticSource(patch(fg=(230, 20, 20), bg=(20, 20, 20))).open().read().image
    f = extract(img)
    assert f.color == "red"
    # patch 기본 상자는 화면의 40%, ROI 는 60% 이므로 ROI 대비 (0.4/0.6)^2 = 0.44
    assert 0.40 < f.coverage < 0.50


def test_detects_green_and_blue():
    for rgb, expected in [((20, 220, 20), "green"), ((20, 20, 230), "blue")]:
        img = SyntheticSource(patch(fg=rgb, bg=(20, 20, 20))).open().read().image
        assert extract(img).color == expected


def test_reports_no_object_on_grey_scene():
    """무채색 장면은 물체 없음이어야 한다 — 어두운 곳의 hue 는 노이즈다."""
    img = SyntheticSource(solid((120, 120, 120))).open().read().image
    assert extract(img).color is None


def test_brightness_is_roi_local_not_global():
    """ROI 밖만 밝은 장면에서 밝기가 낮게 나와야 한다.

    전역 평균을 쓰면 이 시험이 깨진다. 자동노출이 전역 밝기를 상쇄하므로
    전역 평균은 조명 판단에 쓸 수 없다 (LED 검출 실측 참조).
    """
    img = np.full((480, 640, 3), 10, dtype=np.uint8)
    img[:, :100] = 250          # 왼쪽 가장자리만 밝게 — ROI(가운데 60%) 바깥
    img[0, 0, 1] = 11           # 평탄 프레임 방지
    assert extract(img).brightness < 40


def test_red_hue_wraparound_is_handled():
    """빨강은 H=0 근처와 179 근처로 갈라진다. 평균을 쓰면 초록으로 오판한다."""
    assert classify_hue(2) == "red"
    assert classify_hue(175) == "red"


def test_centroid_tracks_horizontal_position():
    left = SyntheticSource(patch((230, 20, 20), box=(0.22, 0.4, 0.42, 0.6))).open().read().image
    right = SyntheticSource(patch((230, 20, 20), box=(0.58, 0.4, 0.78, 0.6))).open().read().image
    assert extract(left).centroid_x < extract(right).centroid_x


# --- 정책 (µ2.2) ---


def test_policy_maps_colour_to_blink_rate():
    p = ColorRulePolicy()
    red = p.decide(SceneFeatures("red", 5, 0.5, 200, 120, 0.5))
    green = p.decide(SceneFeatures("green", 60, 0.5, 200, 120, 0.5))
    assert red.mode == "blink" and green.mode == "blink"
    assert red.interval_ms < green.interval_ms, "빨강이 더 빨라야 한다"


def test_policy_turns_off_when_nothing_seen():
    assert ColorRulePolicy().decide(
        SceneFeatures(None, None, 0.0, 0.0, 100, None)
    ).mode == "off"


def test_policy_scales_level_with_coverage():
    p = ColorRulePolicy()
    small = p.decide(SceneFeatures("red", 5, 0.06, 200, 120, 0.5))
    large = p.decide(SceneFeatures("red", 5, 0.60, 200, 120, 0.5))
    assert small.level < large.level
    assert p.decide(SceneFeatures("red", 5, 0.99, 200, 120, 0.5)).level == 255


def test_policy_output_always_satisfies_the_contract():
    """정책이 무엇을 내든 펌웨어 한계를 넘지 않는다."""
    p = ColorRulePolicy()
    for cov in (0.0, 0.05, 0.5, 1.0, 5.0):
        for colour in list(__import__("control").COLOR_RULES) + ["unknown", None]:
            cmd = p.decide(SceneFeatures(colour, 5, cov, 200, 120, 0.5))
            assert 10 <= cmd.interval_ms <= 5000 and 0 <= cmd.level <= 255


# --- 종단 루프 (µ2.3) ---


def test_loop_runs_without_hardware():
    """VS-2 의 합격 조건: 카메라도 아두이노도 없이 종단 경로가 돈다."""
    act = NullActuator()
    loop = ControlLoop(
        SyntheticSource(patch((230, 20, 20))).open(), ColorRulePolicy(), act
    )
    results = loop.run(steps=5)
    assert len(results) == 5
    assert act.last.mode == "blink"


def test_loop_only_actuates_on_change():
    """같은 명령을 반복 전송하면 펌웨어가 점멸 위상을 리셋해 끊겨 보인다."""
    act = NullActuator()
    loop = ControlLoop(
        SyntheticSource(patch((230, 20, 20))).open(), ColorRulePolicy(), act
    )
    loop.run(steps=5)
    assert len(act.history) == 1, "장면이 그대로면 한 번만 보내야 한다"


def test_loop_reacts_when_scene_changes():
    from perception.sources import Painter

    def switching(seq: int) -> np.ndarray:
        rgb = (230, 20, 20) if seq < 2 else (20, 20, 230)
        return patch(fg=rgb, bg=(20, 20, 20))(seq)

    act = NullActuator()
    loop = ControlLoop(SyntheticSource(switching).open(), ColorRulePolicy(), act)
    loop.run(steps=4)
    assert [c.mode for c in act.history] == ["blink", "on"]


def test_timings_cover_every_stage():
    loop = ControlLoop(SyntheticSource().open(), ColorRulePolicy(), NullActuator())
    r = loop.step()
    assert set(r.timings_ms) == {"capture", "extract", "decide", "actuate"}
    assert r.total_ms > 0


def test_summarize_reports_latency_budget():
    loop = ControlLoop(SyntheticSource().open(), ColorRulePolicy(), NullActuator())
    s = summarize(loop.run(steps=5))
    assert {"capture_ms", "extract_ms", "decide_ms", "total_ms", "p95_ms", "fps"} <= set(s)
    assert s["fps"] > 0
