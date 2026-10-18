"""S-1 시험 — 가상 LED 가 실물의 성질을 재현하는가.

이 파일이 지키려는 것은 "시뮬레이터가 돈다" 가 아니라 **"시뮬레이터가 기록된
실패를 그대로 낸다"** 이다. 잘 되는 시뮬레이터는 해피패스만 가르친다.
"""

import cv2
import numpy as np
import pytest

from control import ControlLoop, LedCommand, MirrorColorPolicy
from control.features import DEFAULT_ROI, extract
from perception.health import assert_frame_sane
from sim import LedPanel, SimActuator, SimSource, SimWorld


def hue_of(rgb) -> int:
    px = np.uint8([[list(rgb)]])
    return int(cv2.cvtColor(px, cv2.COLOR_RGB2HSV)[0, 0, 0])


# --- 펌웨어와 같은 계산 ---


def test_duty_matches_firmware_integer_arithmetic():
    """dutyFor() 는 단계마다 버린다. 부동소수로 바꾸면 값이 달라진다."""
    panel = LedPanel(gains=(120, 200, 255))
    cmd = LedCommand("on", rgb=(255, 255, 0), level=255)
    assert panel.duty(cmd) == (120, 200, 0)

    half = LedCommand("on", rgb=(255, 255, 0), level=128)
    expected = tuple(v * 128 // 255 * g // 255 for v, g in zip((255, 255, 0), (120, 200, 255)))
    assert panel.duty(half) == expected


def test_off_emits_nothing():
    assert LedPanel().emit(LedCommand("off"), 0.0) == (0, 0, 0)


def test_blink_phase_follows_the_clock():
    panel = LedPanel()
    cmd = LedCommand("blink", rgb=(255, 0, 0), interval_ms=100)
    assert panel.is_lit(cmd, 0.00) is True
    assert panel.is_lit(cmd, 0.05) is True
    assert panel.is_lit(cmd, 0.10) is False     # 100ms 뒤 반전
    assert panel.is_lit(cmd, 0.20) is True


# --- 공통 저항 경쟁 (문제 2 의 재현) ---


MEASURED = [
    # (빨강 듀티, 초록 듀티, 교정 기록에 남은 색조)
    (255, 255, 0),
    (120, 255, 38),
    (60, 255, 58),
]


@pytest.mark.parametrize("dr,dg,recorded_hue", MEASURED)
def test_competition_reproduces_the_measured_hues(dr, dg, recorded_hue):
    """실물에서 잰 세 점을 시뮬레이터가 다시 내야 한다.

    이 수치는 docs/tech/notes/rgb-led-calibration.md 의 검증 실험이다.
    모델 계수를 바꾸면 여기서 먼저 깨진다.
    """
    emitted = LedPanel(gains=(255, 255, 255)).compete((dr, dg, 0))
    assert abs(hue_of(emitted) - recorded_hue) <= 4


def test_yellow_comes_out_red_on_the_real_wiring():
    """보정 없이 노랑을 명령하면 빨강이 나온다 — 교정 기록의 문제 2 그 자체."""
    raw = LedPanel(gains=(255, 255, 255))
    emitted = raw.emit(LedCommand("on", rgb=(255, 255, 0)), 0.0)
    assert hue_of(emitted) <= 10              # 노랑(30)이 아니라 빨강(0)


def test_single_channel_is_untouched_by_competition():
    """경쟁은 섞을 때만 일어난다. 단색은 듀티 그대로 나와야 한다."""
    panel = LedPanel(gains=(255, 255, 255))
    assert panel.compete((200, 0, 0)) == (200, 0, 0)
    assert panel.compete((0, 200, 0)) == (0, 200, 0)
    assert panel.compete((0, 0, 200)) == (0, 0, 200)


def test_per_channel_resistor_removes_the_competition():
    """올바른 배선이었다면 노랑이 노랑으로 나온다."""
    fixed = LedPanel(gains=(255, 255, 255), shared_resistor=False)
    emitted = fixed.emit(LedCommand("on", rgb=(255, 255, 0)), 0.0)
    assert 23 <= hue_of(emitted) <= 33        # features 의 yellow 대역


# --- 극성 버그 (문제 1 의 재현) ---


def test_polarity_bug_turns_red_into_cyan():
    """반전을 적용하지 않으면 R 만 꺼지고 G+B 가 켜진다."""
    broken = LedPanel(gains=(255, 255, 255), polarity_fixed=False)
    r, g, b = broken.emit(LedCommand("on", rgb=(255, 0, 0)), 0.0)
    assert r == 0 and g > 0 and b > 0


def test_polarity_bug_turns_white_into_darkness():
    broken = LedPanel(gains=(255, 255, 255), polarity_fixed=False)
    assert broken.emit(LedCommand("on", rgb=(255, 255, 255)), 0.0) == (0, 0, 0)


# --- 장면과 닫힌 루프 ---


def test_rendered_frame_passes_the_health_check():
    world = SimWorld(clock=lambda: 0.0)
    assert_frame_sane(world.render(0))


def test_led_sits_outside_the_default_roi():
    """기본 배치에서 LED 는 특징 추출에 섞이지 않아야 한다.

    섞이면 루프가 자기 출력을 입력으로 먹는다. 그것도 실제 현상이지만
    기본값이 되어서는 안 된다.
    """
    x0, _, x1, _ = DEFAULT_ROI
    assert not (x0 <= SimWorld().led_at[0] <= x1)


def test_led_core_saturates_to_white():
    """실물에서 코어는 어떤 색이든 흰색으로 포화한다. 주변부에만 색이 남는다."""
    world = SimWorld(clock=lambda: 0.0, background_rgb=(0, 0, 0))
    world.apply(LedCommand("on", rgb=(0, 0, 255), level=255))
    frame = world.render(0)
    h, w = frame.shape[:2]
    core = frame[int(0.5 * h), int(world.led_at[0] * w)]
    assert core.min() > 200                   # 세 채널이 모두 높다 = 흰색


def test_the_loop_closes_command_shows_up_in_the_next_frame():
    """S-1 의 전부 — 정책이 켠 LED 를 카메라가 본다."""
    world = SimWorld(clock=lambda: 0.0)
    with SimSource(world) as src:
        loop = ControlLoop(src, MirrorColorPolicy(), SimActuator(world))

        world.set_card((40, 190, 70))         # 초록 색지
        loop.step()
        emitted = world.emitted()
        assert emitted[1] == max(emitted)     # 초록이 가장 세다

        world.set_card((50, 70, 215))         # 파랑 색지
        loop.step()
        emitted = world.emitted()
        assert emitted[2] == max(emitted)


def test_actuator_records_what_the_wire_would_have_carried():
    world = SimWorld(clock=lambda: 0.0)
    act = SimActuator(world)
    act.apply(LedCommand("on", rgb=(255, 0, 0)))
    act.apply(LedCommand("blink", rgb=(0, 255, 0), interval_ms=200))
    assert len(act.history) == 2
    assert act.wire_lines == 3 + 4            # RGB·LEVEL·ON / RGB·LEVEL·INT·BLINK
    assert world.commands == 2


def test_hysteresis_still_holds_the_output_in_the_simulator():
    """노이즈만으로 명령이 떨리면 ADR-0007 의 교훈을 실습할 수 없다."""
    world = SimWorld(clock=lambda: 0.0)
    act = SimActuator(world)
    with SimSource(world) as src:
        loop = ControlLoop(src, MirrorColorPolicy(), act)
        loop.run(20)                           # 색지는 그대로
    assert len(act.history) == 1               # 첫 명령 한 번뿐


# --- 출력이 입력에 섞일 때 (재 보고 알아낸 조건) ---


def _latch_test(radius: int, led_at: tuple[float, float]) -> list[str | None]:
    """초록 색지를 보여준 뒤 치운다. 그 다음 네 프레임이 무엇을 보는가."""
    world = SimWorld(clock=lambda: 0.0, led_at=led_at, led_radius_px=radius)
    with SimSource(world) as src:
        loop = ControlLoop(src, MirrorColorPolicy(), SimActuator(world))
        world.set_card((40, 190, 70))
        loop.run(3)
        world.set_card((30, 30, 34))          # 색지를 치운다
        return [loop.step().features.color for _ in range(4)]


def test_moving_the_led_into_the_roi_is_not_enough():
    """기본 반경에서는 ROI 안으로 옮겨도 판정이 뒤집히지 않는다.

    옮기기만 하면 발진할 것이라고 예상했으나 **측정하니 아니었다.** 코어는
    흰색으로 포화해 채도 문턱에서 걸러지고, 남은 테두리는 면적으로 색지에 진다.
    """
    assert _latch_test(24, (0.5, 0.5)) == [None, None, None, None]


def test_a_big_led_inside_the_roi_latches_onto_its_own_output():
    """반경이 커지면 루프가 자기가 켠 불을 보고 색지가 없는데도 초록이라고 한다."""
    assert _latch_test(70, (0.5, 0.5)) == ["green"] * 4


def test_the_same_big_led_outside_the_roi_lets_go():
    """같은 크기라도 ROI 밖이면 색지를 치웠을 때 놓는다 — 위치가 원인이다."""
    assert _latch_test(70, (0.88, 0.5))[-1] is None
