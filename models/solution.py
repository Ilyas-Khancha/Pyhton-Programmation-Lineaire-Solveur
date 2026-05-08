"""
Solution model — stores the result of solving a LinearProgram.
"""


class Solution:
    """
    Stores the complete result of an LP solve.

    Attributes:
        status (str): 'optimal', 'infeasible', 'unbounded', 'error'.
        objective_value (float | None): Optimal Z value.
        variables (dict): {name: value} for each decision variable.
        steps (list[dict]): Intermediate steps (tableaux, plot data, …).
        method (str): 'simplex' or 'graphical'.
        message (str): Human-readable summary.
        graph_image (str | None): Base-64 PNG for graphical method.
    """

    def __init__(
        self,
        status: str,
        method: str,
        objective_value=None,
        variables: dict = None,
        steps: list = None,
        message: str = "",
        graph_image: str = None,
    ):
        self.status = status
        self.method = method
        self.objective_value = objective_value
        self.variables = variables or {}
        self.steps = steps or []
        self.message = message
        self.graph_image = graph_image  # base64-encoded PNG string

    # ------------------------------------------------------------------
    # Serialisation (sent to the Jinja2 template / JSON response)
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "method": self.method,
            "objective_value": self.objective_value,
            "variables": self.variables,
            "steps": self.steps,
            "message": self.message,
            "graph_image": self.graph_image,
        }

    @property
    def is_optimal(self) -> bool:
        return self.status == "optimal"

    def __repr__(self) -> str:
        return f"Solution(status={self.status}, Z={self.objective_value}, vars={self.variables})"
