"""
LinearProgram model — the central data object.

Holds the objective function, all constraints, variable names,
optimisation direction, and non-negativity flags.
"""

from .constraint import Constraint


class LinearProgram:
    """
    Represents a complete linear programme.

    Attributes:
        objective (list[float]): Coefficients of the objective function.
        constraints (list[Constraint]): List of constraints.
        direction (str): 'max' or 'min'.
        variable_names (list[str]): e.g. ['x1', 'x2'].
        non_negative (list[bool]): True if the variable must be ≥ 0.
        num_vars (int): Number of decision variables.
    """

    def __init__(
        self,
        objective: list,
        constraints: list,
        direction: str = "max",
        variable_names: list = None,
        non_negative: list = None,
    ):
        if direction not in ("max", "min"):
            raise ValueError("direction must be 'max' or 'min'")

        self.num_vars = len(objective)
        self.objective = [float(c) for c in objective]
        self.direction = direction
        self.constraints = constraints  # list[Constraint]

        # Auto-generate variable names if not provided
        self.variable_names = variable_names or [f"x{i+1}" for i in range(self.num_vars)]

        # By default all variables are non-negative
        self.non_negative = non_negative if non_negative is not None else [True] * self.num_vars

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def validate(self) -> list:
        """Return a list of validation error strings (empty = OK)."""
        errors = []
        if self.num_vars < 1:
            errors.append("At least one decision variable is required.")
        for i, c in enumerate(self.constraints):
            if c.num_variables() != self.num_vars:
                errors.append(
                    f"Constraint {i+1} has {c.num_variables()} coefficients "
                    f"but the programme has {self.num_vars} variables."
                )
        return errors

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "objective": self.objective,
            "direction": self.direction,
            "variable_names": self.variable_names,
            "non_negative": self.non_negative,
            "constraints": [c.to_dict() for c in self.constraints],
        }

    def objective_str(self) -> str:
        """Return a human-readable objective function string."""
        terms = []
        for i, c in enumerate(self.objective):
            if c == 0:
                continue
            name = self.variable_names[i]
            terms.append(f"{c:g} {name}")
        return " + ".join(terms) if terms else "0"

    def __repr__(self) -> str:
        return (
            f"LinearProgram({self.direction.upper()} Z = {self.objective_str()}, "
            f"{len(self.constraints)} constraints, {self.num_vars} vars)"
        )
