"""S-1 — 가상 카메라. 같은 현장을 읽는다.

`FrameSource` 를 그대로 구현하므로 상위 계층은 이것이 시뮬레이터인지 모른다.
그것이 ADR-0004 가 노린 성질이고, 여기서 값을 치른다.
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
    ) -> None:
        super().__init__(source_id=source_id, check_health=check_health)
        self.world = world
        self._fps = fps

    def _open(self) -> None:
        pass

    def _close(self) -> None:
        pass

    def _grab(self) -> np.ndarray:
        if self._fps:
            time.sleep(1.0 / self._fps)
        return self.world.render(self._seq)

    def _meta(self) -> dict[str, Any]:
        return {"sim": True, "fps": self._fps, **self.world.describe()}
