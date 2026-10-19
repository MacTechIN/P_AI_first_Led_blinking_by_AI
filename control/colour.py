"""색 변환 — OpenCV 없이도 돌게 한다.

교실에 네트워크가 없으면 `pip install` 을 할 수 없다. OpenCV 휠은 플랫폼마다
50MB 가 넘어서 USB 로 돌리기에 무겁고, 우리가 쓰는 기능은 **색 공간 변환 하나뿐**
이다. 그래서 그 하나를 numpy 로 직접 쓴다.

OpenCV 의 8비트 HSV 규약을 **그대로** 따른다 — H 는 0~179(360 이 아니다),
S·V 는 0~255. 규약이 어긋나면 색 판정이 전부 틀어지므로, 두 구현이 같은 답을
내는지 시험이 고정한다 (`tests/test_colour.py`).

cv2 가 있으면 그쪽을 쓴다. 더 빠르고, 젯슨에는 이미 있다.
"""

from __future__ import annotations

import numpy as np

try:
    import cv2 as _cv2
except ImportError:                     # 학생 노트북
    _cv2 = None

HAVE_CV2 = _cv2 is not None


def rgb_to_hsv(image: np.ndarray) -> np.ndarray:
    """RGB uint8 → HSV uint8 (H 0-179, S·V 0-255). OpenCV 와 같은 값."""
    if _cv2 is not None:
        return _cv2.cvtColor(image, _cv2.COLOR_RGB2HSV)
    return _rgb_to_hsv_numpy(image)


def hsv_to_rgb(image: np.ndarray) -> np.ndarray:
    """HSV uint8 → RGB uint8."""
    if _cv2 is not None:
        return _cv2.cvtColor(image, _cv2.COLOR_HSV2RGB)
    return _hsv_to_rgb_numpy(image)


def _rgb_to_hsv_numpy(image: np.ndarray) -> np.ndarray:
    a = image.astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    v = a.max(axis=-1)
    mn = a.min(axis=-1)
    span = v - mn

    # 채도: V 가 0 이면 0 (0 나눗셈을 피한다)
    s = np.zeros_like(v)
    nz = v > 0
    s[nz] = span[nz] / v[nz] * 255.0

    # 색조: 최대 채널이 무엇이냐로 구간이 갈린다. 단위는 도(0~360).
    h = np.zeros_like(v)
    gt = span > 0
    rmax = gt & (v == r)
    gmax = gt & (v == g) & ~rmax
    bmax = gt & ~rmax & ~gmax
    with np.errstate(invalid="ignore", divide="ignore"):
        h[rmax] = 60.0 * (g[rmax] - b[rmax]) / span[rmax]
        h[gmax] = 120.0 + 60.0 * (b[gmax] - r[gmax]) / span[gmax]
        h[bmax] = 240.0 + 60.0 * (r[bmax] - g[bmax]) / span[bmax]
    h[h < 0] += 360.0

    # OpenCV 는 8비트에서 색조를 절반으로 접어 0~179 에 담는다.
    out = np.empty(image.shape, dtype=np.uint8)
    out[..., 0] = np.clip(np.round(h / 2.0), 0, 179).astype(np.uint8)
    out[..., 1] = np.clip(np.round(s), 0, 255).astype(np.uint8)
    out[..., 2] = np.clip(np.round(v), 0, 255).astype(np.uint8)
    return out


def _hsv_to_rgb_numpy(image: np.ndarray) -> np.ndarray:
    a = image.astype(np.float32)
    h = a[..., 0] * 2.0                 # 0~179 를 도로 되돌린다
    s = a[..., 1] / 255.0
    v = a[..., 2]

    i = np.floor(h / 60.0).astype(np.int32) % 6
    f = h / 60.0 - np.floor(h / 60.0)
    p = v * (1.0 - s)
    q = v * (1.0 - f * s)
    t = v * (1.0 - (1.0 - f) * s)

    # i == 5 (색조 300도 이상) 는 기본값으로 떨어진다 — (v, p, q) 다.
    # 처음에 r 의 기본값을 t 로 뒀다가 320도 이상이 전부 틀렸다.
    r = np.select([i == 0, i == 1, i == 2, i == 3, i == 4], [v, q, p, p, t], v)
    g = np.select([i == 0, i == 1, i == 2, i == 3, i == 4], [t, v, v, q, p], p)
    b = np.select([i == 0, i == 1, i == 2, i == 3, i == 4], [p, p, t, v, v], q)

    out = np.empty(image.shape, dtype=np.uint8)
    for k, ch in enumerate((r, g, b)):
        out[..., k] = np.clip(np.round(ch), 0, 255).astype(np.uint8)
    return out


def to_gray(image: np.ndarray) -> np.ndarray:
    """RGB → 그레이스케일 uint8. OpenCV 의 BT.601 가중치와 같다."""
    if _cv2 is not None:
        return _cv2.cvtColor(image, _cv2.COLOR_RGB2GRAY)
    a = image.astype(np.float32)
    g = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    return np.clip(np.round(g), 0, 255).astype(np.uint8)


def resize_area(image: np.ndarray, width: int, height: int) -> np.ndarray:
    """영역 평균으로 축소. `cv2.INTER_AREA` 와 같은 생각이다.

    축소는 속도만을 위한 것이 아니다 — 평균이 저역통과 역할을 해서 화소 단위
    노이즈를 눌러 준다 (예제 2 의 전제).
    """
    if _cv2 is not None:
        return _cv2.resize(image, (width, height), interpolation=_cv2.INTER_AREA)

    h, w = image.shape[:2]
    if width > w or height > h:
        raise ValueError("축소만 지원한다 (INTER_AREA 와 같은 범위)")

    # 경계 화소를 **부분 가중**한다. 정수 경계로 자르면 cv2 와 최대 15 차이가
    # 났고, 움직임 점수는 그 차이를 그대로 물려받아 노이즈 바닥 측정값이
    # 기계마다 달라진다 — 실제로 그렇게 만들었다가 시험에서 걸렸다.
    def weights(src: int, dst: int) -> np.ndarray:
        w_mat = np.zeros((dst, src), dtype=np.float32)
        scale = src / dst
        for k in range(dst):
            lo, hi = k * scale, (k + 1) * scale
            i0, i1 = int(np.floor(lo)), min(int(np.ceil(hi)), src)
            for i in range(i0, i1):
                w_mat[k, i] = min(hi, i + 1) - max(lo, i)
        return w_mat / w_mat.sum(axis=1, keepdims=True)

    wy, wx = weights(h, height), weights(w, width)
    a = image.astype(np.float32)
    if a.ndim == 2:
        out = wy @ a @ wx.T
    else:
        out = np.stack([wy @ a[..., c] @ wx.T for c in range(a.shape[2])], axis=-1)
    return np.clip(np.round(out), 0, 255).astype(image.dtype)
