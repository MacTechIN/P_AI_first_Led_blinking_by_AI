"""건전성 검사 시험 — ADR-0005 가 실제로 IMX708 사례를 잡는지 확인한다."""

import numpy as np
import pytest

from perception import (
    IMX708_FLAT_VALUE_8BIT,
    FrameHealthError,
    assert_frame_sane,
    frame_stats,
    is_frame_sane,
)


def test_constant_frame_rejected():
    """IMX708 재현: 모든 픽셀이 같은 값인 프레임은 거부된다."""
    frame = np.full((480, 640, 3), IMX708_FLAT_VALUE_8BIT, dtype=np.uint8)
    with pytest.raises(FrameHealthError, match="constant frame"):
        assert_frame_sane(frame)


def test_zero_frame_rejected():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    with pytest.raises(FrameHealthError, match="constant frame"):
        assert_frame_sane(frame)


def test_nearly_flat_frame_rejected():
    """상수는 아니지만 사실상 평탄한 프레임도 거부된다."""
    frame = np.full((480, 640, 3), 100, dtype=np.uint8)
    frame[0, 0, 0] = 101  # min != max 이지만 std 는 0 에 가깝다
    with pytest.raises(FrameHealthError, match="flat frame"):
        assert_frame_sane(frame)


def test_real_scene_accepted():
    rng = np.random.default_rng(0)
    frame = rng.integers(0, 256, size=(480, 640, 3), dtype=np.uint8)
    assert_frame_sane(frame)  # 예외가 없으면 통과


def test_dark_but_noisy_frame_accepted():
    """렌즈 캡을 씌운 어두운 장면도 센서 노이즈 덕에 통과해야 한다.

    이게 막히면 임계값이 너무 높아 정상 촬영을 오탐하는 것이다.
    """
    rng = np.random.default_rng(1)
    frame = np.clip(rng.normal(8, 3, size=(240, 320, 3)), 0, 255).astype(np.uint8)
    assert_frame_sane(frame)


def test_empty_and_none_rejected():
    with pytest.raises(FrameHealthError, match="empty"):
        assert_frame_sane(np.empty((0, 0, 3), dtype=np.uint8))
    with pytest.raises(FrameHealthError, match="None"):
        assert_frame_sane(None)


def test_is_frame_sane_does_not_raise():
    assert is_frame_sane(np.full((10, 10, 3), 7, dtype=np.uint8)) is False
    rng = np.random.default_rng(2)
    assert is_frame_sane(rng.integers(0, 256, (10, 10, 3), dtype=np.uint8)) is True


def test_frame_stats_shape():
    frame = np.full((4, 4, 3), 50, dtype=np.uint8)
    stats = frame_stats(frame)
    assert stats == {"min": 50.0, "max": 50.0, "mean": 50.0, "std": 0.0}
