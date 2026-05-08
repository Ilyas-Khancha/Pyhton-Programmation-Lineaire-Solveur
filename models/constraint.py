"""
Constraint model — represents one linear constraint:
    a1*x1 + a2*x2 + ... + an*xn  {<=, >=, =}  rhs
"""


class Constraint:
    """
    Stores the data for a single linear constraint.

    Attributes:
        coefficients (list[float]): Left-hand side coefficients.
        inequality (str): One of '<=', '>=', '='.
        rhs (float): Right-hand side value.
        label (str): Optional human-readable label.
    """

    VALID_INEQUALITIES = {"<=", ">=", "="}

    def __init__(self, coefficients: list, inequality: str, rhs: float, label: str = ""):
        if inequality not in self.VALID_INEQUALITIES:
            raise ValueError(f"Invalid inequality '{inequality}'. Must be one of {self.VALID_INEQUALITIES}")
        self.coefficients = [float(c) for c in coefficients]
        self.inequality = inequality
        self.rhs = float(rhs)
        self.label = label

    def num_variables(self) -> int:
        return len(self.coefficients)

    def to_dict(self) -> dict:
        return {
            "coefficients": self.coefficients,
            "inequality": self.inequality,
            "rhs": self.rhs,
            "label": self.label,
        }

    def __repr__(self) -> str:
        terms = " + ".join(f"{c}·x{i+1}" for i, c in enumerate(self.coefficients))
        return f"Constraint({terms} {self.inequality} {self.rhs})"
