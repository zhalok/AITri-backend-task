from decimal import ROUND_HALF_UP, Decimal


def percent(part: int, whole: int) -> int:
    """part / whole as a whole percent, rounded half up (12.5 -> 13), in exact decimal arithmetic."""
    return int((Decimal(part) * 100 / Decimal(whole)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
