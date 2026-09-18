"""VS-4 — 역량 계약. 액추에이터를 **코드가 아니라 데이터로** 선언한다.

정의서는 "프로그램 불필요" 와 "액추에이터 구성은 사용자가 입력" 을 요구한다.
그러려면 모델이 무엇을 할 수 있는지 **선언된 데이터**로 알아야 하고, 새 장치를
붙이는 일이 파이썬 수정이 아니라 선언 추가여야 한다.

세 가지가 한 선언에서 파생된다:

1. 모델에게 주는 도구 스키마 (µ4.2) — 수기 동기화가 없으므로 어긋날 수 없다
2. 명령 검증기 (µ4.3) — 선언에 없는 것은 통과하지 못한다
3. 전송 문자열 (`wire` 템플릿) — 그래서 장치 추가에 코드가 필요 없다

합격 판정은 `test_adding_a_device_needs_no_code` 다. JSON 파일 하나를 놓는 것만으로
모델이 새 장치를 쓸 수 있어야 한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "capabilities"


class ContractError(ValueError):
    """선언을 위반했다. 이 예외를 넘어선 명령은 액추에이터에 닿지 않는다."""


@dataclass(frozen=True)
class ArgSpec:
    """명령 인자 하나의 계약."""

    name: str
    type: str                      # int | float | enum | bool
    description: str = ""
    minimum: float | None = None
    maximum: float | None = None
    choices: tuple[str, ...] = ()
    default: Any = None

    @classmethod
    def parse(cls, name: str, raw: dict[str, Any]) -> "ArgSpec":
        t = raw.get("type", "int")
        if t not in ("int", "float", "enum", "bool"):
            raise ContractError(f"{name}: 알 수 없는 type {t!r}")
        if t == "enum" and not raw.get("choices"):
            raise ContractError(f"{name}: enum 에는 choices 가 필요하다")
        return cls(
            name=name, type=t, description=raw.get("description", ""),
            minimum=raw.get("min"), maximum=raw.get("max"),
            choices=tuple(raw.get("choices", ())), default=raw.get("default"),
        )

    def coerce(self, value: Any) -> Any:
        """값을 계약에 맞춰 변환·검사한다. 위반이면 ContractError."""
        if self.type == "bool":
            if not isinstance(value, bool):
                raise ContractError(f"{self.name}: bool 이어야 한다 ({value!r})")
            return value
        if self.type == "enum":
            if value not in self.choices:
                raise ContractError(
                    f"{self.name}: {list(self.choices)} 중 하나여야 한다 ({value!r})"
                )
            return value

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ContractError(f"{self.name}: 숫자여야 한다 ({value!r})")
        v = int(value) if self.type == "int" else float(value)
        if self.minimum is not None and v < self.minimum:
            raise ContractError(f"{self.name}: {self.minimum} 이상이어야 한다 ({v})")
        if self.maximum is not None and v > self.maximum:
            raise ContractError(f"{self.name}: {self.maximum} 이하여야 한다 ({v})")
        return v

    def json_schema(self) -> dict[str, Any]:
        if self.type == "enum":
            out: dict[str, Any] = {"type": "string", "enum": list(self.choices)}
        elif self.type == "bool":
            out = {"type": "boolean"}
        else:
            out = {"type": "integer" if self.type == "int" else "number"}
            if self.minimum is not None:
                out["minimum"] = self.minimum
            if self.maximum is not None:
                out["maximum"] = self.maximum
        if self.description:
            out["description"] = self.description
        return out


@dataclass(frozen=True)
class CommandSpec:
    name: str
    wire: str
    """전송 문자열 템플릿. `{arg}` 가 치환된다. 줄바꿈으로 여러 문장을 보낸다.

    이것이 있어서 장치 추가에 코드가 필요 없다. 없으면 장치마다 파이썬
    어댑터를 써야 하고, 그 순간 "프로그램 불필요" 가 깨진다.
    """
    description: str = ""
    args: dict[str, ArgSpec] = field(default_factory=dict)

    @classmethod
    def parse(cls, name: str, raw: dict[str, Any]) -> "CommandSpec":
        if "wire" not in raw:
            raise ContractError(f"{name}: wire 템플릿이 없다")
        return cls(
            name=name, wire=raw["wire"], description=raw.get("description", ""),
            args={k: ArgSpec.parse(k, v) for k, v in raw.get("args", {}).items()},
        )

    def render(self, args: dict[str, Any]) -> list[str]:
        """검증된 인자로 전송 문장들을 만든다."""
        return [ln for ln in self.wire.format(**args).split("\n") if ln.strip()]


@dataclass(frozen=True)
class Device:
    id: str
    kind: str
    transport: dict[str, Any]
    commands: dict[str, CommandSpec]
    description: str = ""
    status: str = "wired"
    """`planned` 이면 아직 물리적으로 붙지 않은 장치다.

    선언은 존재하고 스키마에도 나타나지만 전송로가 `null` 이라 명령이 어디에도
    가지 않는다. 계약 구조를 검증하려고 실물보다 선언이 먼저 존재할 수 있으므로,
    그 상태를 선언 안에 적어 둔다 — 파일만 보고 동작한다고 오해하지 않도록.
    """

    @property
    def wired(self) -> bool:
        return self.status != "planned"

    @classmethod
    def parse(cls, raw: dict[str, Any]) -> "Device":
        for key in ("id", "kind", "transport", "commands"):
            if key not in raw:
                raise ContractError(f"선언에 {key} 가 없다")
        status = raw.get("status", "wired")
        if status == "planned" and raw["transport"].get("type") != "null":
            raise ContractError(
                f"{raw['id']}: status=planned 인데 전송로가 null 이 아니다. "
                "미배선 장치가 실제 포트로 명령을 보내면 안 된다"
            )
        return cls(
            id=raw["id"], kind=raw["kind"], transport=raw["transport"],
            description=raw.get("description", ""), status=status,
            commands={k: CommandSpec.parse(k, v) for k, v in raw["commands"].items()},
        )


@dataclass(frozen=True)
class Call:
    """검증을 통과한 호출. 이 형태로만 액추에이터에 닿는다."""

    device: str
    command: str
    args: dict[str, Any] = field(default_factory=dict)

    def describe(self) -> str:
        a = " ".join(f"{k}={v}" for k, v in self.args.items())
        return f"{self.device}.{self.command}({a})".replace("()", "()")


class Registry:
    """선언들의 모음. 도구 스키마와 검증기가 여기서 나온다."""

    def __init__(self, devices: Iterable[Device]) -> None:
        self.devices = {d.id: d for d in devices}

    # --- 적재 ---

    @classmethod
    def load(cls, directory: str | Path = DEFAULT_DIR) -> "Registry":
        path = Path(directory)
        if not path.is_dir():
            raise ContractError(f"선언 디렉터리가 없다: {path}")
        devices = []
        for f in sorted(path.glob("*.json")):
            try:
                devices.append(Device.parse(json.loads(f.read_text())))
            except (ValueError, ContractError) as e:
                raise ContractError(f"{f.name}: {e}") from e
        if not devices:
            raise ContractError(f"선언이 하나도 없다: {path}")
        return cls(devices)

    # --- µ4.2 도구 스키마 자동 생성 ---

    def tool_schema(self) -> dict[str, Any]:
        """모델에게 줄 JSON 스키마. 선언에서 파생되므로 수기 동기화가 없다."""
        options = []
        for dev in self.devices.values():
            for cmd in dev.commands.values():
                props: dict[str, Any] = {
                    "device": {"type": "string", "enum": [dev.id]},
                    "command": {"type": "string", "enum": [cmd.name]},
                }
                if cmd.args:
                    props["args"] = {
                        "type": "object",
                        "properties": {n: a.json_schema() for n, a in cmd.args.items()},
                        "required": list(cmd.args),
                        "additionalProperties": False,
                    }
                options.append({
                    "type": "object",
                    "description": f"{dev.description} — {cmd.description}".strip(" —"),
                    "properties": props,
                    "required": ["device", "command"] + (["args"] if cmd.args else []),
                    "additionalProperties": False,
                })
        return {"oneOf": options}

    def describe(self) -> str:
        """프롬프트에 넣을 사람이 읽는 요약."""
        lines = []
        for dev in self.devices.values():
            mark = "" if dev.wired else " [not wired yet]"
            lines.append(f"- {dev.id} ({dev.kind}){mark}: {dev.description}")
            for cmd in dev.commands.values():
                args = ", ".join(
                    f"{n} {a.type}"
                    + (f" {a.minimum}..{a.maximum}" if a.minimum is not None else "")
                    + (f" {list(a.choices)}" if a.choices else "")
                    for n, a in cmd.args.items()
                )
                lines.append(f"    {cmd.name}({args}) — {cmd.description}")
        return "\n".join(lines)

    # --- µ4.3 검증 ---

    def validate(self, raw: Any) -> Call:
        """모델이 낸 호출을 계약에 비춘다. 위반이면 ContractError."""
        if not isinstance(raw, dict):
            raise ContractError(f"객체가 아니다: {type(raw).__name__}")

        dev = self.devices.get(raw.get("device"))
        if dev is None:
            raise ContractError(
                f"알 수 없는 장치: {raw.get('device')!r} "
                f"(있는 것: {sorted(self.devices)})"
            )
        cmd = dev.commands.get(raw.get("command"))
        if cmd is None:
            raise ContractError(
                f"{dev.id} 에 없는 명령: {raw.get('command')!r} "
                f"(있는 것: {sorted(dev.commands)})"
            )

        given = raw.get("args") or {}
        if not isinstance(given, dict):
            raise ContractError("args 는 객체여야 한다")
        unknown = set(given) - set(cmd.args)
        if unknown:
            raise ContractError(f"{cmd.name} 에 없는 인자: {sorted(unknown)}")

        args: dict[str, Any] = {}
        for name, spec in cmd.args.items():
            if name in given:
                args[name] = spec.coerce(given[name])
            elif spec.default is not None:
                args[name] = spec.coerce(spec.default)
            else:
                raise ContractError(f"{cmd.name}: {name} 가 빠졌다")
        return Call(dev.id, cmd.name, args)

    def render(self, call: Call) -> list[str]:
        """검증된 호출 → 전송 문장들."""
        return self.devices[call.device].commands[call.command].render(call.args)

    def transport_of(self, call: Call) -> dict[str, Any]:
        return self.devices[call.device].transport


class ContractActuator:
    """검증된 호출을 선언된 전송로로 보낸다.

    장치별 파이썬 어댑터가 없다. 전송 방식(`transport.type`)마다 하나씩만 있고,
    장치가 늘어도 이 클래스는 그대로다 — 그것이 VS-4 의 요점이다.
    """

    def __init__(self, registry: Registry, *, verbose: bool = False) -> None:
        self.registry = registry
        self.verbose = verbose
        self._ports: dict[str, Any] = {}
        self.sent: list[tuple[str, str]] = []
        """(장치, 문장) 기록. 시험과 결정 로그(µ6.4)에 쓴다."""

    def apply(self, call: Call) -> list[str]:
        lines = self.registry.render(call)
        transport = self.registry.transport_of(call)
        kind = transport.get("type")
        if kind == "serial":
            self._send_serial(transport, call.device, lines)
        elif kind == "null":
            for ln in lines:
                self.sent.append((call.device, ln))
        else:
            raise ContractError(f"지원하지 않는 전송 방식: {kind!r}")
        return lines

    def _send_serial(self, transport: dict[str, Any], device: str,
                     lines: list[str]) -> None:
        port = transport["port"]
        conn = self._ports.get(port)
        if conn is None:
            import sys
            from pathlib import Path as _P

            sys.path.insert(0, str(_P(__file__).resolve().parent.parent / "host"))
            from blink import Arduino

            conn = Arduino(port, verbose=self.verbose)
            self._ports[port] = conn
        for ln in lines:
            conn.send(ln)
            self.sent.append((device, ln))

    def close(self) -> None:
        for conn in self._ports.values():
            conn.close()
        self._ports.clear()

    def __enter__(self) -> "ContractActuator":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
