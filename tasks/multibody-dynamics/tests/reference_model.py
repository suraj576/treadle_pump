import math
import numpy as np
import yaml

DESIGN_KEYS = ("mass_lever", "com_lever", "inertia_lever",
               "mass_rod", "com_rod", "inertia_rod")

STEP = 1.0e-5

def load_spec(path):
    with open(path) as fh:
        s = yaml.safe_load(fh)
    lv, pi, rd = s["lever"], s["piston"], s["connecting_rod"]
    j, ld, st = s["clearance_joint"], s["loads"], s["stroke"]
    f = float
    p = dict(
        g=f(s["environment"]["gravity"]),
        a1=f(lv["pivot_to_joint"]), a3=f(rd["length"]), m2=f(pi["mass"]),
        R1=f(j["bore_radius"]), R2=f(j["pin_radius"]),
        E=f(j["youngs_modulus"]), nu=f(j["poisson_ratio"]),
        torque=f(ld["pedal_torque"]), load=f(ld["piston_load"]),
        th0=math.radians(f(st["lever_angle_start"])),
        th1_end=math.radians(f(st["lever_angle_end"])),
        t_max=f(st["time_limit"]),
        design=np.array([f(lv["mass"]), f(lv["centre_of_mass"]), f(lv["inertia_zz"]),
                         f(rd["mass"]), f(rd["centre_of_mass"]), f(rd["inertia_zz"])]),
    )
    p["c"] = p["R1"] - p["R2"]
    compliance = (1.0 - p["nu"] ** 2) / p["E"]
    p["K"] = 2.0 * math.sqrt((p["R1"] * p["R2"]) / (p["R1"] + p["R2"])) / (3.0 * compliance)
    return p


def initial_state(p):
    th1 = p["th0"]
    th3 = math.acos((p["a1"] * math.cos(th1) - p["a1"]) / p["a3"])
    b = p["a1"] * math.sin(th1) - p["a3"] * math.sin(th3)
    return np.array([th1, b, th3, 0.0, 0.0, 0.0])


def offset(q, p):
    th1, b, th3 = q[0], q[1], q[2]
    dx = p["a1"] * math.cos(th1) - p["a1"] - p["a3"] * math.cos(th3)
    dy = p["a1"] * math.sin(th1) - b - p["a3"] * math.sin(th3)
    return dx, dy, math.hypot(dx, dy)


def _derivs(q, p, d):
    m1, d1, I1, m3, d3, I3 = d
    a1, a3, g = p["a1"], p["a3"], p["g"]
    th1, th3, th3d = q[0], q[2], q[5]

    dx, dy, e = offset(q, p)
    delta = e - p["c"]
    if delta > 0.0 and e > 0.0:
        Fn = p["K"] * delta ** 1.5
        Fx, Fy = -Fn * dx / e, -Fn * dy / e
    else:
        Fx = Fy = 0.0

    s1, c1 = math.sin(th1), math.cos(th1)
    s3, c3 = math.sin(th3), math.cos(th3)

    tau = np.array([
        p["torque"] - a1 * s1 * Fx - m1 * g * d1 * c1 + a1 * c1 * Fy,
        -p["m2"] * g - p["load"] - m3 * g - Fy * a3 / d3 + m3 * d3 * s3 * th3d ** 2,
        a3 * s3 * Fx - m3 * g * d3 * c3 - a3 * c3 * Fy,
    ])
    M = np.array([
        [I1 + m1 * d1 * d1, 0.0,          0.0],
        [0.0,               p["m2"] + m3, m3 * d3 * c3],
        [0.0,               m3 * d3 * c3, I3 + m3 * d3 * d3],
    ])
    acc = np.linalg.solve(M, tau)
    return np.array([q[3], q[4], q[5], acc[0], acc[1], acc[2]])


def stroke(p, design, step=STEP):
    d = np.asarray(design, float)
    if d[4] == 0.0:
        return np.nan, 0.0, False
    q = initial_state(p)
    h, n = step, int(p["t_max"] / step)
    ssq = 0.0
    cnt = 0
    t = 0.0
    for _ in range(n):
        pen = offset(q, p)[2] - p["c"]
        ssq += pen * pen
        cnt += 1
        if q[0] >= p["th1_end"]:
            return math.sqrt(ssq / cnt), t, True
        try:
            k1 = _derivs(q, p, d)
            k2 = _derivs(q + 0.5 * h * k1, p, d)
            k3 = _derivs(q + 0.5 * h * k2, p, d)
            k4 = _derivs(q + h * k3, p, d)
            q = q + (h / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        except (ValueError, OverflowError, ZeroDivisionError, np.linalg.LinAlgError):
            return np.nan, t, False
        if not np.isfinite(q).all():
            return np.nan, t, False
        t += h
    return np.nan, p["t_max"], False


def neighbourhood_best(p, design, pct=0.02):
    d = np.asarray(design, float)
    vals = []
    for cand in [d] + [_bump(d, i, s, pct) for i in range(6) for s in (-1.0, 1.0)]:
        F, _, ok = stroke(p, cand)
        if ok and np.isfinite(F):
            vals.append(F)
    return min(vals) if vals else np.nan


def _bump(d, i, sign, pct):
    out = d.copy()
    out[i] = d[i] * (1.0 + sign * pct)
    return out
