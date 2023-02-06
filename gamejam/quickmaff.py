import math
import numpy


def clamp(val: float, low: float, high: float) -> float:
    return max(low, min(val, high))


def clamp021(val: float,) -> float:
    return max(0.0, min(val, 1.0))


def lerp(val: float, target:float, frac: float) -> float:
    return val + ((target - val) * frac)


def bicubic(val: float, target: float, frac: float) -> float:
    return lerp(val, target, frac * frac * (3.0 - 2.0 * frac))


def get_orthographic_mat_row_major(left, right, bottom, top, near, far):
    return [
        2.0 / (right-left), 0.0, 0.0, 0.0,
        0.0, 2.0 / (top-bottom), 0.0, 0.0,
        0.0, 0.0 , -2.0 / (far-near), 0.0,
        -((right+left)/(right-left)), -((top+bottom)/(top-bottom)), -((far+near)/(far/near)), 1.0
    ]


def get_perspective_mat_row_major(fov: float, aspect: float, near: float, far: float):
    ymax = near * math.tan(fov * 0.5 * math.pi/180.0)
    ymin = -ymax
    xmax = ymax * aspect
    xmin = ymin * aspect

    width = xmax - xmin
    height = ymax - ymin

    depth = far - near
    q = -(far + near) / depth
    qn = -2.0 * (far * near) / depth

    w = 2.0 * near / width
    w = w / aspect
    h = 2.0 * near / height

    return [
        w, 0.0, 0.0, 0.0,
        0.0, h, 0.0, 0.0,
        0.0, 0.0, q, -1.0,
        0.0, 0.0, qn, 0.0
    ]


MATRIX_IDENTITY = numpy.array([
    1.0, 0.0, 0.0, 0.0, 
    0.0, 1.0, 0.0, 0.0,
    0.0, 0.0, 1.0, 0.0,
    0.0, 0.0, 0.0, 1.0
])
MATRIX_ORTHO = numpy.array([get_orthographic_mat_row_major(-1.0, 1.0, -1.0, 1.0, 1.0, -1.0)])
MATRIX_PERSPECTIVE = numpy.array([get_perspective_mat_row_major(60.0, 1.3333, 1.0, 10000.0)])