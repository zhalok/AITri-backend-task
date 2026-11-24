"""Optimistic concurrency: a write may say which value it was based on.

`seen` is what the caller's screen showed (a number, or None for "nothing yet"). Leaving it out entirely
(UNSET) means "no check": the last save simply wins, as the brief specifies for scores.
"""


class _Unset:
    def __repr__(self) -> str:
        return "UNSET"


UNSET = _Unset()
