import math
from dataclasses import dataclass, replace

import numpy as np
import yaml

DESIGN_KEYS = ("mass_lever", "com_lever", "inertia_lever", "mass_rod", "com_rod", "inertia_rod")

STEP = 1e-5

@dataclass(frozen=True)
class Machine:
  g: float
  a1: float; d1: float; m1: float; I1: float
  m2: float
  a3: float; d3: float; m3: float; I3: float
  R1: float; R2: float; E: float; nu: float
  torque: float; load: float
  th_start: float; th_end: float; t_max: float

  @property
  def c(self) -> float:
    return self.R1 - self.R2

  @property
  def K(self) -> float:
    return (2.0 * math.sqrt((self.R1 * self.R2) / (self.R1 + self.R2))) / \
               (3.0 * (1.0 - self.nu ** 2) / self.E)


  def initial_state(self) -> np.ndarray:
    th1 = self.th_start
    th3 = math.acos((self.a1 * math.cos(th1) - self.a1) / self.a3)
    b = self.a1 * math.sin(th1) - self.a3 * math.sin(th3)
    return np.array([th1, b, th3, 0.0, 0.0, 0.0])

  def with_design(self, v) -> "Machine":
    return replace(self, m1=float(v[0]), d1=float(v[1]), I1=float(v[2]),
                   m3=float(v[3]), d3=float(v[4]), I3=float(v[5]))

  def design_vector(self) -> np.ndarray:
    return np.array([self.m1, self.d1, self.I1, self.m3, self.d3, self.I3])


def load_machine(path: str) -> Machine:
    with open(path) as fh:
        s = yaml.safe_load(fh)
    f = float
    lv, pi, rd = s["lever"], s["piston"], s["connecting_rod"]
    j, ld, st = s["clearance_joint"], s["loads"], s["stroke"]
    return Machine(
        g=f(s["environment"]["gravity"]),
        a1=f(lv["pivot_to_joint"]), d1=f(lv["centre_of_mass"]),
        m1=f(lv["mass"]), I1=f(lv["inertia_zz"]),
        m2=f(pi["mass"]),
        a3=f(rd["length"]), d3=f(rd["centre_of_mass"]),
        m3=f(rd["mass"]), I3=f(rd["inertia_zz"]),
        R1=f(j["bore_radius"]), R2=f(j["pin_radius"]),
        E=f(j["youngs_modulus"]), nu=f(j["poisson_ratio"]),
        torque=f(ld["pedal_torque"]), load=f(ld["piston_load"]),
        th_start=math.radians(f(st["lever_angle_start"])),
        th_end=math.radians(f(st["lever_angle_end"])),
        t_max=f(st["time_limit"]),
    )


def make_rhs(M: Machine):
    g, a1, a3, m2 = M.g, M.a1, M.a3, M.m2
    m1, d1, I1 = M.m1, M.d1, M.I1
    m3, d3, I3 = M.m3, M.d3, M.I3
    torque, load, K, c = M.torque, M.load, M.K, M.c
    sin, cos, atan, sqrt, pi = math.sin, math.cos, math.atan, math.sqrt, math.pi

    def f(y):
        th1, b, th3, th1d, bd, th3d = y[0], y[1], y[2], y[3], y[4], y[5]
        s1, c1, s3, c3 = sin(th1), cos(th1), sin(th3), cos(th3)

        dx = a1 * c1 - a1 - a3 * c3
        dy = a1 * s1 - b - a3 * s3
        delta = sqrt(dx * dx + dy * dy) - c
        if delta > 0.0:
            Fn = K * delta * sqrt(delta)
            phi = pi / 2 if (dx == 0.0 and dy == 0.0) else atan(dy / dx)
            sx = 1.0 if dx > 0.0 else (-1.0 if dx < 0.0 else 0.0)
            sy = 1.0 if dy > 0.0 else (-1.0 if dy < 0.0 else 0.0)
            Fx = -sx * Fn * abs(cos(phi))
            Fy = -sy * Fn * abs(sin(phi))
        else:
            Fx = Fy = 0.0

        T0 = torque - a1 * s1 * Fx - m1 * g * d1 * c1 + a1 * c1 * Fy
        T1 = -m2 * g - load - m3 * g - Fy * a3 / d3 + m3 * d3 * s3 * th3d * th3d
        T2 = a3 * s3 * Fx - m3 * g * d3 * c3 - a3 * c3 * Fy

        i22, i23, i33 = m2 + m3, m3 * d3 * c3, I3 + m3 * d3 * d3
        det = i22 * i33 - i23 * i23
        return (th1d, bd, th3d,
                T0 / (I1 + m1 * d1 * d1),
                (i33 * T1 - i23 * T2) / det,
                (i22 * T2 - i23 * T1) / det)

    return f


def stroke(M: Machine, step: float = STEP):
    f = make_rhs(M)
    h, c = step, M.c
    a1, a3 = M.a1, M.a3
    y = M.initial_state()
    n = int(M.t_max / h)
    ssq = 0.0; cnt = 0; t = 0.0

    for k in range(n):
        dx = a1 * math.cos(y[0]) - a1 - a3 * math.cos(y[2])
        dy = a1 * math.sin(y[0]) - y[1] - a3 * math.sin(y[2])
        d = math.hypot(dx, dy) - c
        ssq += d * d; cnt += 1
        if y[0] >= M.th_end:
            return math.sqrt(ssq / cnt), t, True
        try:
            k1 = np.asarray(f(y)); k2 = np.asarray(f(y + 0.5 * h * k1))
            k3 = np.asarray(f(y + 0.5 * h * k2)); k4 = np.asarray(f(y + h * k3))
            y = y + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        except (ValueError, OverflowError, ZeroDivisionError):
            return np.nan, t, False
        if not np.isfinite(y[0]):
            return np.nan, t, False
        t += h

    return np.nan, M.t_max, False


def evaluate(M: Machine, v, step: float = STEP):
    """(F, peak, duration, ok) for design vector v."""
    return stroke(M.with_design(v), step)
