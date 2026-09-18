"""예제 2 — 움직임 경보. 장면이 변하면 경고한다.

지금까지의 모든 모듈은 **한 프레임만** 봤다. 시간이 들어오면 새 문제가 생긴다.

**무엇을 변화로 볼 것인가.** 완전히 정지한 장면도 센서 노이즈 때문에 프레임마다
다르다. 임계값을 추측으로 정하면 오경보가 나거나 진짜 움직임을 놓친다.
**노이즈 바닥을 먼저 재고, 그 위에서 임계값을 정한다.**

**자동보정이 스스로 움직임을 만든다.** 노출이나 화이트밸런스가 조정되면 장면이
그대로여도 픽셀이 전부 바뀐다. 차분 기반 검출에서는 `aelock`·`awblock` 이
선택이 아니라 **전제**다.

**경보는 상태이지 사건이 아니다.** 한 프레임 넘었다고 켜고 다음 프레임에 끄면
깜빡인다 — 모듈 3 의 이력과 같은 문제이고, 여기서는 유지 시간으로 푼다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from perception import Observation

from .commands import LedCommand
from .features import SceneFeatures, hue_to_rgb
from .policy import Policy

CALM_HUE = 60      # 초록
ALARM_HUE = 0      # 빨강


@dataclass
class MotionDetector:
    """연속 프레임의 차이로 움직임 점수를 낸다.

    점수는 0~255 범위의 평균 절대차다. 해상도를 줄여서 재는 이유는 속도만이
    아니다 — 축소가 저역통과 역할을 해서 화소 단위 노이즈를 눌러준다.
    """

    width: int = 160
    height: int = 90
    _prev: np.ndarray | None = field(default=None, init=False, repr=False)

    def reset(self) -> None:
        self._prev = None

    def _prepare(self, image: np.ndarray) -> np.ndarray:
        import cv2

        small = cv2.resize(image, (self.width, self.height),
                           interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)

    def score(self, image: np.ndarray) -> float | None:
        """직전 프레임 대비 움직임 점수. 첫 프레임이면 None."""
        cur = self._prepare(image)
        prev, self._prev = self._prev, cur
        if prev is None:
            return None                      # 비교할 대상이 없다. 0 이 아니다.
        return float(np.abs(cur - prev).mean())


@dataclass
class MotionPolicy(Policy):
    """움직임이 감지되면 빨갛게 점멸, 조용하면 초록으로 은은하게.

    `hold_s` 동안은 새 움직임이 없어도 경보를 유지한다. 그러지 않으면 사람이
    잠깐 멈출 때마다 경보가 꺼졌다 켜졌다 한다.
    """

    threshold: float = 2.0
    hold_s: float = 2.0
    calm_level: int = 60
    alarm_level: int = 220
    alarm_interval_ms: int = 120
    detector: MotionDetector = field(default_factory=MotionDetector)

    _last_motion: float = field(default=0.0, init=False)
    _score: float | None = field(default=None, init=False)
    _seen: int = field(default=0, init=False)
    _fired: int = field(default=0, init=False)

    @property
    def alarming(self) -> bool:
        return (time.monotonic() - self._last_motion) < self.hold_s

    @property
    def last_score(self) -> float | None:
        return self._score

    @property
    def stats(self) -> dict[str, float]:
        return {"frames": self._seen, "triggers": self._fired,
                "last_score": self._score if self._score is not None else -1.0}

    def decide(
        self, features: SceneFeatures, observation: Observation | None = None
    ) -> LedCommand:
        if observation is not None and observation.image is not None:
            self._seen += 1
            score = self.detector.score(observation.image)
            self._score = score
            if score is not None and score >= self.threshold:
                self._last_motion = time.monotonic()
                self._fired += 1

        if self.alarming:
            return LedCommand("blink", rgb=hue_to_rgb(ALARM_HUE),
                              interval_ms=self.alarm_interval_ms,
                              level=self.alarm_level)
        return LedCommand("on", rgb=hue_to_rgb(CALM_HUE), level=self.calm_level)
