"""
GraphicalSolver — resolves a 2-variable LP graphically.

Steps:
  1. Find all corner points of the feasible region.
  2. Evaluate the objective at each corner.
  3. Return the optimal corner with a matplotlib plot (base64 PNG).
"""

import io
import base64
import itertools
import numpy as np
import matplotlib
matplotlib.use("Agg")   # non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

from models.linear_program import LinearProgram
from models.solution import Solution


class GraphicalSolver:
    """
    Solves a 2-variable LinearProgram graphically.

    Usage:
        solver = GraphicalSolver(lp)
        solution = solver.solve()
    """

    COLORS = ["#4361ee", "#f72585", "#4cc9f0", "#7209b7", "#3a0ca3", "#480ca8"]
    FEASIBLE_COLOR = "#b7e4c7"
    OPTIMAL_COLOR = "#e63946"
    AXIS_COLOR = "#333"

    def __init__(self, lp: LinearProgram):
        if lp.num_vars != 2:
            raise ValueError("GraphicalSolver only supports exactly 2 variables.")
        self.lp = lp
        self.steps = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def solve(self) -> Solution:
        try:
            corners = self._find_feasible_corners()
            if not corners:
                return Solution(
                    status="infeasible",
                    method="graphical",
                    message="No feasible region found.",
                    steps=self.steps,
                )

            best_pt, best_val = self._evaluate_corners(corners)
            graph_b64 = self._plot(corners, best_pt)

            variables = {
                self.lp.variable_names[0]: round(best_pt[0], 4),
                self.lp.variable_names[1]: round(best_pt[1], 4),
            }

            self.steps.append({
                "title": "Corner Point Evaluation",
                "corners": [
                    {
                        "point": (round(p[0], 4), round(p[1], 4)),
                        "value": round(self._obj(p), 4),
                        "optimal": (p == best_pt),
                    }
                    for p in corners
                ],
            })

            return Solution(
                status="optimal",
                method="graphical",
                objective_value=round(best_val, 4),
                variables=variables,
                steps=self.steps,
                message=f"Optimal at ({best_pt[0]:.4f}, {best_pt[1]:.4f}), Z = {best_val:.4f}",
                graph_image=graph_b64,
            )
        except Exception as exc:
            return Solution(
                status="error",
                method="graphical",
                message=f"Graphical solver error: {str(exc)}",
                steps=self.steps,
            )

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------

    def _obj(self, point) -> float:
        return sum(c * x for c, x in zip(self.lp.objective, point))

    def _find_feasible_corners(self) -> list:
        """
        Find all vertices of the feasible polytope by intersecting
        pairs of constraint lines (including the non-negativity axes).
        """
        lp = self.lp
        # Build list of (a, b, rhs) for each half-plane: a*x1 + b*x2 <= rhs
        half_planes = []
        for con in lp.constraints:
            a, b = con.coefficients[0], con.coefficients[1]
            rhs = con.rhs
            if con.inequality == "<=":
                half_planes.append((a, b, rhs))
            elif con.inequality == ">=":
                half_planes.append((-a, -b, -rhs))
            elif con.inequality == "=":
                half_planes.append((a, b, rhs))
                half_planes.append((-a, -b, -rhs))

        # Non-negativity constraints
        if lp.non_negative[0]:
            half_planes.append((-1, 0, 0))  # x1 >= 0
        if lp.non_negative[1]:
            half_planes.append((0, -1, 0))  # x2 >= 0

        # All bounding lines (as equality forms for intersection)
        lines = []
        for con in lp.constraints:
            lines.append((con.coefficients[0], con.coefficients[1], con.rhs))
        if lp.non_negative[0]:
            lines.append((1, 0, 0))
        if lp.non_negative[1]:
            lines.append((0, 1, 0))

        corners = []
        for (a1, b1, c1), (a2, b2, c2) in itertools.combinations(lines, 2):
            pt = self._intersect(a1, b1, c1, a2, b2, c2)
            if pt is None:
                continue
            if self._is_feasible(pt, half_planes):
                corners.append(pt)

        # Deduplicate
        unique = []
        for pt in corners:
            if not any(abs(pt[0] - u[0]) < 1e-6 and abs(pt[1] - u[1]) < 1e-6 for u in unique):
                unique.append(pt)

        return unique

    @staticmethod
    def _intersect(a1, b1, c1, a2, b2, c2):
        """Solve the 2×2 system: a1x+b1y=c1, a2x+b2y=c2."""
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-10:
            return None
        x = (c1 * b2 - c2 * b1) / det
        y = (a1 * c2 - a2 * c1) / det
        return (x, y)

    @staticmethod
    def _is_feasible(pt, half_planes, tol=1e-6) -> bool:
        """Check if a point satisfies all half-planes a*x + b*y <= rhs."""
        x, y = pt
        for a, b, rhs in half_planes:
            if a * x + b * y > rhs + tol:
                return False
        return True

    def _evaluate_corners(self, corners):
        """Return (best_point, best_value) depending on direction."""
        lp = self.lp
        vals = [(pt, self._obj(pt)) for pt in corners]
        if lp.direction == "max":
            return max(vals, key=lambda t: t[1])
        else:
            return min(vals, key=lambda t: t[1])

    # ------------------------------------------------------------------
    # Plotting
    # ------------------------------------------------------------------

    def _plot(self, corners: list, optimal: tuple) -> str:
        """Create a matplotlib figure and return it as a base64 PNG string."""
        lp = self.lp
        fig, ax = plt.subplots(figsize=(7, 6), facecolor="#fafafa")
        ax.set_facecolor("#f8f9fa")

        # Determine plot bounds
        all_x = [p[0] for p in corners] + [0]
        all_y = [p[1] for p in corners] + [0]
        x_max = max(all_x) * 1.35 + 2
        y_max = max(all_y) * 1.35 + 2
        x_min = min(min(all_x) * 1.1 - 1, -0.5)
        y_min = min(min(all_y) * 1.1 - 1, -0.5)

        x_range = np.linspace(x_min, x_max, 800)

        # --- Draw feasible region polygon ---
        if len(corners) >= 3:
            # Sort corners by angle for a convex hull appearance
            cx = sum(p[0] for p in corners) / len(corners)
            cy = sum(p[1] for p in corners) / len(corners)
            sorted_corners = sorted(corners, key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
            poly_x = [p[0] for p in sorted_corners] + [sorted_corners[0][0]]
            poly_y = [p[1] for p in sorted_corners] + [sorted_corners[0][1]]
            ax.fill(poly_x, poly_y, color=self.FEASIBLE_COLOR, alpha=0.45, label="Feasible Region", zorder=1)
            ax.plot(poly_x, poly_y, color="#52b788", linewidth=1.2, linestyle="--", zorder=2)

        # --- Draw constraint lines ---
        for idx, con in enumerate(lp.constraints):
            a, b = con.coefficients[0], con.coefficients[1]
            rhs = con.rhs
            color = self.COLORS[idx % len(self.COLORS)]

            if abs(b) > 1e-10:
                y_vals = (rhs - a * x_range) / b
                label = f"{a:g}x₁ + {b:g}x₂ {con.inequality} {rhs:g}"
                ax.plot(x_range, y_vals, color=color, linewidth=2, label=label, zorder=3)
            else:
                # Vertical line
                xv = rhs / a if abs(a) > 1e-10 else 0
                label = f"{a:g}x₁ {con.inequality} {rhs:g}"
                ax.axvline(x=xv, color=color, linewidth=2, label=label, zorder=3)

        # --- Non-negativity axes ---
        ax.axhline(y=0, color="#333", linewidth=1.5, zorder=4)
        ax.axvline(x=0, color="#333", linewidth=1.5, zorder=4)

        # --- Corner points ---
        for pt in corners:
            is_opt = (abs(pt[0] - optimal[0]) < 1e-5 and abs(pt[1] - optimal[1]) < 1e-5)
            color = self.OPTIMAL_COLOR if is_opt else "#555"
            size = 90 if is_opt else 40
            ax.scatter(*pt, color=color, s=size, zorder=6)
            ax.annotate(
                f"({pt[0]:.2f}, {pt[1]:.2f})",
                xy=pt,
                xytext=(8, 8),
                textcoords="offset points",
                fontsize=8.5,
                color=color,
                fontweight="bold" if is_opt else "normal",
            )

        # --- Objective direction arrow ---
        obj_len = min(x_max, y_max) * 0.18
        dx, dy = lp.objective[0], lp.objective[1]
        norm = (dx**2 + dy**2) ** 0.5 or 1
        ax.annotate(
            "",
            xy=(optimal[0] + dx / norm * obj_len, optimal[1] + dy / norm * obj_len),
            xytext=(optimal[0], optimal[1]),
            arrowprops=dict(arrowstyle="->", color=self.OPTIMAL_COLOR, lw=2),
            zorder=7,
        )

        # --- Labels & styling ---
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel(lp.variable_names[0], fontsize=11, color=self.AXIS_COLOR)
        ax.set_ylabel(lp.variable_names[1], fontsize=11, color=self.AXIS_COLOR)
        ax.set_title(
            f"Graphical Solution — {lp.direction.upper()} Z = {lp.objective_str()}",
            fontsize=12,
            fontweight="bold",
            color="#1a1a2e",
            pad=12,
        )
        ax.grid(True, alpha=0.3, linestyle=":")
        ax.legend(fontsize=8.5, loc="upper right", framealpha=0.85)
        plt.tight_layout()

        # --- Convert to base64 ---
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
