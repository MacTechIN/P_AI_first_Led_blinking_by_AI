"""µ2.1 — 프레임에서 판단에 쓸 특징을 뽑는다.

**전역 평균 밝기를 쓰지 않는다.** 실측에서 LED 를 최대로 켜도 전체 화면 평균은
+0.02 밖에 움직이지 않았다 — Argus 자동노출이 상쇄하기 때문이다
(docs/tech/notes/led-camera-detection.md). 전역 밝기는 조명 상태를 반영하지
못하므로 특징으로 쓸 수 없다.

대신 **관심영역(ROI) 안의 색상**을 본다. 색상(hue)은 노출 변화에 견고하다 —
AE 가 바꾸는 것은 밝기이지 색조가 아니다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DEFAULT_ROI = (0.2, 0.2, 0.8, 0.8)
"""화면 가운데 60%. 가장자리의 배경·조명을 판단에서 제외한다."""

MIN_SATURATION = 60
"""이보다 채도가 낮으면 무채색으로 본다 (0-255)."""

MIN_VALUE = 40
"""이보다 어두우면 색을 신뢰하지 않는다. 어두운 곳의 hue 는 노이즈다."""

MIN_COVERAGE = 0.05
"""ROI 의 이 비율 미만이면 '물체 없음' 으로 본다."""

# OpenCV HSV 의 H 는 0-179 다 (0-359 가 아니다).
_HUE_BANDS: list[tuple[str, int, int]] = [
    ("red", 0, 10),
    ("orange", 11, 22),
    ("yellow", 23, 33),
    ("green", 34, 85),
    ("cyan", 86, 100),
    ("blue", 101, 130),
    ("purple", 131, 160),
    ("red", 161, 179),  # 빨강은 0 을 감싸며 두 구간으로 나뉜다
]


@dataclass(frozen=True)
class SceneFeatures:
    """한 프레임의 요약. 정책(policy)이 보는 유일한 입력이다."""

    color: str | None
    """지배 색 이름. 물체가 없으면 None."""

    hue: float | None
    """지배 색조 (OpenCV 0-179). 물체가 없으면 None."""

    coverage: float
    """ROI 중 지배 색이 차지하는 비율 0-1."""

    saturation: float
    """지배 색 영역의 평균 채도 0-255."""

    brightness: float
    """**ROI 안의** 평균 밝기 0-255. 전체 화면 평균이 아니다."""

    centroid_x: float | None
    """지배 색 영역의 가로 중심 0-1 (0=왼쪽). 방향 판단용. 없으면 None."""

    rgb: tuple[int, int, int] | None = None
    """LED 로 재현할 색. 관측된 원색이 아니라 **색조를 완전 채도로 편 값**이다.

    물체가 어둡거나 바래 보여도 LED 는 그 색조를 선명하게 보여야 한다. 관측
    RGB 를 그대로 쓰면 어두운 빨강이 거의 검게 나와 아무것도 안 보인다.
    """

    def describe(self) -> str:
        if self.color is None:
            return f"물체 없음 (밝기 {self.brightness:.0f})"
        side = "좌" if (self.centroid_x or 0.5) < 0.4 else (
            "우" if (self.centroid_x or 0.5) > 0.6 else "중앙"
        )
        swatch = "#%02x%02x%02x" % self.rgb if self.rgb else "-"
        return (
            f"{self.color} {swatch} {self.coverage:.0%} {side} "
            f"(채도 {self.saturation:.0f}, 밝기 {self.brightness:.0f})"
        )


def hue_to_rgb(hue: float) -> tuple[int, int, int]:
    """색조를 완전 채도·완전 명도의 RGB 로 편다. LED 표시용."""
    import cv2

    px = np.uint8([[[int(hue) % 180, 255, 255]]])
    r, g, b = cv2.cvtColor(px, cv2.COLOR_HSV2RGB)[0, 0]
    return (int(r), int(g), int(b))


def classify_hue(hue: float) -> str:
    for name, lo, hi in _HUE_BANDS:
        if lo <= hue <= hi:
            return name
    return "unknown"


def extract(
    image: np.ndarray,
    *,
    roi: tuple[float, float, float, float] = DEFAULT_ROI,
    min_saturation: int = MIN_SATURATION,
    min_value: int = MIN_VALUE,
    min_coverage: float = MIN_COVERAGE,
) -> SceneFeatures:
    """RGB 이미지에서 특징을 뽑는다."""
    import cv2

    h, w = image.shape[:2]
    x0, y0, x1, y1 = roi
    crop = image[int(y0 * h) : int(y1 * h), int(x0 * w) : int(x1 * w)]

    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    brightness = float(val.mean())

    # 색을 신뢰할 수 있는 화소만 남긴다: 충분히 진하고 충분히 밝은 것
    mask = (sat >= min_saturation) & (val >= min_value)
    if not mask.any():
        return SceneFeatures(None, None, 0.0, 0.0, brightness, None)

    # 지배 색조는 최빈값으로 고른다. 평균은 빨강(0 근처와 179 근처)에서 무너진다.
    counts = np.bincount(hue[mask].ravel(), minlength=180)
    dominant = int(counts.argmax())
    name = classify_hue(dominant)

    # 같은 색 이름에 속하는 화소 전체를 물체로 본다 (빨강의 두 구간을 합친다)
    same = np.zeros_like(mask)
    for band_name, lo, hi in _HUE_BANDS:
        if band_name == name:
            same |= (hue >= lo) & (hue <= hi)
    obj = mask & same

    coverage = float(obj.mean())
    if coverage < min_coverage:
        return SceneFeatures(None, None, coverage, 0.0, brightness, None)

    xs = np.nonzero(obj.any(axis=0))[0]
    centroid_x = float(xs.mean() / obj.shape[1]) if xs.size else None

    return SceneFeatures(
        color=name,
        hue=float(dominant),
        coverage=coverage,
        saturation=float(sat[obj].mean()),
        brightness=brightness,
        centroid_x=centroid_x,
        rgb=hue_to_rgb(dominant),
    )
