"""OpenCV 없는 색 변환이 **OpenCV 와 같은 답**을 내는가.

규약이 어긋나면 색 판정이 전부 틀어진다. 학생 노트북(cv2 없음)과 강사 장비
(cv2 있음)가 다른 답을 내면 실습이 성립하지 않는다.
"""

import numpy as np
import pytest

from control.colour import (_hsv_to_rgb_numpy, _rgb_to_hsv_numpy, hsv_to_rgb,
                            rgb_to_hsv)

cv2 = pytest.importorskip("cv2")


def test_hue_uses_opencv_eight_bit_convention():
    """H 는 0~179 다. 0~360 으로 쓰면 색 이름이 전부 밀린다."""
    red = np.uint8([[[255, 0, 0]]])
    assert _rgb_to_hsv_numpy(red)[0, 0, 0] == 0
    green = np.uint8([[[0, 255, 0]]])
    assert _rgb_to_hsv_numpy(green)[0, 0, 0] == 60      # 120도 → 60
    blue = np.uint8([[[0, 0, 255]]])
    assert _rgb_to_hsv_numpy(blue)[0, 0, 0] == 120      # 240도 → 120


def test_rgb_to_hsv_matches_opencv_on_random_images():
    rng = np.random.default_rng(0)
    img = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
    ours = _rgb_to_hsv_numpy(img)
    theirs = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    # 색조는 원형이다 — 179 와 0 은 1 만큼 떨어져 있다
    dh = np.abs(ours[..., 0].astype(int) - theirs[..., 0].astype(int))
    assert np.minimum(dh, 180 - dh).max() <= 1
    assert np.abs(ours[..., 1].astype(int) - theirs[..., 1].astype(int)).max() <= 1
    assert np.array_equal(ours[..., 2], theirs[..., 2])


def test_hsv_to_rgb_matches_opencv_on_random_images():
    rng = np.random.default_rng(1)
    img = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
    img[..., 0] %= 180
    ours = _hsv_to_rgb_numpy(img)
    theirs = cv2.cvtColor(img, cv2.COLOR_HSV2RGB)
    assert np.abs(ours.astype(int) - theirs.astype(int)).max() <= 1


@pytest.mark.parametrize("rgb", [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255),
    (255, 0, 255), (0, 0, 0), (255, 255, 255), (128, 128, 128), (220, 40, 40),
])
def test_the_colours_the_course_uses_match_exactly(rgb):
    px = np.uint8([[list(rgb)]])
    assert np.array_equal(_rgb_to_hsv_numpy(px), cv2.cvtColor(px, cv2.COLOR_RGB2HSV))


def test_the_public_helpers_use_opencv_when_it_is_there():
    rng = np.random.default_rng(2)
    img = rng.integers(0, 256, (16, 16, 3), dtype=np.uint8)
    assert np.array_equal(rgb_to_hsv(img), cv2.cvtColor(img, cv2.COLOR_RGB2HSV))
    hsv = rgb_to_hsv(img)
    assert np.array_equal(hsv_to_rgb(hsv), cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB))
