from app.core.clock import Clock
from tests.helpers import NOW, TZ


def test_a_plain_clock_is_frozen_for_both_now_and_live_now():
    clock = Clock(NOW, TZ)
    assert clock.live_now() == clock.now() == NOW


def test_a_ticking_clock_keeps_now_frozen_but_live_now_moves():
    clock = Clock(NOW, TZ, ticking=True)
    first = clock.live_now()
    assert clock.now() == NOW
    assert first >= NOW and clock.live_now() >= first
