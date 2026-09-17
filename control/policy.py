"""µ2.2 — 특징을 LED 명령으로 옮긴다. **규칙 기반, AI 없음.**

이것이 VS-3 의 기준선이다. VLM 이 이상하게 굴 때 "모델이 틀린 것" 과
"배선이 틀린 것" 을 가르려면, 같은 배선 위에서 확실히 동작하는 정책이 있어야 한다.

LED 가 하나뿐이라 색을 색으로 보여줄 수 없다. 그래서 **색을 점멸 주기로 부호화**한다.
정의서의 "동일 색 표시" 는 RGB LED 가 붙는 VS-5 에서 문자 그대로 구현된다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .commands import LedCommand
from .features import SceneFeatures


class Policy(ABC):
    """특징 → 명령. VS-3 의 VLM 정책도 같은 인터페이스를 구현한다."""

    @abstractmethod
    def decide(self, features: SceneFeatures) -> LedCommand: ...

    @property
    def name(self) -> str:
        return type(self).__name__


COLOR_RULES: dict[str, LedCommand] = {
    "red": LedCommand("blink", interval_ms=100),
    "orange": LedCommand("blink", interval_ms=200),
    "yellow": LedCommand("blink", interval_ms=300),
    "green": LedCommand("blink", interval_ms=600),
    "cyan": LedCommand("blink", interval_ms=800),
    "blue": LedCommand("on"),
    "purple": LedCommand("blink", interval_ms=1000),
}
"""색 → 기본 반응. 빨강일수록 빠르게 — 경고에 가까운 직관을 따른다."""


class ColorRulePolicy(Policy):
    """지배 색으로 점멸 주기를, 면적으로 밝기를 정한다.

    면적을 밝기에 쓰는 이유: 물체가 가까울수록(크게 보일수록) 강하게 반응하는
    것이 자연스럽고, 관측에서 실제로 변하는 양이기 때문이다.
    """

    def __init__(self, *, min_level: int = 40, max_level: int = 255) -> None:
        self.min_level = min_level
        self.max_level = max_level

    def decide(self, features: SceneFeatures) -> LedCommand:
        if features.color is None:
            return LedCommand("off")

        base = COLOR_RULES.get(features.color)
        if base is None:
            return LedCommand("off")

        # 면적 0.05~0.60 을 밝기 구간에 선형 사상하고 양 끝에서 포화시킨다
        span = max(self.max_level - self.min_level, 0)
        t = min(max((features.coverage - 0.05) / 0.55, 0.0), 1.0)
        level = int(self.min_level + span * t)

        return LedCommand(base.mode, interval_ms=base.interval_ms, level=level)
