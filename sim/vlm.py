"""S-3 — 가상 VLM. 장면의 정답을 알고 있고, 그래서 일부러 틀릴 수 있다.

실물 서버는 GPU 하나에 `--parallel 1` 이라 교실 인원이 동시에 때릴 수 없다.
여기서는 장면의 색지를 바로 읽어 모델이 "맞혔을" 응답을 만든다. 추론이 아니라
**추론의 자리**다.

결함 주입이 이 클래스를 쓴다. 죽는 서버, 계약이 어긋난 응답, 3초 걸리는 추론을
전부 여기서 만든다 — 그것이 이 모듈의 진짜 목적이다.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from control.vlm import COLOURS, VlmClient, VlmError, validate

from .world import SimWorld

_HUE_NAME: list[tuple[int, int, str]] = [
    (0, 10, "red"), (11, 22, "orange"), (23, 33, "yellow"), (34, 85, "green"),
    (86, 100, "cyan"), (101, 130, "blue"), (131, 160, "purple"), (161, 179, "red"),
]


def colour_of(rgb: tuple[int, int, int]) -> str | None:
    """장면의 색지가 무슨 색인지. 모델이 제대로 답했다면 냈을 이름."""
    from control.colour import rgb_to_hsv

    px = np.uint8([[list(rgb)]])
    h, s, v = rgb_to_hsv(px)[0, 0]
    if s < 60 or v < 40:
        return None
    for lo, hi, name in _HUE_NAME:
        if lo <= h <= hi:
            return name if name in COLOURS else None
    return None


class SimVlmClient(VlmClient):
    """장면을 보고 답한다. 지연과 실패를 흉내낼 수 있다."""

    def __init__(
        self,
        world: SimWorld,
        *,
        latency_ms: float = 950.0,
        fail: bool = False,
        drift: float = 0.0,
        seed: int = 0,
    ) -> None:
        super().__init__(endpoint="sim://vlm")
        self.world = world
        self.latency_ms = latency_ms
        """실측 평균이 ~950ms 였다 (3B). 결함 주입이 이 값을 올린다."""
        self.fail = fail
        """True 면 모든 요청이 죽는다. `/health` 는 여전히 ok 라고 답할 것이다."""
        self.drift = drift
        """계약이 어긋난 응답을 낼 확률. 스키마는 통과하고 검증기가 거부한다."""
        self._rng = __import__("random").Random(seed)
        self.requests = 0

    def health(self) -> dict[str, Any]:
        """실물 서버를 따라 한다 — **죽어 있어도 model loaded 라고 답한다.**"""
        return {"status": "ok", "model": "sim-qwen2.5-vl-3b"}

    def ask(self, image: Any) -> tuple[dict[str, Any], float, str]:
        self.requests += 1
        t0 = time.perf_counter()
        time.sleep(self.latency_ms / 1000.0)
        latency = (time.perf_counter() - t0) * 1000.0

        if self.fail:
            raise VlmError("VLM 호출 실패: 서버가 응답하지 않는다")

        colour = colour_of(self.world.card_rgb)
        if colour is None:
            obj = {"action": "off", "colour": None, "reason": "아무것도 보이지 않음"}
        else:
            obj = {"action": "blink" if colour == "red" else "on",
                   "colour": colour, "reason": f"{colour} 물체"}

        if self.drift and self._rng.random() < self.drift:
            # 스키마는 통과하지만 검증기가 거부하는 모양 — ADR-0009 의 그 응답.
            obj = {"action": obj["action"], "reason": obj["reason"]}

        return validate(obj), latency, str(obj)
