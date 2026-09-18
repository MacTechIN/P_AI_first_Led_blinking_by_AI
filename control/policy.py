"""µ2.2 — 특징을 LED 명령으로 옮긴다. **규칙 기반, AI 없음.**

이것이 VS-3 의 기준선이다. VLM 이 이상하게 굴 때 "모델이 틀린 것" 과
"배선이 틀린 것" 을 가르려면, 같은 배선 위에서 확실히 동작하는 정책이 있어야 한다.

RGB LED 가 붙으면서 정의서의 "동일 색 표시" 를 문자 그대로 구현할 수 있게 됐다 —
`MirrorColorPolicy` 가 본 색을 그대로 켠다. 단색 LED 시절의 점멸 부호화
(`ColorRulePolicy`) 도 남겨둔다. 색맹 관찰자나 단색 LED 배선에서는 그쪽이 낫고,
무엇보다 두 정책을 같은 배선에서 갈아 끼울 수 있다는 점이 VS-3 의 전제다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from perception import Observation

from .commands import LedCommand
from .features import SceneFeatures, hue_to_rgb


class Policy(ABC):
    """특징 → 명령. VS-3 의 VLM 정책도 같은 인터페이스를 구현한다.

    `observation` 은 선택적이다. 규칙 정책은 추출된 특징만으로 충분하지만 VLM 은
    원본 이미지를 봐야 하므로, 특징만 넘기면 VLM 정책을 이 인터페이스 뒤에 둘 수
    없다. 기본값을 None 으로 두어 기존 정책은 그대로 동작한다.
    """

    @abstractmethod
    def decide(
        self, features: SceneFeatures, observation: "Observation | None" = None
    ) -> LedCommand: ...

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


class MirrorColorPolicy(Policy):
    """본 색을 그대로 LED 에 띄운다 — 정의서의 "동일 색 표시".

    면적이 밝기를 정한다. 물체가 클수록(가까울수록) 밝게 반응하는 것이
    자연스럽고, 관측에서 실제로 변하는 양이기 때문이다.
    """

    def __init__(
        self,
        *,
        min_level: int = 40,
        max_level: int = 255,
        alert: str | None = "red",
        hue_step: int = 10,
        level_step: int = 24,
    ) -> None:
        self.min_level = min_level
        self.max_level = max_level
        self.alert = alert
        """이 색만은 점멸시켜 경고로 구분한다. None 이면 전부 상시 점등."""
        self.hue_step = hue_step
        self.level_step = level_step
        """출력을 붙잡아 두는 폭. 양자화가 아니라 **이력(hysteresis)** 이다.

        관측 색조는 센서 노이즈로 프레임마다 흔들린다. 그대로 내보내면 매 프레임
        명령이 달라져 LED 가 미세하게 깜빡이고 시리얼이 붐빈다 — 실측에서 20 스텝
        중 18 회가 전송됐다.

        단순 양자화로는 부족했다(18 → 11). 값이 스텝 경계 위에서 진동하면 양자화
        결과도 같이 진동하기 때문이다. 그래서 **직전에 내보낸 값** 과 비교해
        이 폭을 넘을 때만 바꾼다. 경계가 고정되어 있지 않으므로 진동이 통과하지
        못한다.

        정확도를 버리는 것이 아니라 **판단의 분해능을 관측의 신뢰도에 맞추는** 것이다.
        """
        self._held_hue: float | None = None
        self._held_level: int | None = None

    def decide(
        self, features: SceneFeatures, observation: "Observation | None" = None
    ) -> LedCommand:
        if features.color is None or features.hue is None:
            self._held_hue = self._held_level = None
            return LedCommand("off")

        hue = self._hold_hue(features.hue)
        rgb = hue_to_rgb(hue)

        raw = _level_from_coverage(features.coverage, self.min_level, self.max_level)
        level = self._hold_level(raw)

        if self.alert and features.color == self.alert:
            return LedCommand("blink", rgb=rgb, interval_ms=150, level=level)
        return LedCommand("on", rgb=rgb, level=level)

    def _hold_hue(self, hue: float) -> float:
        if self._held_hue is None or _hue_distance(hue, self._held_hue) >= self.hue_step:
            self._held_hue = hue
        return self._held_hue

    def _hold_level(self, level: int) -> int:
        if self._held_level is None or abs(level - self._held_level) >= self.level_step:
            self._held_level = level
        return self._held_level


def _hue_distance(a: float, b: float) -> float:
    """색조는 원형이다 — 179 와 0 은 1 만큼 떨어져 있다."""
    d = abs(a - b) % 180
    return min(d, 180 - d)


def _level_from_coverage(coverage: float, lo: int, hi: int) -> int:
    """면적 0.05~0.60 을 밝기 구간에 선형 사상하고 양 끝에서 포화시킨다."""
    t = min(max((coverage - 0.05) / 0.55, 0.0), 1.0)
    return int(lo + max(hi - lo, 0) * t)


class ColorRulePolicy(Policy):
    """지배 색으로 점멸 주기를, 면적으로 밝기를 정한다.

    면적을 밝기에 쓰는 이유: 물체가 가까울수록(크게 보일수록) 강하게 반응하는
    것이 자연스럽고, 관측에서 실제로 변하는 양이기 때문이다.
    """

    def __init__(self, *, min_level: int = 40, max_level: int = 255) -> None:
        self.min_level = min_level
        self.max_level = max_level

    def decide(
        self, features: SceneFeatures, observation: "Observation | None" = None
    ) -> LedCommand:
        if features.color is None:
            return LedCommand("off")

        base = COLOR_RULES.get(features.color)
        if base is None:
            return LedCommand("off")

        level = _level_from_coverage(features.coverage, self.min_level, self.max_level)
        return LedCommand(
            base.mode,
            rgb=features.rgb or (255, 255, 255),
            interval_ms=base.interval_ms,
            level=level,
        )
