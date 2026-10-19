"""모듈 6 §3 — 시뮬레이터의 워치독이 **펌웨어와 같은 의미**인가.

의미가 다르면 실습에서 배운 것이 실물에서 틀린다. 그래서 펌웨어의 규칙을
한 줄씩 옮겨 고정한다 (`arduino/rgb_led/rgb_led.ino`).
"""

import pytest

from control.commands import LedCommand
from sim import SimWorld


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, ms: float) -> None:
        self.t += ms / 1000.0


def world(watchdog_ms=0):
    c = Clock()
    return SimWorld(clock=c, watchdog_ms=watchdog_ms), c


def test_the_watchdog_is_off_by_default():
    """LED 는 켜진 채 남아도 해롭지 않다. 모터가 시작할 때 켜는 것이다."""
    assert SimWorld().watchdog_ms == 0


def test_without_a_watchdog_the_led_stays_lit_forever():
    w, c = world(0)
    w.apply(LedCommand("on", rgb=(255, 0, 0)))
    c.advance(60_000)
    assert max(w.emitted()) > 0
    assert w.tripped is False


def test_silence_trips_the_watchdog_and_the_device_goes_dark():
    w, c = world(1000)
    w.apply(LedCommand("on", rgb=(255, 0, 0)))
    c.advance(999)
    assert max(w.emitted()) > 0
    c.advance(2)
    assert w.emitted() == (0, 0, 0)
    assert w.tripped is True


def test_a_command_feeds_the_watchdog():
    w, c = world(1000)
    for _ in range(5):
        w.apply(LedCommand("on", rgb=(255, 0, 0)))
        c.advance(800)
        assert w.tripped is False


def test_observing_the_trip_does_not_clear_it():
    """`STATE` 가 트립을 지우면 트립을 영영 읽을 수 없다."""
    w, c = world(500)
    w.apply(LedCommand("on", rgb=(255, 0, 0)))
    c.advance(600)
    assert w.state()["tripped"] is True
    assert w.state()["tripped"] is True          # 두 번 읽어도 남아 있다
    assert w.emitted() == (0, 0, 0)


def test_a_ping_feeds_but_does_not_revive():
    """트립된 장치는 인사했다고 깨어나지 않는다."""
    w, c = world(500)
    w.apply(LedCommand("on", rgb=(255, 0, 0)))
    c.advance(600)
    assert w.tripped is True
    w.feed()
    c.advance(10)
    assert w.tripped is True
    assert w.emitted() == (0, 0, 0)


def test_only_an_output_command_brings_it_back():
    w, c = world(500)
    w.apply(LedCommand("on", rgb=(255, 0, 0)))
    c.advance(600)
    assert w.tripped is True
    w.apply(LedCommand("on", rgb=(0, 255, 0)))   # 명시적으로 되돌린다
    assert w.tripped is False
    assert max(w.emitted()) > 0


def test_a_tripped_device_does_not_keep_blinking_on_its_way_down():
    """펌웨어는 출력을 구동하기 **전에** 워치독을 본다."""
    w, c = world(300)
    w.apply(LedCommand("blink", rgb=(255, 0, 0), interval_ms=100))
    c.advance(400)
    for _ in range(10):                          # 어느 위상에서 봐도 꺼져 있다
        c.advance(37)
        assert w.emitted() == (0, 0, 0)
