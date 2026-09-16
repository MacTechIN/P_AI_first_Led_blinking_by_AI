"""소스 시험. **카메라 없이** 전부 통과해야 한다 — 이것이 µ1.4 의 합격 조건이다."""

import numpy as np
import pytest

from perception import (
    FrameHealthError,
    ImageFileSource,
    Observation,
    SyntheticSource,
    flat,
    moving_patch,
    open_source,
    patch,
    solid,
)


def test_synthetic_source_yields_sane_frames():
    with SyntheticSource() as src:
        obs = src.read()
    assert isinstance(obs, Observation)
    assert obs.image.dtype == np.uint8
    assert obs.image.shape == (480, 640, 3)
    assert obs.size == (640, 480)


def test_sequence_increments_and_timestamps_advance():
    with SyntheticSource() as src:
        a, b = src.read(), src.read()
    assert (a.seq, b.seq) == (0, 1)
    assert b.timestamp >= a.timestamp


def test_read_before_open_is_an_error():
    src = SyntheticSource()
    with pytest.raises(RuntimeError, match="open"):
        src.read()


def test_flat_painter_is_caught_by_health_check():
    """합성 소스라도 평탄 프레임이면 막힌다 — 검사가 소스와 무관하게 동작한다."""
    with SyntheticSource(flat()) as src:
        with pytest.raises(FrameHealthError, match="constant frame"):
            src.read()


def test_health_check_can_be_disabled_for_raw_debugging():
    with SyntheticSource(flat(), check_health=False) as src:
        obs = src.read()
    assert obs.image.std() == 0.0


def test_solid_painter_passes_health_check():
    """단색이어도 센서 노이즈 모사 덕분에 통과한다."""
    with SyntheticSource(solid((10, 200, 10))) as src:
        obs = src.read()
    assert abs(float(obs.image[..., 1].mean()) - 200) < 3


def test_patch_places_foreground_in_centre():
    """VS-2 색 판별이 의존하는 성질: 가운데가 전경색이다."""
    with SyntheticSource(patch(fg=(255, 0, 0), bg=(0, 0, 0))) as src:
        img = src.read().image
    h, w = img.shape[:2]
    centre = img[h // 2, w // 2]
    corner = img[2, 2]
    assert centre[0] > 200 and centre[1] < 50
    assert corner[0] < 50


def test_moving_patch_changes_position_over_time():
    """방향 판단 개발용 소스가 실제로 움직이는지."""

    def centroid_x(img):
        mask = img[..., 0].astype(int) - img[..., 2].astype(int) > 60
        xs = np.nonzero(mask.any(axis=0))[0]
        return xs.mean() if xs.size else -1.0

    with SyntheticSource(moving_patch(fg=(255, 0, 0))) as src:
        frames = [obs.image for obs in src.stream(limit=10)]
    assert centroid_x(frames[-1]) > centroid_x(frames[0]) + 10


def test_stream_respects_limit():
    with SyntheticSource() as src:
        assert len(list(src.stream(limit=4))) == 4


def test_describe_is_loggable():
    with SyntheticSource() as src:
        src.read()
        info = src.describe()
    assert info["type"] == "SyntheticSource"
    assert info["opened"] is True and info["seq"] == 1


def test_open_source_dispatch():
    assert isinstance(open_source("synthetic"), SyntheticSource)
    assert isinstance(open_source("files:/tmp"), ImageFileSource)
    with pytest.raises(ValueError, match="알 수 없는"):
        open_source("carrier-pigeon:0")


def test_v4l2_is_not_constructed_eagerly():
    """생성만으로 장치를 열지 않는다 — 카메라 없는 환경에서도 import·구성이 가능."""
    src = open_source("v4l2:0")
    assert src.describe()["opened"] is False


def test_image_file_source_round_trip(tmp_path):
    import cv2

    rng = np.random.default_rng(3)
    for i in range(3):
        img = rng.integers(0, 256, (32, 48, 3), dtype=np.uint8)
        cv2.imwrite(str(tmp_path / f"{i:02d}.png"), img)

    with ImageFileSource(tmp_path) as src:
        frames = [obs.image for obs in src.stream(limit=3)]
    assert len(frames) == 3
    assert frames[0].shape == (32, 48, 3)


def test_image_file_source_reports_missing_directory(tmp_path):
    with pytest.raises(FileNotFoundError):
        ImageFileSource(tmp_path).open()
