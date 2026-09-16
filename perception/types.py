"""인지 계층이 상위로 넘기는 자료형.

Observation 은 이미지 단독이 아니라 **관측 묶음**이다. VS-5(µ5.3)에서 조도·소리·
연기 센서가 들어올 때 포맷을 다시 설계하지 않으려고 처음부터 센서 슬롯을 둔다.

색 공간은 **RGB** 로 통일한다. cv2 는 BGR 로 주지만 변환을 경계(V4L2Source)에서
한 번만 하고, 소비자는 전부 RGB 를 가정한다. VLM·PIL 이 RGB 를 기대하므로
소비자마다 기억해야 하는 규칙을 남기지 않는 편이 낫다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Observation:
    """한 시점의 관측. 이미지와 센서값을 함께 담는다."""

    image: np.ndarray | None
    """RGB uint8, shape (H, W, 3). 센서 전용 관측이면 None."""

    source_id: str
    """어느 소스에서 왔는지. 로그·재현에 쓴다."""

    seq: int
    """소스별 단조 증가 시퀀스. 프레임 누락 탐지에 쓴다."""

    timestamp: float = field(default_factory=time.time)
    """취득 시각 (epoch seconds)."""

    sensors: dict[str, float] = field(default_factory=dict)
    """센서 이름 → 값. VS-5 에서 채워진다."""

    meta: dict[str, Any] = field(default_factory=dict)
    """소스별 부가 정보 (노출, 해상도 등). 판단에 쓰지 않는다."""

    @property
    def size(self) -> tuple[int, int]:
        """(width, height). 이미지가 없으면 (0, 0)."""
        if self.image is None:
            return (0, 0)
        h, w = self.image.shape[:2]
        return (w, h)

    def describe(self) -> dict[str, Any]:
        """사람이 읽는 요약. 결정 로그(µ6.4)에 남길 용도."""
        w, h = self.size
        return {
            "source": self.source_id,
            "seq": self.seq,
            "timestamp": self.timestamp,
            "size": f"{w}x{h}",
            "sensors": dict(self.sensors),
        }
