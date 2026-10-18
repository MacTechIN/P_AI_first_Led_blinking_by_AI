"""S-1 — 가상 RGB LED 의 발광 모델.

명령이 실제로 어떤 빛이 되는지를 재현한다. 두 단계를 거친다.

1. **펌웨어** — `dutyFor()` 와 같은 정수 연산으로 듀티를 만든다.
   `값 × level/255 × gain/255`, 각 단계마다 버림.
2. **하드웨어** — 공통 전류 제한 저항 하나를 셋이 나눠 쓰는 경쟁을 모사한다.

2번이 이 모듈의 존재 이유다. 보정된 LED 를 흉내내는 것은 쉽지만 쓸모가 없다.
교재가 가르치는 것은 `RGB 255 255 0` 이 왜 순수 빨강으로 나왔는가이고,
시뮬레이터가 그것을 재현하지 못하면 해피패스만 가르치게 된다
(`docs/tech/notes/rgb-led-calibration.md`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from control.commands import LedCommand

GAIN_R, GAIN_G, GAIN_B = 120, 200, 255
"""펌웨어 `rgb_led.ino` 의 GAIN_* 와 일치해야 한다.

저항을 채널마다 하나씩 두는 배선으로 바꾸면 펌웨어와 여기 둘 다 255 로 되돌린다.
"""

COMPETITION_EXPONENT = 3.46
DIE_STRENGTH = (1.0, 0.109, 0.0118)
"""전류 경쟁의 두 계수. **실측에서 맞춘 값이다** — 아래 유도를 보라.

순방향 전압이 낮은 다이가 이긴다(적 < 녹 < 청). 발광량을

    raw_i = (duty_i / 255) ** EXPONENT × STRENGTH_i

로 두고, 셋이 고정된 전류를 나눠 갖는다고 본다. 계수는 교정 기록의 검증 실험
세 점에서 풀었다(모두 B=0, G 듀티 255 고정):

    duty (255, 255) → 색조  0   관측 → 초록 기여 거의 0
    duty (120, 255) → 색조 38
    duty ( 60, 255) → 색조 58

색조에서 발광비를 되돌리면 r/g = 9.21 × (d_r/d_g)^3.46 이 세 점을 모두 지난다.
그래서 STRENGTH 의 적:녹 = 1 : 1/9.21 = 0.109 이다.

**청색 계수는 실측이 아니라 외삽이다.** 기록에 남은 것은 순서(적>녹>청)와
"청록이 초록으로 나왔다" 는 사실뿐이라, 적:녹과 같은 비율을 한 칸 더 적용했다.
"""

GLOW_SIGMA = 0.35
BLOOM_KNEE = 0.72
"""중심부가 흰색으로 포화하는 지점.

실물에서 **LED 코어는 어떤 색이든 카메라를 포화시켜 흰색이 된다.** 색 정보는
주변부에만 남는다. 이것을 재현해야 "포화 화소를 빼야 한다" 는 교훈이 실습에서
성립한다. 재현하지 않으면 그 단계가 왜 필요한지 보여줄 방법이 없다.
"""


@dataclass
class LedPanel:
    """명령 → 카메라가 볼 색. 기본값은 **현재 실물 배선** 그대로다."""

    gains: tuple[int, int, int] = (GAIN_R, GAIN_G, GAIN_B)
    strength: tuple[float, float, float] = DIE_STRENGTH
    exponent: float = COMPETITION_EXPONENT

    shared_resistor: bool = True
    """False 면 채널마다 저항이 있는 **올바른 배선**이 된다. 경쟁이 사라진다."""

    polarity_fixed: bool = True
    """펌웨어가 공통 애노드 반전을 적용했는가.

    False 로 두면 극성 버그가 되살아난다 — `RGB 255 0 0` 이 청록으로, 흰색이
    소등으로 나온다. S-3 의 결함 주입이 이 스위치를 쓴다.
    """

    def duty(self, cmd: LedCommand) -> tuple[int, int, int]:
        """펌웨어 `dutyFor()` 와 같은 정수 연산. 단계마다 버린다."""
        out = []
        for value, gain in zip(cmd.rgb, self.gains):
            out.append(value * cmd.level // 255 * gain // 255)
        return (out[0], out[1], out[2])

    def is_lit(self, cmd: LedCommand, t: float) -> bool:
        """점멸 위상. 펌웨어의 `millis()` 토글과 같은 규칙이다."""
        if cmd.mode == "off":
            return False
        if cmd.mode == "on":
            return True
        return int(t * 1000.0 / cmd.interval_ms) % 2 == 0

    def compete(self, duty: tuple[int, int, int]) -> tuple[int, int, int]:
        """공통 저항을 나눠 쓰는 세 다이의 경쟁."""
        if max(duty) == 0:
            return (0, 0, 0)
        if not self.shared_resistor:
            return duty

        raw = [(d / 255.0) ** self.exponent * s for d, s in zip(duty, self.strength)]
        total = sum(raw)
        if total <= 0.0:
            return (0, 0, 0)

        # 저항 하나가 허용하는 총 전류는 가장 세게 켜진 채널이 정한다.
        budget = max(duty) / 255.0
        out = [int(round(r / total * budget * 255.0)) for r in raw]
        return (out[0], out[1], out[2])

    def emit(self, cmd: LedCommand, t: float) -> tuple[int, int, int]:
        """시각 t 에 카메라가 볼 색."""
        if not self.is_lit(cmd, t):
            return (0, 0, 0)
        d = self.duty(cmd)
        if not self.polarity_fixed:
            d = (255 - d[0], 255 - d[1], 255 - d[2])
        return self.compete(d)

    def describe(self) -> dict[str, object]:
        return {
            "gains": self.gains,
            "shared_resistor": self.shared_resistor,
            "polarity_fixed": self.polarity_fixed,
        }
