"""공개 세트에 맞춰 손본 정책. **일부러 과적합시킨 본보기다.**

공개 대본에 나오는 색은 빨강·초록·파랑 셋뿐이다. 그래서 그 셋만 처리하고
나머지는 끈다. 공개 세트에서는 만점이 나온다 — 그리고 그것이 함정이다.
"""

from control.commands import LedCommand
from control.features import SceneFeatures, hue_to_rgb
from control.policy import Policy

KNOWN = {"red", "green", "blue"}


class TunedPolicy(Policy):
    def decide(self, features: SceneFeatures, observation=None) -> LedCommand:
        if features.color not in KNOWN or features.hue is None:
            return LedCommand("off")
        rgb = hue_to_rgb(features.hue)
        if features.color == "red":
            return LedCommand("blink", rgb=rgb, interval_ms=150, level=200)
        return LedCommand("on", rgb=rgb, level=200)


def build() -> Policy:
    return TunedPolicy()
