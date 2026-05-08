"""
Flask Blueprint: main routes.

Endpoints:
    GET  /           — render the solver UI
    POST /solve      — parse form data, run solver, return JSON result
    GET  /random     — return a random example LP as JSON
"""

import json
import random
from flask import Blueprint, render_template, request, jsonify

from models import LinearProgram, Constraint, Solution
from solvers import SimplexSolver, GraphicalSolver

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_float(val, default=0.0) -> float:
    """Safely parse a form value to float."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def _build_lp_from_form(data: dict) -> LinearProgram:
    """
    Parse the JSON POST body into a LinearProgram object.

    Expected shape:
    {
      "direction": "max" | "min",
      "num_vars": int,
      "num_constraints": int,
      "objective": [c1, c2, ...],
      "constraints": [
          {"coefficients": [...], "inequality": "<=", "rhs": float},
          ...
      ],
      "non_negative": [true, true, ...]
    }
    """
    direction = data.get("direction", "max").lower()
    num_vars = int(data.get("num_vars", 2))
    objective = [_parse_float(v) for v in data.get("objective", [])]

    constraints = []
    for cd in data.get("constraints", []):
        coefs = [_parse_float(v) for v in cd.get("coefficients", [])]
        ineq = cd.get("inequality", "<=")
        rhs = _parse_float(cd.get("rhs", 0))
        constraints.append(Constraint(coefs, ineq, rhs))

    non_negative = data.get("non_negative", [True] * num_vars)

    lp = LinearProgram(
        objective=objective,
        constraints=constraints,
        direction=direction,
        non_negative=non_negative,
    )
    return lp


# ---------------------------------------------------------------------------
# Example problems (pre-filled on page load)
# ---------------------------------------------------------------------------

EXAMPLE_PROBLEMS = [
    # Classic 2-variable max LP (good for graphical)
    {
        "label": "Classic 2-var MAX",
        "direction": "max",
        "num_vars": 2,
        "num_constraints": 3,
        "objective": [5, 4],
        "constraints": [
            {"coefficients": [6, 4], "inequality": "<=", "rhs": 24},
            {"coefficients": [1, 2], "inequality": "<=", "rhs": 6},
            {"coefficients": [0, 1], "inequality": "<=", "rhs": 2},
        ],
        "non_negative": [True, True],
    },
    # Min cost
    {
        "label": "Min cost 2-var",
        "direction": "min",
        "num_vars": 2,
        "num_constraints": 2,
        "objective": [2, 3],
        "constraints": [
            {"coefficients": [1, 1], "inequality": ">=", "rhs": 4},
            {"coefficients": [2, 1], "inequality": ">=", "rhs": 6},
        ],
        "non_negative": [True, True],
    },
    # 3-variable simplex
    {
        "label": "3-var MAX simplex",
        "direction": "max",
        "num_vars": 3,
        "num_constraints": 3,
        "objective": [3, 2, 5],
        "constraints": [
            {"coefficients": [1, 2, 1], "inequality": "<=", "rhs": 430},
            {"coefficients": [3, 2, 0], "inequality": "<=", "rhs": 460},
            {"coefficients": [1, 4, 0], "inequality": "<=", "rhs": 420},
        ],
        "non_negative": [True, True, True],
    },
    # Mixed constraints (Big-M)
    {
        "label": "Mixed constraints (Big-M)",
        "direction": "max",
        "num_vars": 2,
        "num_constraints": 3,
        "objective": [2, 3],
        "constraints": [
            {"coefficients": [1, 0], "inequality": "<=", "rhs": 4},
            {"coefficients": [0, 1], "inequality": "<=", "rhs": 6},
            {"coefficients": [1, 1], "inequality": ">=", "rhs": 3},
        ],
        "non_negative": [True, True],
    },
]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@main_bp.route("/")
def index():
    """Render the main solver page with a default pre-filled example."""
    default_example = EXAMPLE_PROBLEMS[0]
    return render_template(
        "index.html",
        default_example=json.dumps(default_example),
        examples=json.dumps(EXAMPLE_PROBLEMS),
    )


@main_bp.route("/solve", methods=["POST"])
def solve():
    """
    Parse the submitted LP, run the selected solver, and return JSON.
    """
    data = request.get_json(force=True)
    method = data.get("method", "simplex").lower()

    try:
        lp = _build_lp_from_form(data)
    except Exception as exc:
        return jsonify({"status": "error", "message": f"Invalid input: {exc}"}), 400

    errors = lp.validate()
    if errors:
        return jsonify({"status": "error", "message": "\n".join(errors)}), 400

    # Choose solver
    if method == "graphical":
        if lp.num_vars != 2:
            return jsonify({
                "status": "error",
                "message": "Graphical method requires exactly 2 variables.",
            }), 400
        solver = GraphicalSolver(lp)
    else:
        solver = SimplexSolver(lp)

    solution: Solution = solver.solve()
    return jsonify(solution.to_dict())


@main_bp.route("/random")
def random_problem():
    """Return a randomly chosen example problem as JSON."""
    problem = random.choice(EXAMPLE_PROBLEMS)
    return jsonify(problem)
