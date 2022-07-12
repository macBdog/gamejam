def clamp(val: float, low: float, high: float) -> float:
    return max(low, min(val, high))


def clamp021(val: float,) -> float:
    return max(0.0, min(val, 1.0))


def lerp(val: float, target:float, frac: float) -> float:
    return val + ((target - val) * frac)


def bicubic(val: float, target: float, frac: float) -> float:
    return lerp(val, target, frac * frac * (3.0 - 2.0 * frac))
