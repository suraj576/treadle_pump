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
