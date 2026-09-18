"""VS-3 — VLM 판단. 모델이 장면을 해석하고 LED 명령을 정한다.

두 가지 원칙이 구조를 결정한다.

**1. 제어 루프를 막지 않는다 (ADR-0008).**
VLM 추론은 약 950ms 이고 제어 루프는 34ms 다. 동기로 부르면 루프가 1fps 로
떨어진다. 그래서 추론은 작업 스레드에서 돌고, `decide()` 는 **가장 최근에 완성된
판단을 즉시 반환**한다. 아직 판단이 없으면 폴백 정책이 답한다.

**2. 모델 출력은 검증을 통과해야 액추에이터에 닿는다 (ADR-0003).**
JSON 스키마를 디코딩 단계에서 강제하고(사후 파싱은 반드시 깨진다), 그 뒤에도
`LedCommand` 생성자가 범위를 검사하며, 마지막으로 펌웨어가 한 번 더 막는다.
"""

from __future__ import annotations

import base64
import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

from perception import Observation

from .commands import LedCommand
from .features import SceneFeatures, hue_to_rgb
from .policy import ColorRulePolicy, MirrorColorPolicy, Policy

DEFAULT_ENDPOINT = "http://127.0.0.1:8080/v1/chat/completions"

COLOURS = ["red", "orange", "yellow", "green", "cyan", "blue", "purple", "white"]

COLOUR_HUE = {
    "red": 0, "orange": 15, "yellow": 30, "green": 60,
    "cyan": 90, "blue": 120, "purple": 145, "white": None,
}

RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["on", "blink", "off", "none"]},
        "colour": {"type": "string", "enum": COLOURS},
        "reason": {"type": "string", "maxLength": 80},
    },
    "required": ["action", "colour", "reason"],
    "additionalProperties": False,
}
"""`none` 은 **합법적인 출력**이다.

모델에게 "모르겠다" 는 출구를 주지 않으면 반드시 지어낸다. `none` 이 오면
직전 명령을 유지한다 — 판단을 못 한 것과 "끄라" 는 것은 다르다.

`colour` 는 `action` 과 무관하게 **항상 필수**다. 조건부로 두었더니 모델이
`blink` 를 내면서 `colour` 를 생략했고, 스키마는 허용하는데 검증기는 거부해
전 요청이 실패했다. 스키마가 허용하는 것을 검증기가 막으면 그 계약은 틀린
것이다 — 둘이 어긋나지 않도록 `test_schema_and_validator_agree` 로 고정한다.
`off` 와 `none` 에서는 값을 무시한다.
"""

SYSTEM_PROMPT = (
    "You control a single RGB LED by looking at a camera image. "
    "Reply only with the JSON object the schema describes.\n"
    "- If a clearly coloured object is present, set action to 'on' and colour to "
    "the object's colour, so the LED mirrors it.\n"
    "- If the object looks like a warning (red), use 'blink' instead.\n"
    "- If the scene has no clearly coloured object, use 'off'.\n"
    "- If the image is too dark, blurred or ambiguous to judge, use 'none'. "
    "Do not guess.\n"
    "Always include a colour field. For 'off' and 'none' it is ignored, so any "
    "value is fine."
)


class VlmError(RuntimeError):
    """VLM 호출이나 응답 검증이 실패했다."""


@dataclass(frozen=True)
class VlmDecision:
    """모델이 낸 한 번의 판단. 결정 로그(µ6.4)에 그대로 남긴다."""

    action: str
    colour: str | None
    reason: str
    latency_ms: float
    observed_seq: int
    observed_at: float
    raw: str = ""

    def describe(self) -> str:
        c = f" {self.colour}" if self.colour else ""
        return f"{self.action}{c} ({self.reason[:40]}) {self.latency_ms:.0f}ms"


