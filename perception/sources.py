"""프레임 소스 — 상위 계층이 카메라 유무를 모르게 한다 (ADR-0004).

핵심은 SyntheticSource 다. 카메라가 없어도 VS-2 이후를 개발할 수 있게 해서
임계 경로를 끊는다. 실제 카메라(V4L2Source)와 완전히 같은 인터페이스를 쓰므로
나중에 교체해도 상위 코드는 바뀌지 않는다.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterator, Sequence

import numpy as np

from .health import FrameHealthError, assert_frame_sane
from .types import Observation

Painter = Callable[[int], np.ndarray]
"""seq 를 받아 RGB uint8 이미지를 만드는 함수."""


class FrameSource(ABC):
    """모든 프레임 소스의 공통 인터페이스.

    컨텍스트 매니저로 쓰는 것을 기본으로 한다:

        with SyntheticSource() as src:
            obs = src.read()
    """

    def __init__(self, *, source_id: str, check_health: bool = True) -> None:
        self.source_id = source_id
        self.check_health = check_health
        self._seq = 0
        self._opened = False

    # --- 하위 구현이 채우는 부분 ---

    @abstractmethod
    def _open(self) -> None: ...

    @abstractmethod
    def _close(self) -> None: ...

    @abstractmethod
    def _grab(self) -> np.ndarray:
        """RGB uint8 프레임 하나. 실패하면 예외."""

    def _meta(self) -> dict[str, Any]:
        return {}

    # --- 공통 동작 ---

    def open(self) -> "FrameSource":
        if not self._opened:
            self._open()
            self._opened = True
        return self

    def close(self) -> None:
        if self._opened:
            self._close()
            self._opened = False

    def read(self) -> Observation:
        """관측 하나를 취득한다. check_health 면 건전성 검사를 통과해야 한다."""
        if not self._opened:
            raise RuntimeError(f"{self.source_id}: open() 을 먼저 호출해야 한다")

        frame = self._grab()
        if self.check_health:
            try:
                assert_frame_sane(frame)
            except FrameHealthError as e:
                raise FrameHealthError(f"{self.source_id}: {e}") from e

        obs = Observation(
            image=frame,
            source_id=self.source_id,
            seq=self._seq,
            timestamp=time.time(),
            meta=self._meta(),
        )
        self._seq += 1
        return obs

    def stream(self, limit: int | None = None) -> Iterator[Observation]:
        """관측을 연속으로 낸다. limit 이 None 이면 무한."""
        n = 0
        while limit is None or n < limit:
            yield self.read()
            n += 1

    def describe(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "type": type(self).__name__,
            "opened": self._opened,
            "seq": self._seq,
            **self._meta(),
        }

    def __enter__(self) -> "FrameSource":
        return self.open()

    def __exit__(self, *exc: object) -> None:
        self.close()


# --------------------------------------------------------------------------
# 합성 소스 — 카메라 없이 개발하기 위한 것
# --------------------------------------------------------------------------


def solid(color: Sequence[int], size: tuple[int, int] = (640, 480)) -> Painter:
    """단색 화면. 노이즈를 약간 섞어 건전성 검사를 통과시킨다.

    노이즈가 없으면 std=0 이라 assert_frame_sane 이 막는다. 이건 검사가
    제대로 동작한다는 뜻이므로, 의도적으로 정상인 단색을 원하면 여기를 쓴다.
    """
    w, h = size
    rgb = np.array(color, dtype=np.uint8)

    def paint(seq: int) -> np.ndarray:
        rng = np.random.default_rng(seq)
        img = np.broadcast_to(rgb, (h, w, 3)).astype(np.int16)
        img = img + rng.integers(-4, 5, size=(h, w, 3), dtype=np.int16)
        return np.clip(img, 0, 255).astype(np.uint8)

    return paint


def patch(
    fg: Sequence[int],
    bg: Sequence[int] = (32, 32, 32),
    box: tuple[float, float, float, float] = (0.3, 0.3, 0.7, 0.7),
    size: tuple[int, int] = (640, 480),
) -> Painter:
    """배경 위에 색 사각형 하나. VS-2 의 색 판별 개발에 쓴다.

    box 는 (x0, y0, x1, y1) 비율. 기본값은 가운데 40% 영역.
    """
    w, h = size
    base = solid(bg, size)
    fg_rgb = np.array(fg, dtype=np.uint8)
    x0, y0, x1, y1 = box

    def paint(seq: int) -> np.ndarray:
        img = base(seq)
        img[int(y0 * h) : int(y1 * h), int(x0 * w) : int(x1 * w)] = fg_rgb
        return img

    return paint


def moving_patch(
    fg: Sequence[int],
    bg: Sequence[int] = (32, 32, 32),
    size: tuple[int, int] = (640, 480),
    period: int = 30,
) -> Painter:
    """좌우로 움직이는 색 사각형. 방향 판단(정의서의 "방향 표시") 개발용."""
    w, h = size

    def paint(seq: int) -> np.ndarray:
        t = (seq % period) / period
        x0 = 0.05 + 0.6 * t
        return patch(fg, bg, (x0, 0.35, x0 + 0.3, 0.65), size)(seq)

    return paint


IMX708_FLAT_VALUE_8BIT = 4100 >> 8
"""IMX708 사례에서 관측된 상수 4100 을 8비트 범위로 환산한 값 (16).

