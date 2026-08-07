import csv
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import reference_model as R

DATA = Path(os.environ.get("TASK_DATA", "/app/data"))
OUT = Path(os.environ.get("TASK_OUT", "/app/output"))

TOL_CLAIM = 2.5
TARGET_FRACTION = 0.65

def say(msg):
    print(msg, flush=True)

def ratio_off(a, b):
    if not (math.isfinite(a) and math.isfinite(b)) or a <= 0 or b <= 0:
        return math.inf
    return max(a / b, b / a)


def write_reward(score):
    d = Path("/logs/verifier")
    try:
        d.mkdir(parents=True, exist_ok=True)
        (d / "reward.txt").write_text(f"{score:.6f}\n")
    except OSError:
        pass
    say(f"REWARD {score:.6f}")


def fail(reason):
    say(f"FAILED: {reason}")
    write_reward(0.0)
    sys.exit(0)

def main():
    spec = R.load_spec(str(DATA / "pump_specification.yaml"))
    bounds = {r["variable"]: (float(r["lower"]), float(r["upper"]))
              for r in csv.DictReader(open(DATA / "design_bounds.csv"))}

    opt_path = OUT / "optimised_design.json"
    if not opt_path.is_file():
        fail("optimised_design.json missing")
    try:
        opt = json.load(open(opt_path))
    except Exception as exc:
        fail(f"optimised_design.json unreadable: {exc}")

    need = set(R.DESIGN_KEYS) | {"objective", "stroke_duration"}
    if not need <= set(opt):
        fail(f"optimised_design.json needs keys {sorted(need)}")
    try:
        design = np.array([float(opt[k]) for k in R.DESIGN_KEYS])
        claimed = float(opt["objective"])
    except (TypeError, ValueError) as exc:
        fail(f"optimised_design.json values not numeric: {exc}")
    if not np.isfinite(design).all() or not math.isfinite(claimed):
        fail("optimised_design.json contains non-finite values")


    for k, v in zip(R.DESIGN_KEYS, design):
        lo, hi = bounds[k]
        if not lo - 1e-12 <= v <= hi + 1e-12:
            fail(f"{k} = {v:g} is outside its permitted range [{lo:g}, {hi:g}]")


    F_opt, _, completed = R.stroke(spec, design)
    if not completed:
        fail("the submitted design does not complete a stroke")

    baseline = R.stroke(spec, spec["design"])[0]
    achieved = R.neighbourhood_best(spec, design)
    target = TARGET_FRACTION * baseline

    say(f"as-built objective           {baseline:.6e}")
    say(f"submitted design, recomputed {F_opt:.6e}   (claimed {claimed:.6e})")
    say(f"best in its neighbourhood    {achieved:.6e}"
        f"   = {100 * achieved / baseline:.0f}% of as-built,"
        f" target <= {100 * TARGET_FRACTION:.0f}%")


    if ratio_off(claimed, F_opt) > TOL_CLAIM:
        fail(f"claimed objective {claimed:.4e} is not consistent with the "
             f"recomputed {F_opt:.4e}")

    if not (math.isfinite(achieved) and achieved <= target):
        fail(f"the design does not suppress chatter enough: {achieved:.4e} "
             f"against a target of {target:.4e}")

    say("all checks passed")
    write_reward(1.0)


if __name__ == "__main__":
    with np.errstate(over="ignore", invalid="ignore"):
        main()