def encode_jpeg(image: Any, width: int = 768, height: int = 432, quality: int = 85) -> str:
    """이미지를 base64 JPEG 로. 768×432 는 실측으로 정한 값이다.

    더 크면 이미지 토큰이 배치를 넘어 abort 하고, 더 작으면 그라운딩 정확도가
    떨어진다는 경고가 뜬다 (docs/tech/notes/vlm-on-orin-nano.md).
    """
    import cv2

    small = cv2.resize(image, (width, height))
    bgr = cv2.cvtColor(small, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not ok:
        raise VlmError("JPEG 인코딩 실패")
    return base64.b64encode(buf.tobytes()).decode()


class VlmClient:
    """llama-server 의 OpenAI 호환 엔드포인트 호출."""

    def __init__(
        self,
        endpoint: str = DEFAULT_ENDPOINT,
        *,
        timeout_s: float = 20.0,
        max_tokens: int = 80,
        temperature: float = 0.1,
        prompt: str = SYSTEM_PROMPT,
        opener: Callable[[Any, float], bytes] | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.timeout_s = timeout_s
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.prompt = prompt
        # 시험에서 갈아끼운다. 실제 서버 없이 정책 로직을 검증하기 위한 이음매다.
        self._opener = opener or self._urlopen

    @staticmethod
    def _urlopen(req: Any, timeout: float) -> bytes:
        return urllib.request.urlopen(req, timeout=timeout).read()

    def ask(self, image: Any) -> tuple[dict[str, Any], float, str]:
        """이미지를 보내고 스키마를 통과한 판단을 받는다."""
        body = json.dumps({
            "model": "local",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "led_decision", "schema": RESPONSE_SCHEMA,
                                "strict": True},
            },
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": self.prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_jpeg(image)}"}},
            ]}],
        }).encode()

        req = urllib.request.Request(
            self.endpoint, data=body, headers={"Content-Type": "application/json"}
        )
        t0 = time.perf_counter()
        try:
            payload = self._opener(req, self.timeout_s)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise VlmError(f"VLM 호출 실패: {type(e).__name__}: {e}") from e
        latency = (time.perf_counter() - t0) * 1000

        try:
            content = json.loads(payload)["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise VlmError(f"응답 형식이 예상과 다르다: {e}") from e

        try:
            obj = json.loads(content)
        except ValueError as e:
            raise VlmError(f"JSON 이 아니다: {content[:80]!r}") from e

        return validate(obj), latency, content


def validate(obj: Any) -> dict[str, Any]:
    """스키마 강제를 믿지 않고 한 번 더 검사한다.

    `strict` 스키마를 지원하지 않는 서버에 붙을 수도 있고, 지원하더라도
    검증기는 계약의 일부다 — 모델 출력이 액추에이터에 닿는 유일한 통로다.
    """
    if not isinstance(obj, dict):
        raise VlmError(f"객체가 아니다: {type(obj).__name__}")
    action = obj.get("action")
    if action not in ("on", "blink", "off", "none"):
        raise VlmError(f"알 수 없는 action: {action!r}")
    colour = obj.get("colour")
    if action in ("on", "blink"):
        if colour not in COLOURS:
            raise VlmError(f"{action} 에는 유효한 colour 가 필요하다: {colour!r}")
    return {"action": action, "colour": colour,
            "reason": str(obj.get("reason", ""))[:80]}


def to_command(decision: dict[str, Any], *, level: int = 200) -> LedCommand | None:
    """모델 판단을 명령으로. `none` 이면 None (직전 명령 유지)."""
    action = decision["action"]
    if action == "none":
        return None
    if action == "off":
        return LedCommand("off")

    colour = decision["colour"]
    hue = COLOUR_HUE.get(colour)
    rgb = (255, 255, 255) if hue is None else hue_to_rgb(hue)
    if action == "blink":
        return LedCommand("blink", rgb=rgb, interval_ms=150, level=level)
    return LedCommand("on", rgb=rgb, level=level)


class VlmPolicy(Policy):
    """VLM 판단을 **비동기로** 수행하는 정책 (ADR-0008).

    `decide()` 는 절대 블로킹하지 않는다. 작업 스레드가 최신 관측으로 추론을
    돌리는 동안, 제어 루프는 마지막으로 확정된 명령을 계속 쓴다.
    """

    def __init__(
        self,
        client: VlmClient | None = None,
        *,
        fallback: Policy | None = None,
        level: int = 200,
        min_interval_s: float = 0.5,
    ) -> None:
        self.client = client or VlmClient()
        self.fallback = fallback or MirrorColorPolicy()
        """VLM 판단이 아직 없거나 실패했을 때 답하는 정책.

        루프는 항상 명령이 필요하다. 폴백이 없으면 첫 판단이 올 때까지 LED 가
        죽어 있고, VLM 이 죽으면 영영 멈춘다.
        """
        self.level = level
        self.min_interval_s = min_interval_s

        self._lock = threading.Lock()
        self._pending: Observation | None = None
        self._command: LedCommand | None = None
        self._last: VlmDecision | None = None
        self._last_run = 0.0
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None
        self.stats: dict[str, int] = {
            "requests": 0, "ok": 0, "invalid": 0, "failed": 0, "none": 0
        }

    # --- 생애주기 ---

    def start(self) -> "VlmPolicy":
        if self._worker is None:
            self._stop.clear()
            self._worker = threading.Thread(target=self._run, daemon=True)
            self._worker.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._worker is not None:
            self._worker.join(timeout=5.0)
            self._worker = None

    def __enter__(self) -> "VlmPolicy":
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()

    # --- Policy ---

    def decide(
        self, features: SceneFeatures, observation: Observation | None = None
    ) -> LedCommand:
        if observation is not None and observation.image is not None:
            with self._lock:
                self._pending = observation   # 최신 것만 남긴다. 밀린 프레임은 버린다.

        with self._lock:
            cmd = self._command
        if cmd is not None:
            return cmd
        return self.fallback.decide(features, observation)

    @property
    def last_decision(self) -> VlmDecision | None:
        with self._lock:
            return self._last

    # --- 작업 스레드 ---

    def _run(self) -> None:
        while not self._stop.is_set():
            obs = self._take()
            if obs is None:
                self._stop.wait(0.05)
                continue
            self._infer(obs)

    def _take(self) -> Observation | None:
        """처리할 관측을 꺼낸다. 최소 간격을 지켜 서버를 몰아붙이지 않는다."""
        if time.monotonic() - self._last_run < self.min_interval_s:
            return None
        with self._lock:
            obs, self._pending = self._pending, None
        return obs

    def _infer(self, obs: Observation) -> None:
        self._last_run = time.monotonic()
        self.stats["requests"] += 1
        try:
            decision, latency, raw = self.client.ask(obs.image)
        except VlmError:
            self.stats["failed"] += 1
            return          # 직전 명령을 유지한다. 실패가 LED 를 끄지는 않는다.

        record = VlmDecision(
            action=decision["action"], colour=decision["colour"],
            reason=decision["reason"], latency_ms=latency,
            observed_seq=obs.seq, observed_at=obs.timestamp, raw=raw,
        )
        try:
            cmd = to_command(decision, level=self.level)
        except Exception:
            self.stats["invalid"] += 1
            return

        if cmd is None:
            self.stats["none"] += 1
        else:
            self.stats["ok"] += 1
        with self._lock:
            self._last = record
            if cmd is not None:
                self._command = cmd


# --------------------------------------------------------------------------
# VS-4 — 역량 계약 위에서 판단하기
# --------------------------------------------------------------------------


CONTRACT_PROMPT = (
    "You control physical devices by looking at a camera image.\n"
    "Available devices and commands:\n{devices}\n\n"
    "Reply with one JSON object choosing a device and command, with arguments "
    "inside the declared ranges. Mirror the colour of any clearly coloured "
    "object you see. If you cannot judge the scene, choose the command that "
    "leaves things unchanged rather than guessing."
)


class ContractVlmClient(VlmClient):
    """역량 계약에서 파생된 스키마로 모델에게 묻는다.

    프롬프트의 장치 목록도, 강제할 JSON 스키마도, 응답 검증도 **모두 하나의
    선언에서 나온다.** 장치를 추가해도 이 클래스는 바뀌지 않는다 — 그것이 VS-4 다.
    """

    def __init__(self, registry: Any, endpoint: str = DEFAULT_ENDPOINT, **kw: Any) -> None:
        super().__init__(endpoint, prompt=CONTRACT_PROMPT.format(
            devices=registry.describe()), **kw)
        self.registry = registry

    def ask(self, image: Any) -> tuple[Any, float, str]:
        body = json.dumps({
            "model": "local",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "device_call",
                                "schema": self.registry.tool_schema(),
                                "strict": True},
            },
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": self.prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_jpeg(image)}"}},
            ]}],
        }).encode()

        req = urllib.request.Request(
            self.endpoint, data=body, headers={"Content-Type": "application/json"}
        )
        t0 = time.perf_counter()
        try:
            payload = self._opener(req, self.timeout_s)
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise VlmError(f"VLM 호출 실패: {type(e).__name__}: {e}") from e
        latency = (time.perf_counter() - t0) * 1000

        try:
            content = json.loads(payload)["choices"][0]["message"]["content"]
            obj = json.loads(content)
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise VlmError(f"응답을 해석할 수 없다: {e}") from e

        from .capability import ContractError

        try:
            call = self.registry.validate(obj)
        except ContractError as e:
            raise VlmError(f"계약 위반: {e}") from e
        return call, latency, content