4100 은 16비트 컨테이너에 담긴 RG10 샘플 값이었다. uint8 프레임으로 재현할 때
그대로 쓰면 범위를 넘으므로 8비트만 취한다. 정확한 밝기는 중요하지 않다 —
중요한 것은 **모든 픽셀이 같다**는 성질이다.
"""


def flat(
    value: int = IMX708_FLAT_VALUE_8BIT, size: tuple[int, int] = (640, 480)
) -> Painter:
    """완전 평탄 프레임 — 건전성 검사를 **일부러 실패시키는** 용도.

    검사 자체를 검사하기 위해 존재한다.
    """
    w, h = size

    def paint(seq: int) -> np.ndarray:
        return np.full((h, w, 3), value, dtype=np.uint8)

    return paint


class SyntheticSource(FrameSource):
    """합성 프레임 소스. 카메라 없이 상위 계층을 개발·시험한다."""

    def __init__(
        self,
        painter: Painter | None = None,
        *,
        source_id: str = "synthetic",
        check_health: bool = True,
        fps: float | None = None,
    ) -> None:
        super().__init__(source_id=source_id, check_health=check_health)
        self._painter = painter or patch((220, 40, 40))
        self._fps = fps

    def _open(self) -> None:
        pass

    def _close(self) -> None:
        pass

    def _grab(self) -> np.ndarray:
        if self._fps:
            time.sleep(1.0 / self._fps)
        return self._painter(self._seq)

    def _meta(self) -> dict[str, Any]:
        return {"synthetic": True, "fps": self._fps}


# --------------------------------------------------------------------------
# 파일 소스 — 골든셋 재생 (µ6.3)
# --------------------------------------------------------------------------


class ImageFileSource(FrameSource):
    """디렉터리의 이미지를 순서대로 낸다. 평가·재현에 쓴다."""

    SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}

    def __init__(
        self,
        path: str | Path,
        *,
        source_id: str = "files",
        check_health: bool = True,
        loop: bool = False,
    ) -> None:
        super().__init__(source_id=source_id, check_health=check_health)
        self._path = Path(path)
        self._loop = loop
        self._files: list[Path] = []

    def _open(self) -> None:
        if self._path.is_file():
            self._files = [self._path]
        else:
            self._files = sorted(
                p for p in self._path.iterdir() if p.suffix.lower() in self.SUFFIXES
            )
        if not self._files:
            raise FileNotFoundError(f"이미지를 찾지 못했다: {self._path}")

    def _close(self) -> None:
        self._files = []

    def _grab(self) -> np.ndarray:
        if self._seq >= len(self._files) and not self._loop:
            raise StopIteration(f"{self.source_id}: 이미지 소진")
        path = self._files[self._seq % len(self._files)]
        return _imread_rgb(path)

    def _meta(self) -> dict[str, Any]:
        return {"count": len(self._files), "path": str(self._path)}


# --------------------------------------------------------------------------
# 실제 카메라
# --------------------------------------------------------------------------


class V4L2Source(FrameSource):
    """cv2.VideoCapture 기반 실물 카메라. USB 웹캠과 CSI 양쪽에 쓴다.

    cv2 는 BGR 을 주므로 여기서 RGB 로 바꾼다 — 색 공간 변환은 이 경계에서만
    일어나고, 상위는 전부 RGB 를 가정한다 (types.py 참조).
    """

    def __init__(
        self,
        device: int | str = 0,
        *,
        width: int | None = None,
        height: int | None = None,
        source_id: str | None = None,
        check_health: bool = True,
        warmup: int = 5,
    ) -> None:
        super().__init__(
            source_id=source_id or f"v4l2:{device}", check_health=check_health
        )
        self._device = device
        self._width = width
        self._height = height
        self._warmup = warmup
        self._cap: Any = None

    def _open(self) -> None:
        import cv2  # 지연 import — 합성 소스만 쓸 때 cv2 를 요구하지 않는다

        self._cap = cv2.VideoCapture(self._device)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"카메라를 열지 못했다: {self._device}. "
                "ls /dev/video* 로 장치를 확인하라"
            )
        if self._width:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        if self._height:
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

        # 첫 프레임들은 자동노출이 수렴하기 전이라 버린다
        for _ in range(self._warmup):
            self._cap.read()

    def _close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _grab(self) -> np.ndarray:
        import cv2

        ok, frame_bgr = self._cap.read()
        if not ok or frame_bgr is None:
            raise RuntimeError(f"{self.source_id}: 프레임 취득 실패")
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    def _meta(self) -> dict[str, Any]:
        if self._cap is None:
            return {"device": str(self._device)}
        import cv2

        return {
            "device": str(self._device),
            "width": int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        }


def _imread_rgb(path: Path) -> np.ndarray:
    import cv2

    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"이미지를 읽지 못했다: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def open_source(spec: str = "synthetic", **kwargs: Any) -> FrameSource:
    """문자열로 소스를 고른다. 설정 파일·CLI 에서 쓴다.

        open_source("synthetic")
        open_source("v4l2:0")
        open_source("files:/path/to/golden")
    """
    if spec == "synthetic" or spec.startswith("synthetic:"):
        return SyntheticSource(**kwargs)
    if spec.startswith("v4l2:"):
        dev = spec.split(":", 1)[1]
        return V4L2Source(int(dev) if dev.isdigit() else dev, **kwargs)
    if spec.startswith("files:"):
        return ImageFileSource(spec.split(":", 1)[1], **kwargs)
    raise ValueError(f"알 수 없는 소스 지정: {spec}")
