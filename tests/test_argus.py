"""ArgusSource 시험.

하드웨어 의존 시험은 카메라가 없으면 건너뛴다. 파이프라인 문자열 구성처럼
하드웨어 없이 검증 가능한 부분은 항상 돌린다.
"""

from pathlib import Path

import pytest

from perception import open_source
from perception.argus import DEFAULT_WARMUP, ArgusSource

HAS_CSI = Path("/dev/video0").exists()
requires_csi = pytest.mark.skipif(not HAS_CSI, reason="CSI 카메라 없음")


def test_pipeline_description_is_well_formed():
    """하드웨어 없이 검증 가능 — 파이프라인이 Argus→RGB→appsink 를 거치는지."""
    desc = ArgusSource(0, width=640, height=480, framerate=30).pipeline_description()
    assert "nvarguscamerasrc sensor-id=0" in desc
    assert "width=640,height=480" in desc
    assert "format=RGB" in desc, "상위는 RGB 를 가정한다 (ADR-0004)"
    assert "drop=true" in desc, "제어 루프는 최신 프레임만 필요하다"


def test_not_opened_eagerly():
    src = open_source("argus:0")
    assert isinstance(src, ArgusSource)
    assert src.describe()["opened"] is False


def test_read_before_open_is_an_error():
    with pytest.raises(RuntimeError, match="open"):
        ArgusSource(0).read()


def test_warmup_default_is_nonzero():
    """워밍업이 0 이면 자동노출 수렴 전 검은 프레임을 받는다 (실측 mean=22.7)."""
    assert DEFAULT_WARMUP > 0


@requires_csi
def test_captures_real_frames():
    with open_source("argus:0", width=1280, height=720) as src:
        obs = src.read()
    assert obs.image.shape == (720, 1280, 3)
    assert obs.image.std() > 5.0, "워밍업 후에는 노출이 수렴해 있어야 한다"


@requires_csi
def test_sequence_advances_across_reads():
    with open_source("argus:0", width=640, height=480) as src:
        frames = list(src.stream(limit=3))
    assert [o.seq for o in frames] == [0, 1, 2]
