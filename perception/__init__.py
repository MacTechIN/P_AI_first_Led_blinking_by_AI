"""인지 계층 (L2) — 관측을 상위로 공급한다.

상위 계층은 카메라의 유무나 종류를 알지 못한다. 교체는 소스 지정만 바꾸면 된다:

    from perception import open_source

    with open_source("synthetic") as src:   # 카메라 없이 개발
        obs = src.read()

    with open_source("argus:0") as src:     # Jetson CSI 카메라
        obs = src.read()
"""

from .health import (
    DEFAULT_MIN_STD,
    FrameHealthError,
    assert_frame_sane,
    frame_stats,
    is_frame_sane,
)
from .sources import (
    IMX708_FLAT_VALUE_8BIT,
    FrameSource,
    ImageFileSource,
    SyntheticSource,
    V4L2Source,
    flat,
    moving_patch,
    open_source,
    patch,
    solid,
)
from .types import Observation


def __getattr__(name: str):  # ArgusSource 는 gi 를 요구하므로 지연 로드
    if name == "ArgusSource":
        from .argus import ArgusSource

        return ArgusSource
    raise AttributeError(name)

__all__ = [
    "Observation",
    "FrameSource",
    "SyntheticSource",
    "ImageFileSource",
    "V4L2Source",
    "ArgusSource",
    "open_source",
    "solid",
    "patch",
    "moving_patch",
    "flat",
    "assert_frame_sane",
    "is_frame_sane",
    "frame_stats",
    "FrameHealthError",
    "DEFAULT_MIN_STD",
    "IMX708_FLAT_VALUE_8BIT",
]
