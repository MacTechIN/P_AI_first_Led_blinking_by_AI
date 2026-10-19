"""예제 3 — 장면 판단. **규칙으로 쓸 수 없는 질문**을 다루는 법.

앞의 두 예제는 규칙 편에 섰다. 위치는 산술이고(예제 1), 임계값은 재서 정한다
(예제 2). 이 예제는 반대쪽이다 — 규칙을 **쓸 수 없는** 질문이 실제로 있고,
그때 치러야 하는 값이 무엇인지가 주제다.

## 먼저 규칙을 써 본다

건너뛰기 쉬운 단계이고, 건너뛰면 모델이 필요한지 영영 알 수 없다. 질문을
하나 고르고 규칙으로 적어 본다. 적을 수 있으면 규칙으로 한다. 끝.

"작업대가 정리되어 있는가" 를 적어 보면 막히는 지점이 분명하다. '정리' 는
물건의 **개수**가 아니고(정리된 책상에도 물건은 많다), **위치의 분산**도
아니며(줄 맞춘 어수선함이 있다), **빈 면적 비율**도 아니다(빈 책상은 정리된
것이 아니라 비어 있는 것이다). 셋 다 반례가 즉시 나온다 — 그래서 적을 수 없다.

## 치러야 하는 값

규칙은 **읽어서 검증**된다. 모델은 그럴 수 없다. 그래서 세 가지가 따라온다.

1. **출력을 좁힌다.** 자유 문장이 아니라 스키마로 받는다. 모델이 말할 수 있는
   것을 미리 정하지 않으면 액추에이터에 닿는 것을 통제할 수 없다 (ADR-0003).
2. **기권을 허용한다.** `uncertain` 이 합법이어야 모델이 지어내지 않는다.
3. **골든셋이 필수가 된다.** 눈으로 확인할 수 없으므로 사례로 고정하는 수밖에
   없고, **답이 프레임마다 흔들린다는 것을 먼저 재 봐야** 한다.

마지막이 이 예제의 실측 과제다 — `host/measure_scene.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from perception import Observation

from .commands import LedCommand
from .features import SceneFeatures, hue_to_rgb
from .policy import Policy

VERDICTS = ("tidy", "cluttered", "uncertain")
"""모델이 말할 수 있는 전부. `uncertain` 이 없으면 모델은 지어낸다."""

VERDICT_HUE = {"tidy": 60, "cluttered": 0}
"""정돈 초록 · 어수선 빨강. `uncertain` 은 색을 주지 않는다 — 아래 참조."""

SCENE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": list(VERDICTS)},
        "evidence": {"type": "string", "maxLength": 80},
    },
    "required": ["verdict", "evidence"],
    "additionalProperties": False,
}

NO_ABSTAIN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["tidy", "cluttered"]},
        "evidence": {"type": "string", "maxLength": 80},
    },
    "required": ["verdict", "evidence"],
    "additionalProperties": False,
}
"""기권을 뺀 스키마. **일부러 잘못 만든 것**이고, 비교 측정에만 쓴다.

"탈출구가 없으면 모델은 답을 지어낸다" 는 이 저장소의 주장을 숫자로 확인하려면
지어낼 수밖에 없는 상황을 한 번 만들어 봐야 한다 (`host/measure_scene.py --no-abstain`).
"""

SCENE_PROMPT = (
    "You judge whether a work area is tidy. Answer ONLY with JSON matching the "
    "schema. verdict is one of tidy, cluttered, uncertain. Use uncertain when the "
    "image does not show a work area clearly. evidence is a short phrase naming "
    "what you actually see, not a restatement of the verdict."
)


class SceneError(ValueError):
    """장면 판단 응답이 계약을 어겼다."""


def validate_scene(obj: Any, allowed: tuple[str, ...] = VERDICTS) -> dict[str, str]:
    """스키마를 믿지 않고 한 번 더 본다 (ADR-0009 와 같은 이유)."""
    if not isinstance(obj, dict):
        raise SceneError(f"객체가 아니다: {type(obj).__name__}")
    verdict = obj.get("verdict")
    if verdict not in allowed:
        raise SceneError(f"알 수 없는 verdict: {verdict!r}")
    return {"verdict": verdict, "evidence": str(obj.get("evidence", ""))[:80]}


def try_rule(features: SceneFeatures) -> None:
    """**이 함수는 일부러 아무것도 하지 않는다.**

    "정리되어 있는가" 를 특징에서 계산하려는 시도가 여기 있어야 하는데, 쓸 수
    있는 식이 없다. 비어 있다는 사실 자체가 예제 3 의 출발점이므로 지우지
    않고 둔다 — 지우면 "왜 모델을 쓰는가" 에 답할 자리가 사라진다.

    반례 셋: 개수(정돈된 책상에도 물건은 많다), 분산(줄 맞춘 어수선함),
    빈 면적(빈 책상은 정리된 것이 아니라 비어 있는 것이다).
    """
    return None


@dataclass
class ScenePolicy(Policy):
    """장면 판정을 LED 로 옮긴다. 판정이 없으면 **직전 상태를 유지한다.**

    `uncertain` 과 "아직 답이 없음" 을 같게 다룬다. 둘 다 "모른다" 이고,
    모를 때 불을 끄면 **정돈됐다는 신호와 구별되지 않는다.**
    """

    level: int = 200
    hold_blink_ms: int = 400
    _last: LedCommand | None = field(default=None, init=False)
    verdicts: list[str] = field(default_factory=list)

    def decide(
        self, features: SceneFeatures, observation: "Observation | None" = None
    ) -> LedCommand:
        if try_rule(features) is not None:            # 규칙이 생기면 규칙이 이긴다
            raise AssertionError("규칙이 생겼다면 모델을 쓸 이유가 없다")
        return self._last or LedCommand("off")

    def apply_verdict(self, verdict: str) -> LedCommand:
        """모델 판정을 명령으로. 정책 바깥에서 비동기로 도착한다 (ADR-0008)."""
        self.verdicts.append(verdict)
        hue = VERDICT_HUE.get(verdict)
        if hue is None:
            return self._last or LedCommand("off")    # 모르면 유지
        cmd = LedCommand("on" if verdict == "tidy" else "blink",
                         rgb=hue_to_rgb(hue),
                         interval_ms=self.hold_blink_ms, level=self.level)
        self._last = cmd
        return cmd

    @property
    def stability(self) -> float:
        """같은 질문에 같은 답을 한 비율. 1.0 이면 흔들리지 않았다."""
        if not self.verdicts:
            return 0.0
        top = max(set(self.verdicts), key=self.verdicts.count)
        return self.verdicts.count(top) / len(self.verdicts)
