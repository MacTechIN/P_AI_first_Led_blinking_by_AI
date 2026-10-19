"""S-3 — 결함 주입. 기록된 실패를 하나씩 되살린다.

이 모듈이 시뮬레이션 계획의 중심이다. 잘 도는 시뮬레이터는 해피패스만 가르치고,
해피패스는 학습자가 막히는 순간에 아무 도움이 안 된다. 그래서 **플래그 하나가
실제로 겪은 실패 하나**를 되살리고, 과제는 "고쳐라" 가 아니라
**"무엇이 틀렸는지 측정으로 찾아내라"** 가 된다.

강사는 어떤 결함을 켰는지 말하지 않는다. 증상만 보고 원인을 좁히는 것이 실습이다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable

import numpy as np

from control.features import SceneFeatures, extract
from control.loop import ControlLoop
from control.policy import MirrorColorPolicy, Policy

from .actuator import SimActuator
from .panel import LedPanel
from .source import SimSource
from .world import SimWorld


@dataclass(frozen=True)
class Fault:
    """결함 하나. `cause` 와 `found_by` 는 정답이므로 공개하지 않는다."""

    name: str
    layer: str
    symptom: str
    """수강생이 보게 되는 것. 이것만 알려준다."""

    cause: str
    found_by: str
    record: str
    """원 기록 문서. 실습 뒤에 읽히면 된다."""


FAULTS: dict[str, Fault] = {
    "flat-frame": Fault(
        "flat-frame", "센서",
        "카메라가 열리고 프레임도 오는데 아무것도 검출되지 않는다",
        "모든 화소가 같은 값이다. 장치 파일은 있지만 데이터가 없다",
        "프레임의 표준편차를 본다 (perception.assert_frame_sane)",
        "docs/project_0_camtest.md",
    ),
    "autoexposure": Fault(
        "autoexposure", "센서",
        "LED 를 아무리 밝게 켜도 측정한 밝기가 움직이지 않는다",
        "자동 노출이 LED 의 기여를 매 프레임 되돌린다",
        "LED 소등/점등 차분을 보고, 노출·화이트밸런스를 고정해 다시 잰다",
        "docs/tech/notes/led-camera-detection.md",
    ),
    "stale-roi": Fault(
        "stale-roi", "특징",
        "화면에는 색지가 또렷한데 계속 '물체 없음' 이라고 한다",
        "관심영역이 엉뚱한 곳에 고정돼 있다. 장치는 멀쩡하다",
        "ROI 를 프레임 위에 그려 본다. 특징이 보는 화소를 직접 확인한다",
        "docs/labs/03-perception.md",
    ),
    "no-hysteresis": Fault(
        "no-hysteresis", "판단",
        "장면이 정지해 있는데 명령이 쉴 새 없이 나간다",
        "출력을 붙잡아 두지 않아 센서 노이즈가 그대로 명령이 된다",
        "정지 장면에서 스텝당 전송 횟수를 센다",
        "docs/tech/adr/0007-quantise-decisions-to-observation-quality.md",
    ),
    "polarity": Fault(
        "polarity", "구동",
        "빨강을 명령하면 청록이 켜지고, 흰색을 명령하면 꺼진다",
        "공통 애노드 반전이 적용되지 않았다. LOW 가 점등인 배선이다 (이득 보정 이전 상태)",
        "명령한 색과 **촬영한 색**을 대조한다. 통계만 보면 놓친다",
        "docs/tech/notes/rgb-led-calibration.md",
    ),
    "health-ok-dead": Fault(
        "health-ok-dead", "모델",
        "서버는 정상이라는데 LED 는 규칙 정책처럼만 움직인다",
        "모든 추론 요청이 실패하고 폴백이 그것을 완전히 가린다",
        "policy.stats 에서 failed 가 requests 와 같다 — 하나도 성공하지 못했다는 뜻이다",
        "docs/tech/notes/vlm-on-orin-nano.md",
    ),
    "schema-drift": Fault(
        "schema-drift", "모델",
        "모델이 답은 하는데 판단이 거의 반영되지 않는다",
        "응답이 스키마는 통과하고 검증기에서 거부된다. 계약이 두 곳에서 갈라졌다",
        "failed 가 requests 보다 **적다**. 전부 죽었으면 전송, 일부만 죽었으면 계약이다",
        "docs/tech/adr/0009-schema-and-validator-must-agree.md",
    ),
    "slow-vlm": Fault(
        "slow-vlm", "모델",
        "LED 가 색지를 몇 초씩 늦게 따라간다",
        "추론이 3초대인데 제어 주기는 수십 ms 다",
        "단계별 지연을 본다. decide 가 0ms 인데 결과가 늦다면 비동기 구조다",
        "docs/tech/adr/0008-vlm-runs-outside-the-control-loop.md",
    ),
}

VLM_FAULTS = {"health-ok-dead", "schema-drift", "slow-vlm"}
"""이 셋은 VLM 정책에서만 의미가 있다."""


# --------------------------------------------------------------------------
# 센서 계층의 결함
# --------------------------------------------------------------------------


class FlatFrameSource(SimSource):
    """모든 화소가 같은 값. 지원되지 않는 센서에 오버레이가 묶였을 때 본 것."""

    FLAT_VALUE = 4100 >> 8

    def _grab(self) -> np.ndarray:
        h, w = self.world.size[1], self.world.size[0]
        return np.full((h, w, 3), self.FLAT_VALUE, dtype=np.uint8)


class AutoExposureSource(SimSource):
    """프레임 평균 밝기를 매번 같은 값으로 되돌린다.

    LED 를 최대로 켜도 전체 평균이 +0.02 밖에 움직이지 않았던 실측을 재현한다.
    밝기를 특징으로 쓰면 아무것도 보이지 않는다.
    """

    def __init__(self, *a: Any, target: float | None = None, **kw: Any) -> None:
        super().__init__(*a, **kw)
        self._target = target

    def _grab(self) -> np.ndarray:
        frame = super()._grab()
        mean = float(frame.mean())
        if self._target is None:
            self._target = mean
        if mean > 1.0:
            frame = np.clip(frame.astype(np.float32) * (self._target / mean),
                            0, 255).astype(np.uint8)
        return frame


# --------------------------------------------------------------------------
# 조립
# --------------------------------------------------------------------------


@dataclass
class Rig:
    """한 벌의 실습 장비. 결함이 이미 들어가 있을 수도 있다."""

    world: SimWorld
    source: SimSource
    policy: Policy
    actuator: SimActuator
    extractor: Callable[..., SceneFeatures] = extract
    fault: Fault | None = None

    def loop(self) -> ControlLoop:
        return ControlLoop(self.source, self.policy, self.actuator, self.extractor)

    def briefing(self) -> str:
        """수강생에게 주는 것. **원인은 들어 있지 않다.**"""
        if self.fault is None:
            return "이 장비는 정상이라고 알려져 있다."
        return f"증상: {self.fault.symptom}"

    def reveal(self) -> str:
        if self.fault is None:
            return "주입된 결함 없음."
        f = self.fault
        return (f"결함 {f.name} ({f.layer} 계층)\n"
                f"  원인   {f.cause}\n"
                f"  찾는 법 {f.found_by}\n"
                f"  원 기록 {f.record}")


def build_rig(
    fault: str | None = None,
    *,
    policy: str = "mirror",
    world: SimWorld | None = None,
    seed: int = 0,
    vlm_latency_ms: float = 120.0,
    tape: str | Any = None,
    tape_speed: float = 1.0,
) -> Rig:
    """결함 하나를 넣은 장비를 조립한다. `fault=None` 이면 정상 장비.

    `policy="tape"` 는 기록해 둔 실제 모델 응답을 재생한다 (S-4). 서버가 없는
    교실에서 VLM 정책을 그대로 돌리는 방법이다.
    """
    if fault is not None and fault not in FAULTS:
        raise ValueError(f"모르는 결함: {fault!r}  (가능: {', '.join(FAULTS)})")

    spec = FAULTS.get(fault) if fault else None
    world = world or SimWorld()
    if fault in VLM_FAULTS:
        policy = "vlm"

    if fault == "polarity":
        # 이득 보정도 함께 되돌린다. 극성 버그는 이득 보정보다 **먼저** 있었고,
        # 기록된 증상(빨강→청록)은 보정 전 상태에서 관측된 것이다. 지금 이득을
        # 그대로 두고 극성만 뒤집으면 노랑이 나와 기록과 맞지 않는다 — 재 보고 알았다.
        world.panel = LedPanel(polarity_fixed=False, gains=(255, 255, 255))

    src_cls: type[SimSource] = SimSource
    if fault == "flat-frame":
        src_cls = FlatFrameSource
    elif fault == "autoexposure":
        src_cls = AutoExposureSource
    source = src_cls(world, seed=seed)

    extractor: Callable[..., SceneFeatures] = extract
    if fault == "stale-roi":
        # 예전 배치에서 LED 가 있던 자리. 지금은 아무것도 없다.
        extractor = partial(extract, roi=(0.70, 0.62, 0.95, 0.92))

    pol: Policy
    if policy == "tape":
        from control.vlm import VlmPolicy

        from .replay import ReplayVlmClient, Tape

        loaded = tape if hasattr(tape, "entries") else Tape.load(tape)
        pol = VlmPolicy(ReplayVlmClient(loaded, speed=tape_speed),
                        fallback=MirrorColorPolicy(), min_interval_s=0.0)
    elif policy == "vlm":
        from control.vlm import VlmPolicy

        from .vlm import SimVlmClient

        client = SimVlmClient(
            world,
            latency_ms=3100.0 if fault == "slow-vlm" else vlm_latency_ms,
            fail=(fault == "health-ok-dead"),
            drift=0.8 if fault == "schema-drift" else 0.0,
            seed=seed,
        )
        pol = VlmPolicy(client, fallback=MirrorColorPolicy(), min_interval_s=0.0)
    elif fault == "no-hysteresis":
        pol = MirrorColorPolicy(hue_step=1, level_step=1)
    else:
        pol = MirrorColorPolicy()

    return Rig(world, source, pol, SimActuator(world), extractor, spec)
