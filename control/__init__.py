"""제어 계층 (L3 판단 + L1 구동) — VS-2 는 규칙 기반, VS-3 에서 VLM 으로 교체된다."""

from .actuator import Actuator, NullActuator, SerialLedActuator
from .commands import CommandError, LedCommand
from .features import SceneFeatures, classify_hue, extract
from .loop import ControlLoop, StepResult, summarize
from .policy import COLOR_RULES, ColorRulePolicy, Policy

__all__ = [
    "LedCommand",
    "CommandError",
    "SceneFeatures",
    "extract",
    "classify_hue",
    "Policy",
    "ColorRulePolicy",
    "COLOR_RULES",
    "Actuator",
    "NullActuator",
    "SerialLedActuator",
    "ControlLoop",
    "StepResult",
    "summarize",
]
