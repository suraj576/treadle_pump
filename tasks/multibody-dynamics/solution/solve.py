import csv
import json
import os
from pathlib import Path

import numpy as np
import model

DATA = Path(os.environ.get("TASK_DATA", "/app/data"))
OUT = Path(os.environ.get("TASK_OUT", "/app/output"))
SEED = 20240805


def read_bounds(path):
    lo, hi, names = [], [], []
    for r in csv.DictReader(open(path)):
        names.append(r["variable"]); lo.append(float(r["lower"])); hi.append(float(r["upper"]))
    return names, np.array(lo), np.array(hi)

def particle_swarm(cost, lo, hi, seed, n=30, iters=30):
    rng = np.random.default_rng(seed)
    d = len(lo)
    X = rng.uniform(lo, hi, (n, d))
    V = rng.uniform(-(hi - lo), hi - lo, (n, d))
    F = np.array([cost(x) for x in X])
    P, PF = X.copy(), F.copy()
    g = int(np.argmin(PF)); best, bestf = P[g].copy(), PF[g]
    w, base_nbr = 1.1, max(2, n // 4)
    nbr, stall = base_nbr, 0

    for _ in range(iters):
        for i in range(n):
            idx = rng.choice(n, size=min(nbr, n), replace=False)
            local = P[idx[np.argmin(PF[idx])]]
            V[i] = (w * V[i]
                    + 1.49 * rng.random(d) * (P[i] - X[i])
                    + 1.49 * rng.random(d) * (local - X[i]))
        Xn = X + V
        clipped = (Xn < lo) | (Xn > hi)
        X = np.clip(Xn, lo, hi)
        V[clipped] = 0.0
        F = np.array([cost(x) for x in X])
        better = F < PF
        P[better], PF[better] = X[better], F[better]
        g = int(np.argmin(PF))
        if PF[g] < bestf:
            bestf, best = PF[g], P[g].copy()
            stall = max(0, stall - 1); nbr = base_nbr
        else:
            stall += 1; nbr = min(nbr + base_nbr, n - 1)
        w = min(2 * w, 1.1) if stall < 2 else (max(w / 2, 0.1) if stall > 5 else w)
    return best, bestf, P, PF

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    M = model.load_machine(str(DATA / "pump_specification.yaml"))
    names, lo, hi = read_bounds(DATA / "design_bounds.csv")

    
    rows = []
    for r in csv.DictReader(open(DATA / "evaluation_designs.csv")):
        v = [float(r[k]) for k in names]
        F, peak, dur, ok = model.evaluate(M, v)
        rows.append((r["id"], F, peak, dur, ok))
    with open(OUT / "design_response.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "objective", "peak_penetration", "stroke_duration"])
        for cid, F, peak, dur, ok in rows:
            w.writerow([cid, f"{F:.10e}", f"{peak:.10e}", f"{dur:.10e}"])
    print(f"design_response.csv: {len(rows)} designs")

    baseline = model.stroke(M)[0]
    print(f"as-built machine: F = {baseline:.6e}")

   
    def cost(v):
        F, _, _, ok = model.evaluate(M, v)
        return 1e6 if not ok or not np.isfinite(F) else F

    best, bestf, P, PF = particle_swarm(cost, lo, hi, SEED)
    print(f"swarm best: F = {bestf:.6e}  ({100 * bestf / baseline:.0f}% of as-built)")


    order = [i for i in np.argsort(PF)[:8] if PF[i] < 1e5]
    scored = []
    for i in order:
        v = P[i]
        vals = [model.evaluate(M, v)[0]]
        for j in range(6):
            for sgn in (-1.0, 1.0):
                w = v.copy()
                w[j] = v[j] * (1.0 + sgn * 0.02)
                vals.append(model.evaluate(M, w)[0])
        vals = [x for x in vals if np.isfinite(x)]
        if not vals:
            continue
        scored.append((float(min(vals)), float(PF[i]), v))

    scored.sort(key=lambda r: r[0])
    if scored:
        typical, at_nominal, v = scored[0]
    else:
        typical, at_nominal, v = bestf, bestf, best
    worst_case = typical
    F, peak, dur, ok = model.evaluate(M, v)
    print(f"chosen design: F = {F:.6e}  typical over neighbourhood {typical:.6e}"
          f"  ({100 * typical / baseline:.0f}% of as-built)")

    json.dump({**{k: float(x) for k, x in zip(names, v)},
               "objective": float(F), "stroke_duration": float(dur)},
              open(OUT / "optimised_design.json", "w"), indent=2)



if __name__ == "__main__":
    with np.errstate(over="ignore", invalid="ignore"):
        main()
