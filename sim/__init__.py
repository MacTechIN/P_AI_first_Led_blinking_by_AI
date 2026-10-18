"""시뮬레이션 계층 — 장비 없이 제어 루프를 닫는다 (`docs/simulation_plan.md`).

    world = SimWorld()
    loop = ControlLoop(SimSource(world), MirrorColorPolicy(), SimActuator(world))

소스와 액추에이터가 **같은 world 를 가리키는 것**이 전부다. 정책이 내린 명령이
장면에 그려지고, 다음 프레임에서 카메라가 그것을 본다.

시뮬레이터의 목적은 잘 되는 것을 흉내내는 것이 아니라 **기록된 실패를 재현하는
것**이다. 그래서 공통 저항 경쟁과 코어 포화는 기본으로 켜져 있다.
"""

from .actuator import SimActuator
from .faults import FAULTS, Fault, Rig, build_rig
from .panel import LedPanel
from .source import SimSource
from .world import SimWorld

__all__ = [
    "FAULTS", "Fault", "LedPanel", "Rig", "SimActuator", "SimSource", "SimWorld",
    "build_rig",
]
