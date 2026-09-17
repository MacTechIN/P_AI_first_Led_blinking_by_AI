"""Jetson CSI 카메라 소스 — Argus/GStreamer 경유.

**왜 V4L2Source 로는 안 되는가.** CSI 센서의 `/dev/video0` 은 RG10(10비트 Bayer)
원시 데이터를 내놓는다. 디베이어·자동노출·화이트밸런스는 Tegra ISP 가 하며,
접근 경로는 `nvarguscamerasrc` 다. 게다가 이 시스템의 cv2 는 GStreamer 지원 없이
빌드되어 있어(`GStreamer: NO`) `cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)`
도 쓸 수 없다. 그래서 python-gi 의 Gst 를 직접 쓴다.

`gst-launch ! fdsink` 로 파이프하는 방법은 쓰지 않는다 — nvarguscamerasrc 가
stdout 에 진단 문구를 섞어 프레임 바이트를 오염시킨다 (실측: 640x480x3x3 프레임에
1277 바이트 초과 수신).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .sources import FrameSource

DEFAULT_WARMUP = 30
"""버릴 초기 프레임 수.

Argus 자동노출은 수렴에 시간이 걸린다. 실측에서 첫 프레임은 mean=22.7/std=9.7 로
거의 검은 화면이었고, 60프레임 뒤에는 mean=87.5/std=61.5 의 정상 노출이었다.
건전성 검사(ADR-0005)는 첫 프레임도 통과시키므로 — 어두울 뿐 평탄하지는 않다 —
이 워밍업이 검사를 대신하지 않는다. 둘 다 필요하다.
"""


class ArgusSource(FrameSource):
    """nvarguscamerasrc 기반 CSI 카메라.

        with ArgusSource(width=1280, height=720) as src:
            obs = src.read()
    """

    def __init__(
        self,
        sensor_id: int = 0,
        *,
        width: int = 1280,
        height: int = 720,
        framerate: int = 30,
        warmup: int = DEFAULT_WARMUP,
        source_id: str | None = None,
        check_health: bool = True,
        timeout_s: float = 5.0,
        wbmode: int | None = None,
        awblock: bool = False,
        aelock: bool = False,
        exposure_ns: tuple[int, int] | None = None,
    ) -> None:
        super().__init__(
            source_id=source_id or f"argus:{sensor_id}", check_health=check_health
        )
        self.sensor_id = sensor_id
        self.width = width
        self.height = height
        self.framerate = framerate
        self.warmup = warmup
        self.timeout_s = timeout_s
        self.wbmode = wbmode
        self.awblock = awblock
        self.aelock = aelock
        self.exposure_ns = exposure_ns
        self._pipeline: Any = None
        self._sink: Any = None

    def pipeline_description(self) -> str:
        # 측정에는 자동 보정을 끄는 편이 낫다. AWB/AE 가 프레임마다 색과 노출을
        # 바꾸면 "LED 색이 변한 것" 과 "카메라가 해석을 바꾼 것" 을 구별할 수 없다.
        opts = ""
        if self.wbmode is not None:
            opts += f" wbmode={self.wbmode}"
        if self.awblock:
            opts += " awblock=true"
        if self.aelock:
            opts += " aelock=true"
        if self.exposure_ns:
            lo, hi = self.exposure_ns
            opts += f' exposuretimerange="{lo} {hi}"'
        return (
            f"nvarguscamerasrc sensor-id={self.sensor_id}{opts} ! "
            f"video/x-raw(memory:NVMM),width={self.width},height={self.height},"
            f"framerate={self.framerate}/1 ! "
            "nvvidconv ! video/x-raw,format=BGRx ! "
            "videoconvert ! video/x-raw,format=RGB ! "
            "appsink name=sink max-buffers=1 drop=true sync=false"
        )

    def _open(self) -> None:
        import gi

        gi.require_version("Gst", "1.0")
        from gi.repository import Gst

        Gst.init(None)
        self._pipeline = Gst.parse_launch(self.pipeline_description())
        self._sink = self._pipeline.get_by_name("sink")
        if self._pipeline.set_state(Gst.State.PLAYING) == Gst.StateChangeReturn.FAILURE:
            self._pipeline = None
            raise RuntimeError(
                f"{self.source_id}: 파이프라인 시작 실패. "
                "카메라 연결과 오버레이를 확인하라 (ls /dev/video*)"
            )

        # 자동노출이 수렴할 때까지 버린다. 이걸 건너뛰면 거의 검은 프레임을 받는다.
        for _ in range(self.warmup):
            self._pull()

    def _close(self) -> None:
        if self._pipeline is not None:
            from gi.repository import Gst

            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
            self._sink = None

    def _pull(self) -> np.ndarray:
        from gi.repository import Gst

        sample = self._sink.emit(
            "try-pull-sample", int(self.timeout_s * Gst.SECOND)
        )
        if sample is None:
            raise RuntimeError(
                f"{self.source_id}: {self.timeout_s}s 안에 프레임이 오지 않았다"
            )

        caps = sample.get_caps().get_structure(0)
        w, h = caps.get_value("width"), caps.get_value("height")
        buf = sample.get_buffer()
        ok, info = buf.map(Gst.MapFlags.READ)
        if not ok:
            raise RuntimeError(f"{self.source_id}: 버퍼 매핑 실패")
        try:
            # 복사한다. 매핑 해제 후에도 배열이 유효해야 한다.
            return np.frombuffer(info.data, dtype=np.uint8).reshape(h, w, 3).copy()
        finally:
            buf.unmap(info)

    def _grab(self) -> np.ndarray:
        return self._pull()

    def _meta(self) -> dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "width": self.width,
            "height": self.height,
            "framerate": self.framerate,
            "warmup": self.warmup,
            "wbmode": self.wbmode,
            "awblock": self.awblock,
            "aelock": self.aelock,
        }
