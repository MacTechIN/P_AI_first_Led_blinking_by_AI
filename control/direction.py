"""예제 1 — 방향 지시기. 물체가 화면 어디에 있는지를 LED 색으로 표시한다.

정의서의 "방향 표시" 를 문자 그대로 구현한다. 그리고 **공간 판단에서 규칙과
VLM 중 무엇이 나은지** 재기 위한 공통 기반이기도 하다.

색 판별(VS-2·VS-3)과 달리 여기서는 **정답을 알 수 있다.** 합성 이미지는 사각형을
넣은 위치가 정답이고, 실물은 LED 를 차분으로 찾으면 그 좌표가 정답이다.
정답이 있으면 규칙과 모델을 같은 자로 잴 수 있다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from perception import Observation

from .commands import LedCommand
from .features import SceneFeatures, hue_to_rgb
from .policy import Policy

Zone = Literal["left", "centre", "right"]

ZONE_HUE: dict[Zone, int] = {"left": 120, "centre": 60, "right": 0}
"""왼쪽 파랑 · 가운데 초록 · 오른쪽 빨강.

빨강을 오른쪽에 둔 이유는 자의적이지만 **일관되게** 쓴다. 색과 방향의 대응은
학습자가 외워야 하는 것이므로, 교재 전체에서 같아야 한다.
"""

DEFAULT_MARGIN = 0.15
"""가운데 구역의 반폭. 0.15 면 화면 중앙 30% 가 '가운데' 다.

경계를 칼같이 나누면 물체가 경계에 걸쳤을 때 좌우로 떨린다. 모듈 3 의 이력과
같은 문제이고, 여기서는 넓은 중립 구역이 그 역할을 한다.
"""


def zone_of(x: float, margin: float = DEFAULT_MARGIN) -> Zone:
    """가로 위치 0~1 을 구역 이름으로. 0 이 왼쪽 끝."""
    if x < 0.5 - margin:
        return "left"
    if x > 0.5 + margin:
        return "right"
    return "centre"


@dataclass(frozen=True)
class DirectionPolicy(Policy):
    """물체의 가로 위치를 색으로 표시한다. 규칙 기반, 판단 비용 0."""

    margin: float = DEFAULT_MARGIN
    level: int = 180
    hold: float = 0.08
    """구역 경계에서의 이력. 직전 구역을 이 폭만큼 더 유지한다."""

    def __post_init__(self) -> None:
        object.__setattr__(self, "_held", None)

    def decide(
        self, features: SceneFeatures, observation: Observation | None = None
    ) -> LedCommand:
        if features.color is None or features.centroid_x is None:
            object.__setattr__(self, "_held", None)
            return LedCommand("off")

        zone = self._stick(features.centroid_x)
        return LedCommand("on", rgb=hue_to_rgb(ZONE_HUE[zone]), level=self.level)

    def _stick(self, x: float) -> Zone:
        """직전 구역을 조금 더 유지해 경계에서 떨리지 않게 한다."""
        held: Zone | None = getattr(self, "_held", None)
        zone = zone_of(x, self.margin)
        if held is not None and zone != held:
            # 경계를 hold 만큼 더 넘어야 바꾼다
            if zone_of(x, self.margin + self.hold) == held:
                zone = held
        object.__setattr__(self, "_held", zone)
        return zone
