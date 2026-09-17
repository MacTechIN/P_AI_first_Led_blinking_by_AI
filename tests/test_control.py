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
    """RGB/LEVEL/INT 이 BLINK 보다 먼저 가야 첫 점멸부터 올바른 색·밝기로 켜진다."""
    wire = LedCommand("blink", rgb=(1, 2, 3), interval_ms=250, level=100).to_wire()
    assert wire == ["RGB 1 2 3", "LEVEL 100", "INT 250", "BLINK"]
    assert wire.index("BLINK") == len(wire) - 1


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


# --- RGB 확장: 정의서의 "동일 색 표시" ---


def test_command_rejects_bad_rgb():
    from control import LedCommand as C

    with pytest.raises(CommandError, match="0~255"):
        C("on", rgb=(256, 0, 0))
    with pytest.raises(CommandError, match="0~255"):
        C("on", rgb=(0, -1, 0))
    with pytest.raises(CommandError, match="3개"):
        C("on", rgb=(0, 0))


def test_wire_sets_colour_before_mode():
    wire = LedCommand("on", rgb=(10, 20, 30), level=200).to_wire()
    assert wire == ["RGB 10 20 30", "LEVEL 200", "ON"]
    assert wire.index("RGB 10 20 30") < wire.index("ON")


def test_hue_to_rgb_is_fully_saturated():
    """어두운 물체를 봐도 LED 는 선명한 색을 내야 한다."""
    from control import hue_to_rgb

    for hue, channel in [(0, 0), (60, 1), (120, 2)]:
        rgb = hue_to_rgb(hue)
        assert rgb[channel] == 255
        assert min(rgb) == 0


def test_features_carry_display_rgb():
    img = SyntheticSource(patch(fg=(180, 30, 30), bg=(20, 20, 20))).open().read().image
    f = extract(img)
    assert f.rgb is not None
    assert f.rgb[0] > f.rgb[1] and f.rgb[0] > f.rgb[2], "빨강 물체면 빨강이 우세"


def test_mirror_policy_shows_the_colour_it_sees():
    from control import MirrorColorPolicy

    p = MirrorColorPolicy(alert=None)
    for rgb_in, channel in [((255, 0, 0), 0), ((0, 255, 0), 1), ((0, 0, 255), 2)]:
        img = SyntheticSource(patch(fg=rgb_in, bg=(20, 20, 20))).open().read().image
        cmd = p.decide(extract(img))
        assert cmd.mode == "on"
        assert cmd.rgb[channel] == max(cmd.rgb), f"{rgb_in} 를 보면 같은 채널이 우세해야"


def test_mirror_policy_blinks_only_the_alert_colour():
    from control import MirrorColorPolicy

    p = MirrorColorPolicy(alert="red")
    red = p.decide(SceneFeatures("red", 5, 0.4, 200, 120, 0.5, (255, 0, 0)))
    green = p.decide(SceneFeatures("green", 60, 0.4, 200, 120, 0.5, (0, 255, 0)))
    assert red.mode == "blink" and green.mode == "on"


def test_mirror_policy_turns_off_with_nothing_seen():
    from control import MirrorColorPolicy

    assert MirrorColorPolicy().decide(
        SceneFeatures(None, None, 0.0, 0.0, 100, None, None)
    ).mode == "off"


def test_mirror_policy_never_violates_the_contract():
    from control import MirrorColorPolicy

    p = MirrorColorPolicy()
    for hue in range(0, 180, 7):
        from control import hue_to_rgb

        cmd = p.decide(
            SceneFeatures("red", hue, 0.3, 200, 120, 0.5, hue_to_rgb(hue))
        )
        assert all(0 <= c <= 255 for c in cmd.rgb)
        assert 10 <= cmd.interval_ms <= 5000 and 0 <= cmd.level <= 255


def test_actuator_resends_colour_only_when_it_changes():
    from control.actuator import SerialLedActuator

    a = SerialLedActuator.__new__(SerialLedActuator)   # 시리얼 없이 _diff 만 검증
    a._last = LedCommand("on", rgb=(255, 0, 0), level=100)
    assert a._diff(LedCommand("on", rgb=(255, 0, 0), level=100)) == []
    assert a._diff(LedCommand("on", rgb=(0, 255, 0), level=100)) == ["RGB 0 255 0"]


def test_mirror_policy_holds_output_against_jitter():
    """노이즈로 색조가 흔들려도 명령이 바뀌지 않아야 한다."""
    from control import MirrorColorPolicy, hue_to_rgb

    p = MirrorColorPolicy(alert=None, hue_step=10)
    first = p.decide(SceneFeatures("green", 60, 0.4, 200, 120, 0.5, hue_to_rgb(60)))
    for jitter in (61, 59, 62, 58, 63):
        again = p.decide(
            SceneFeatures("green", jitter, 0.4, 200, 120, 0.5, hue_to_rgb(jitter))
        )
        assert again == first, f"색조 {jitter} 는 이력 안이라 같은 명령이어야"


def test_mirror_policy_follows_a_real_colour_change():
    """이력이 진짜 변화까지 막으면 안 된다."""
    from control import MirrorColorPolicy, hue_to_rgb

    p = MirrorColorPolicy(alert=None, hue_step=10)
    green = p.decide(SceneFeatures("green", 60, 0.4, 200, 120, 0.5, hue_to_rgb(60)))
    blue = p.decide(SceneFeatures("blue", 120, 0.4, 200, 120, 0.5, hue_to_rgb(120)))
    assert green.rgb != blue.rgb


def test_mirror_policy_resets_hold_when_object_leaves():
    """물체가 사라졌다 다시 나타나면 새 색을 따라야 한다."""
    from control import MirrorColorPolicy, hue_to_rgb

    p = MirrorColorPolicy(alert=None)
    p.decide(SceneFeatures("green", 60, 0.4, 200, 120, 0.5, hue_to_rgb(60)))
    p.decide(SceneFeatures(None, None, 0.0, 0.0, 100, None, None))
    after = p.decide(SceneFeatures("blue", 118, 0.4, 200, 120, 0.5, hue_to_rgb(118)))
    assert after.rgb == hue_to_rgb(118)
