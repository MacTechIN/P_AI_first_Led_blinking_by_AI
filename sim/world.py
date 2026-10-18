"""S-1 — 가상 현장. 액추에이터와 카메라가 공유하는 단 하나의 상태.

이 모듈이 루프를 닫는다. 정책이 내린 명령을 `apply()` 로 받아 두고, 카메라가
`render()` 를 부르면 **그 명령이 만든 빛을 장면에 그려 넣는다.** 그래서 다음
프레임에서 LED 가 실제로 보인다.

하드웨어 없이도 제어 루프 전체가 관측 가능해지는 지점이 여기다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from control.commands import LedCommand
from perception.sources import Painter, patch

from .panel import BLOOM_KNEE, GLOW_SIGMA, LedPanel

DEFAULT_CARD_BOX = (0.26, 0.28, 0.66, 0.72)
"""색지의 위치. 특징 추출의 기본 ROI(가운데 60%) 안에 들어간다."""

DEFAULT_LED_AT = (0.88, 0.5)
"""LED 의 위치. **기본값은 ROI 밖이다.**

안으로 옮기면 LED 의 빛이 다음 프레임의 특징에 섞인다. 다만 **옮기는 것만으로는
판정이 뒤집히지 않는다** — 재 보고 알았다. 기본 반경(24px)에서 LED 가 ROI 에서
차지하는 비율은 `MIN_COVERAGE` 에 못 미치고, 코어는 흰색으로 포화해 채도
문턱에서 걸러지며, 남은 테두리는 색지(49%)에 면적으로 진다.

자기 출력을 먹는 현상은 **반경 60px 이상 + ROI 안** 에서 비로소 나타난다.
그때는 색지를 치워도 시스템이 계속 같은 색을 보고한다. 자기가 켠 불을 보고
있기 때문이다. 재현은 `./host/sim_demo.py --led-in-roi --led-radius 70`.
"""


@dataclass
class SimWorld:
    """장면 + LED. 액추에이터가 쓰고 카메라가 읽는다."""

    size: tuple[int, int] = (640, 480)
    card_rgb: tuple[int, int, int] = (220, 40, 40)
    card_box: tuple[float, float, float, float] = DEFAULT_CARD_BOX
    background_rgb: tuple[int, int, int] = (28, 28, 32)

    led_at: tuple[float, float] = DEFAULT_LED_AT
    led_radius_px: int = 24
    panel: LedPanel = field(default_factory=LedPanel)

    clock: Callable[[], float] = time.monotonic
    """시간 공급원. 시험에서는 고정 함수를 넣어 점멸 위상을 결정적으로 만든다."""

    command: LedCommand = field(default_factory=lambda: LedCommand("off"))
    commands: int = 0

    def apply(self, cmd: LedCommand) -> None:
        """액추에이터가 부른다. 명령은 즉시 빛이 된다."""
        self.command = cmd
        self.commands += 1

    def set_card(self, rgb: tuple[int, int, int]) -> None:
        """장면의 입력을 바꾼다. S-2 의 장면 대본이 이 자리를 대신한다."""
        self.card_rgb = rgb

    # --- 렌더링 ---

    def _background(self) -> Painter:
        return patch(self.card_rgb, self.background_rgb, self.card_box, self.size)

    def emitted(self, t: float | None = None) -> tuple[int, int, int]:
        """지금 LED 가 내는 색. 점멸 중이면 꺼진 위상에서 (0,0,0)."""
        return self.panel.emit(self.command, self.clock() if t is None else t)

    def render(self, seq: int, t: float | None = None) -> np.ndarray:
        img = self._background()(seq)
        return self.paint_led(img, self.emitted(t))

    def paint_led(self, img: np.ndarray, emitted: tuple[int, int, int]) -> np.ndarray:
        """LED 를 장면에 그려 넣는다. 중심은 포화해 흰색이 된다."""
        if max(emitted) == 0:
            return img

        h, w = img.shape[:2]
        cx, cy = int(self.led_at[0] * w), int(self.led_at[1] * h)
        r = max(1, self.led_radius_px)
        reach = int(r * 2.4)

        x0, x1 = max(0, cx - reach), min(w, cx + reach + 1)
        y0, y1 = max(0, cy - reach), min(h, cy + reach + 1)
        if x0 >= x1 or y0 >= y1:
            return img

        yy, xx = np.ogrid[y0:y1, x0:x1]
        u = np.sqrt((xx - cx) ** 2.0 + (yy - cy) ** 2.0) / r
        glow = np.exp(-(u**2.0) / GLOW_SIGMA)

        colour = glow[..., None] * np.asarray(emitted, dtype=np.float32)
        core = np.clip((glow - BLOOM_KNEE) / (1.0 - BLOOM_KNEE), 0.0, 1.0)
        bloom = core * (max(emitted) / 255.0) * 255.0

        out = img[y0:y1, x0:x1].astype(np.float32) + colour + bloom[..., None]
        img[y0:y1, x0:x1] = np.clip(out, 0, 255).astype(np.uint8)
        return img

    def describe(self) -> dict[str, object]:
        return {
            "size": self.size,
            "card_rgb": self.card_rgb,
            "led_at": self.led_at,
            "commands": self.commands,
            **self.panel.describe(),
        }
