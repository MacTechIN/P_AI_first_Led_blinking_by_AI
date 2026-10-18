"""S-1 — 가상 카메라. 같은 현장을 읽는다.

`FrameSource` 를 그대로 구현하므로 상위 계층은 이것이 시뮬레이터인지 모른다.
그것이 ADR-0004 가 노린 성질이고, 여기서 값을 치른다.

**노이즈는 기본으로 켜져 있다.** 깨끗한 프레임만 내는 카메라는 존재하지 않고,
무엇보다 노이즈가 없으면 이력(hysteresis)이 왜 필요한지 보여줄 수 없다
(ADR-0007). 읽기 노이즈와 손떨림, 둘 다 실제로 있는 것만 넣는다.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from perception.sources import FrameSource

from .world import SimWorld


class SimSource(FrameSource):
    """가상 현장을 촬영한다."""

    def __init__(
        self,
        world: SimWorld,
        *,
        source_id: str = "sim",
        check_health: bool = True,
        fps: float | None = None,
        read_noise: float = 4.0,
        jitter_px: int = 1,
        seed: int = 0,
    ) -> None:
        super().__init__(source_id=source_id, check_health=check_health)
        self.world = world
        self._fps = fps
        self.read_noise = read_noise
        """화소당 읽기 노이즈의 표준편차 (8비트 단위)."""
        self.jitter_px = jitter_px
        """카메라 흔들림. 정지 장면이라도 프레임마다 경계가 미세하게 움직인다."""
        self._rng = np.random.default_rng(seed)

    def _open(self) -> None:
        pass

    def _close(self) -> None:
        pass

    def _grab(self) -> np.ndarray:
        if self._fps:
            time.sleep(1.0 / self._fps)
        return self._sensor(self.world.render(self._seq))

    def _sensor(self, frame: np.ndarray) -> np.ndarray:
        """렌즈를 지난 빛이 화소가 되는 과정에서 더해지는 것들."""
        if self.jitter_px:
            dx, dy = self._rng.integers(-self.jitter_px, self.jitter_px + 1, 2)
            frame = np.roll(frame, (int(dy), int(dx)), axis=(0, 1))
        if self.read_noise:
            noisy = frame.astype(np.float32)
            noisy += self._rng.normal(0.0, self.read_noise, frame.shape)
            frame = np.clip(noisy, 0, 255).astype(np.uint8)
        return frame

    def _meta(self) -> dict[str, Any]:
        return {
            "sim": True,
            "fps": self._fps,
            "read_noise": self.read_noise,
            "jitter_px": self.jitter_px,
            **self.world.describe(),
        }
