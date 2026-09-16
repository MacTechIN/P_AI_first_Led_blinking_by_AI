"""프레임 건전성 검사 — ADR-0005.

`/dev/video0` 이 존재하고 캡처가 성공해도 카메라가 동작하는 것은 아니다.
IMX708 을 IMX477 드라이버가 잡았을 때 3840x2160 프레임의 830만 샘플이 전부
4100 이었다. 장치 노드도, 드라이버 바인딩도, 캡처 성공도 증거가 되지 못한다.

그래서 **픽셀로 검증한다.**
"""

from __future__ import annotations

import numpy as np

DEFAULT_MIN_STD = 1.0
"""이보다 표준편차가 작으면 평탄 프레임으로 본다.

정상적인 장면은 렌즈 캡을 씌운 상태에서도 센서 노이즈로 std 가 1 을 넘는다.
반대로 설정되지 않은 센서는 std 가 정확히 0 에 가깝다.
"""


class FrameHealthError(ValueError):
    """프레임이 건전성 검사를 통과하지 못했다."""


def frame_stats(frame: np.ndarray) -> dict[str, float]:
    """검사와 로그에 공통으로 쓰는 통계."""
    return {
        "min": float(frame.min()),
        "max": float(frame.max()),
        "mean": float(frame.mean()),
        "std": float(frame.std()),
    }


def assert_frame_sane(frame: np.ndarray, *, min_std: float = DEFAULT_MIN_STD) -> None:
    """프레임이 실제 장면을 담고 있는지 검사한다. 아니면 FrameHealthError.

    통과하지 못하는 경우:
      - 빈 배열이나 크기 0
      - 모든 픽셀이 같은 값 (IMX708 사례)
      - 표준편차가 min_std 미만 (사실상 평탄)
    """
    if frame is None:
        raise FrameHealthError("frame is None")
    if frame.size == 0:
        raise FrameHealthError("frame is empty")

    stats = frame_stats(frame)

    if stats["min"] == stats["max"]:
        raise FrameHealthError(
            f"constant frame: 모든 픽셀이 {stats['min']:.0f} — "
            "센서가 설정되지 않았을 가능성 (드라이버/센서 불일치)"
        )
    if stats["std"] < min_std:
        raise FrameHealthError(
            f"flat frame: std={stats['std']:.3f} < {min_std} — {stats}"
        )


def is_frame_sane(frame: np.ndarray, *, min_std: float = DEFAULT_MIN_STD) -> bool:
    """예외 대신 참/거짓. 폴링 루프에서 쓴다."""
    try:
        assert_frame_sane(frame, min_std=min_std)
    except FrameHealthError:
        return False
    return True
