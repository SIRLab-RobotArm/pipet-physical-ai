import numpy as np
import pandas as pd

from ai.eval.analyze import descriptive_success, grasp_errors


def test_grasp_errors_interpolate_first_close_and_cut_before_move():
    trace = pd.DataFrame({
        "t": [0.0, 1.0, 2.0],
        "ee_pose": [
            [10.0, 0.0, 5.0, 0, 0, 0],
            [4.0, 0.0, 3.0, 0, 0, 0],
            [0.0, 0.0, 1.0, 0, 0, 0],
        ],
    })
    e1, e2, e3, clean = grasp_errors(
        trace, {"t_close": 1.5, "t_move": 1.75, "t_end": 2.0}, [0.0, 0.0, 0.0])
    assert e1 == 2.0
    assert e2 == 2.0
    assert e3 == 4.0
    assert clean is True


def test_grasp_errors_no_close_keeps_e3_defined():
    trace = pd.DataFrame({
        "t": [0.0, 1.0],
        "ee_pose": [[3.0, 4.0, 2.0, 0, 0, 0], [0.0, 2.0, 1.0, 0, 0, 0]],
    })
    e1, e2, e3, clean = grasp_errors(
        trace, {"t_close": None, "t_move": None, "t_end": 1.0}, [0.0, 0.0, 0.0])
    assert e1 is None and e2 is None and clean is None
    assert e3 == 2.0


def test_descriptive_success_groups_rgb_models_by_condition():
    data = pd.DataFrame({
        "condition": ["A", "A", "B"],
        "success": [True, False, True],
    })
    rows = descriptive_success(data)
    assert [(row["condition"], row["successes"], row["total"]) for row in rows] == [
        ("A", 1, 2),
        ("B", 1, 1),
    ]
