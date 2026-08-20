#!/usr/bin/env python3
"""Preregistered raw-rollout metrics and mixed-effects analyses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _event_value(events, name):
    if isinstance(events, dict):
        return events.get(name)
    return getattr(events, name, None)


def _pose_matrix(trace):
    values = trace["ee_pose"]
    return np.stack([np.asarray(value, dtype=np.float64) for value in values])


def _interpolate_pose(trace, stamp):
    times = trace["t"].to_numpy(dtype=np.float64)
    poses = _pose_matrix(trace)
    if stamp <= times[0]:
        return poses[0]
    if stamp >= times[-1]:
        return poses[-1]
    upper = int(np.searchsorted(times, stamp, side="right"))
    lower = upper - 1
    weight = (stamp - times[lower]) / (times[upper] - times[lower])
    return poses[lower] * (1.0 - weight) + poses[upper] * weight


def grasp_errors(trace, events, p_target):
    """Return (E1, E2, E3, clean) using only the pre-contact trajectory."""
    if len(trace) == 0:
        raise ValueError("empty trace")
    t_move = _event_value(events, "t_move")
    t_close = _event_value(events, "t_close")
    t_end = _event_value(events, "t_end")
    candidates = [float(x) for x in (t_move, t_close, t_end) if x is not None]
    cutoff = min(candidates) if candidates else float(trace["t"].iloc[-1])
    pre = trace[trace["t"] <= cutoff]
    if len(pre) == 0:
        pre = trace.iloc[[0]]
    target = np.asarray(p_target, dtype=np.float64)
    e3 = float(np.min(np.linalg.norm(_pose_matrix(pre)[:, :2] - target[:2], axis=1)))
    if t_close is None:
        return None, None, e3, None
    pose = _interpolate_pose(trace, float(t_close))
    e1 = float(np.linalg.norm(pose[:2] - target[:2]))
    e2 = float(pose[2] - target[2])
    clean = t_move is None or float(t_close) < float(t_move)
    return e1, e2, e3, bool(clean)


def wilson_interval(successes, total, alpha=0.05):
    from scipy.stats import norm

    if total <= 0:
        return (None, None)
    z = float(norm.ppf(1.0 - alpha / 2.0))
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    radius = z * np.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return float(center - radius), float(center + radius)


def descriptive_success(data):
    rows = []
    for condition, group in data.groupby("condition", dropna=False):
        successes = int(group["success"].sum())
        total = int(len(group))
        lower, upper = wilson_interval(successes, total)
        rows.append({
            "condition": condition, "successes": successes, "total": total,
            "rate": successes / total, "wilson_low": lower, "wilson_high": upper,
        })
    return rows


def fit_models(data):
    """Fit the single preregistered factorial model with crossed random intercepts."""
    import statsmodels.formula.api as smf
    from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM

    fixed = "C(condition) * d"
    success_model = BinomialBayesMixedGLM.from_formula(
        "success ~ " + fixed,
        {"seed": "0 + C(seed)", "position": "0 + C(position_id)"},
        data,
    ).fit_vb()
    results = {
        "formula": "success/E1/E2/E3 ~ condition * d + (1|seed) + (1|position)",
        "success": {
            "fixed_names": list(success_model.model.exog_names),
            "posterior_mean": success_model.fe_mean.tolist(),
            "posterior_sd": success_model.fe_sd.tolist(),
        },
        "continuous": {},
        "success_descriptive": descriptive_success(data),
    }
    for metric in ("E1", "E2", "E3"):
        subset = data.dropna(subset=[metric]).copy()
        if metric in ("E1", "E2") and "clean" in subset:
            subset = subset[subset["clean"].astype(bool)]
        model = smf.mixedlm(
            f"{metric} ~ {fixed}", subset, groups=subset["seed"],
            vc_formula={"position": "0 + C(position_id)"}, re_formula="1").fit()
        results["continuous"][metric] = {
            "coefficients": {key: float(value) for key, value in model.params.items()},
            "confidence_intervals": {
                key: [float(bounds.iloc[0]), float(bounds.iloc[1])]
                for key, bounds in model.conf_int().iterrows()
            },
            "n": int(model.nobs),
        }
    return results


def load_rollouts(root):
    rows = []
    for meta_path in sorted(Path(root).glob("*/meta.json")):
        directory = meta_path.parent
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        events = json.loads((directory / "events.json").read_text(encoding="utf-8"))
        trace = pd.read_parquet(directory / "trace.parquet")
        e1, e2, e3, clean = grasp_errors(trace, events, meta["p_target"])
        rows.append({**meta, "E1": e1, "E2": e2, "E3": e3, "clean": clean})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollouts", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--metrics-only", action="store_true")
    args = parser.parse_args()
    data = load_rollouts(args.rollouts)
    result = {"rollouts": data.to_dict(orient="records")}
    if not args.metrics_only:
        result["models"] = fit_models(data)
    Path(args.output).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
