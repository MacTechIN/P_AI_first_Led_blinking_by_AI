"""제어 계층 (L3 판단 + L1 구동) — VS-2 는 규칙 기반, VS-3 에서 VLM 으로 교체된다."""

from .actuator import Actuator, NullActuator, SerialLedActuator
from .commands import CommandError, LedCommand
from .direction import DEFAULT_MARGIN, ZONE_HUE, DirectionPolicy, zone_of
from .evaluate import Case, CaseResult, GoldenError, Report, load_cases, matches
from .direction import DEFAULT_MARGIN, ZONE_HUE, DirectionPolicy, zone_of
from .evaluate import run as run_golden
from .features import SceneFeatures, classify_hue, extract, hue_to_rgb
from .loop import ControlLoop, StepResult, summarize
from .policy import COLOR_RULES, ColorRulePolicy, MirrorColorPolicy, Policy
from .capability import (
    ArgSpec,
    Call,
    CommandSpec,
    ContractActuator,
    ContractError,
    Device,
    Registry,
)
from .vlm import (
    ContractVlmClient,
    COLOURS,
    RESPONSE_SCHEMA,
    SYSTEM_PROMPT,
    VlmClient,
    VlmDecision,
    VlmError,
    VlmPolicy,
    to_command,
    validate,
)

__all__ = [
    "LedCommand",
    "CommandError",
    "SceneFeatures",
    "extract",
    "classify_hue",
    "hue_to_rgb",
    "Policy",
    "ColorRulePolicy",
    "MirrorColorPolicy",
    "COLOR_RULES",
    "Actuator",
    "NullActuator",
    "SerialLedActuator",
    "ControlLoop",
    "StepResult",
    "summarize",
    "VlmPolicy",
    "VlmClient",
    "VlmDecision",
    "VlmError",
    "validate",
    "to_command",
    "RESPONSE_SCHEMA",
    "SYSTEM_PROMPT",
    "COLOURS",
    "Registry",
    "Device",
    "CommandSpec",
    "ArgSpec",
    "Call",
    "ContractError",
    "ContractActuator",
    "ContractVlmClient",
    "Case",
    "CaseResult",
    "Report",
    "GoldenError",
    "load_cases",
    "matches",
    "run_golden",
    "DirectionPolicy",
    "zone_of",
    "ZONE_HUE",
    "DEFAULT_MARGIN",
]
