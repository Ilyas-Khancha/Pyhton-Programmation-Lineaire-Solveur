"""
SimplexSolver — full OOP simplex implementation with Big-M support.

Algorithm overview:
  1. Convert all constraints to standard form (add slacks / artificials).
  2. Build initial tableau.
  3. Iterate: choose pivot column (most negative reduced cost for max),
     choose pivot row (minimum ratio test), pivot, record step.
  4. Detect optimality / infeasibility / unboundedness.
  5. Return a Solution with all tableau snapshots.
"""

import copy
from models.linear_program import LinearProgram
from models.solution import Solution

BIG_M = 1e6  # Big-M penalty constant


class SimplexSolver:
    """
    Solves a LinearProgram using the revised simplex / Big-M method.

    Usage:
        solver = SimplexSolver(lp)
        solution = solver.solve()
    """

    def __init__(self, lp: LinearProgram):
        self.lp = lp
        self.steps = []          # list of tableau snapshots
        self.tableau = []        # current tableau (list of lists)
        self.basis = []          # indices of basic variables
        self.col_labels = []     # column headers
        self.artificial_vars = []  # indices of artificial variables

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def solve(self) -> Solution:
        """Run the full simplex algorithm and return a Solution."""
        try:
            self._build_tableau()
            result = self._iterate()
            return result
        except Exception as exc:
            return Solution(
                status="error",
                method="simplex",
                message=f"Solver error: {str(exc)}",
                steps=self.steps,
            )

    # ------------------------------------------------------------------
    # Tableau construction
    # ------------------------------------------------------------------

    def _build_tableau(self):
        """
        Convert the LP to augmented standard form and build the tableau.

        Variables layout (columns):
            [ x1 … xn | s1 … sm (slacks) | a1 … ak (artificials) | RHS ]
        """
        lp = self.lp
        n = lp.num_vars
        m = len(lp.constraints)

        # For minimisation convert to maximisation: min c·x = max -c·x
        if lp.direction == "min":
            obj = [-c for c in lp.objective]
        else:
            obj = list(lp.objective)

        # Count extra variables
        num_slack = 0
        num_artificial = 0

        # Pass 1: determine how many slacks / artificials we need
        slack_map = []    # (constraint_index, +1/-1) for slack sign
        art_map = []      # constraint_index for artificials

        for i, con in enumerate(lp.constraints):
            if con.inequality == "<=":
                slack_map.append((i, +1))
            elif con.inequality == ">=":
                slack_map.append((i, -1))   # surplus (subtract)
                art_map.append(i)
            elif con.inequality == "=":
                art_map.append(i)

        num_slack = len(lp.constraints)  # one slack/surplus per row
        num_artificial = len(art_map)

        total_cols = n + num_slack + num_artificial + 1  # +1 for RHS

        # Column labels
        self.col_labels = (
            [lp.variable_names[i] for i in range(n)]
            + [f"s{i+1}" for i in range(num_slack)]
            + [f"a{i+1}" for i in range(num_artificial)]
            + ["RHS"]
        )

        art_start = n + num_slack  # column index where artificials begin
        self.artificial_vars = list(range(art_start, art_start + num_artificial))

        # Build rows
        tableau = []
        self.basis = []

        art_counter = 0
        slack_index = n  # slack columns start at index n

        for row_i, con in enumerate(lp.constraints):
            row = [0.0] * total_cols
            # Decision variable coefficients
            for j, coef in enumerate(con.coefficients):
                row[j] = coef
            # RHS
            rhs = con.rhs
            # Handle negative RHS by flipping the row
            if rhs < 0:
                row = [-v for v in row]
                rhs = -rhs
                # flip inequality sense (already encoded in slack sign)
            row[-1] = rhs

            # Slack / surplus
            if con.inequality == "<=":
                row[slack_index] = 1.0
                self.basis.append(slack_index)
            elif con.inequality == ">=":
                row[slack_index] = -1.0  # surplus variable
                # artificial
                row[art_start + art_counter] = 1.0
                self.basis.append(art_start + art_counter)
                art_counter += 1
            elif con.inequality == "=":
                row[slack_index] = 0.0  # no slack
                row[art_start + art_counter] = 1.0
                self.basis.append(art_start + art_counter)
                art_counter += 1

            slack_index += 1
            tableau.append(row)

        # Objective row (last row): maximise -cj*xj (we store reduced costs)
        obj_row = [0.0] * total_cols
        for j in range(n):
            obj_row[j] = -obj[j]   # reduced cost = -cj initially

        # Big-M penalties for artificials in objective
        for ai in self.artificial_vars:
            obj_row[ai] = BIG_M

        # Eliminate artificials from objective (make basis feasible for obj row)
        for row_i, bv in enumerate(self.basis):
            if bv in self.artificial_vars:
                factor = obj_row[bv]
                for k in range(total_cols):
                    obj_row[k] -= factor * tableau[row_i][k]

        tableau.append(obj_row)
        self.tableau = tableau

        self._record_step("Initial Tableau", pivot_row=None, pivot_col=None)

    # ------------------------------------------------------------------
    # Simplex iterations
    # ------------------------------------------------------------------

    def _iterate(self) -> Solution:
        MAX_ITER = 200

        for iteration in range(MAX_ITER):
            pivot_col = self._choose_pivot_col()
            if pivot_col is None:
                # Optimal
                return self._extract_solution()

            pivot_row = self._choose_pivot_row(pivot_col)
            if pivot_row is None:
                return Solution(
                    status="unbounded",
                    method="simplex",
                    message="The problem is unbounded (no finite optimum exists).",
                    steps=self.steps,
                )

            self._pivot(pivot_row, pivot_col)
            self.basis[pivot_row] = pivot_col
            self._record_step(
                f"Iteration {iteration+1}: pivot on col {self.col_labels[pivot_col]}, row {pivot_row+1}",
                pivot_row=pivot_row,
                pivot_col=pivot_col,
            )

        return Solution(
            status="error",
            method="simplex",
            message="Maximum iterations reached — problem may be cycling.",
            steps=self.steps,
        )

    def _choose_pivot_col(self):
        """Most negative reduced cost in the objective row (maximisation)."""
        obj_row = self.tableau[-1]
        n_cols = len(obj_row) - 1  # exclude RHS
        min_val = -1e-8
        pivot_col = None
        for j in range(n_cols):
            if obj_row[j] < min_val:
                min_val = obj_row[j]
                pivot_col = j
        return pivot_col

    def _choose_pivot_row(self, pivot_col: int):
        """Minimum ratio test (θ-rule)."""
        min_ratio = float("inf")
        pivot_row = None
        for i in range(len(self.tableau) - 1):  # exclude objective row
            entry = self.tableau[i][pivot_col]
            if entry > 1e-8:
                ratio = self.tableau[i][-1] / entry
                if ratio < min_ratio - 1e-8:
                    min_ratio = ratio
                    pivot_row = i
        return pivot_row

    def _pivot(self, pivot_row: int, pivot_col: int):
        """Perform a pivot operation, updating all rows."""
        pivot_element = self.tableau[pivot_row][pivot_col]
        n_rows = len(self.tableau)
        n_cols = len(self.tableau[0])

        # Normalise pivot row
        self.tableau[pivot_row] = [v / pivot_element for v in self.tableau[pivot_row]]

        # Eliminate pivot column from all other rows
        for i in range(n_rows):
            if i == pivot_row:
                continue
            factor = self.tableau[i][pivot_col]
            if abs(factor) < 1e-12:
                continue
            self.tableau[i] = [
                self.tableau[i][k] - factor * self.tableau[pivot_row][k]
                for k in range(n_cols)
            ]

    # ------------------------------------------------------------------
    # Solution extraction
    # ------------------------------------------------------------------

    def _extract_solution(self) -> Solution:
        lp = self.lp
        n = lp.num_vars
        obj_row = self.tableau[-1]
        num_rows = len(self.tableau) - 1  # data rows

        # Check for artificial variables still in basis (infeasible)
        for bv in self.basis:
            if bv in self.artificial_vars:
                row_i = self.basis.index(bv)
                if abs(self.tableau[row_i][-1]) > 1e-6:
                    return Solution(
                        status="infeasible",
                        method="simplex",
                        message="The problem is infeasible (constraints cannot be satisfied simultaneously).",
                        steps=self.steps,
                    )

        # Extract variable values
        values = {lp.variable_names[j]: 0.0 for j in range(n)}
        for row_i, bv in enumerate(self.basis):
            if bv < n:
                values[lp.variable_names[bv]] = round(self.tableau[row_i][-1], 6)

        # Objective value:
        # The objective row accumulates: row[-1] = maximised value (internal).
        # For maximisation: internal max  = real max  → report as-is.
        # For minimisation: we negated c, so internal max = -real min → negate back.
        obj_val = obj_row[-1]
        if lp.direction == "min":
            obj_val = -obj_val

        obj_val = round(obj_val, 6)

        msg = (
            f"Optimal solution found.\n"
            f"Z = {obj_val}\n"
            + "\n".join(f"  {k} = {v}" for k, v in values.items())
        )

        return Solution(
            status="optimal",
            method="simplex",
            objective_value=obj_val,
            variables=values,
            steps=self.steps,
            message=msg,
        )

    # ------------------------------------------------------------------
    # Step recording
    # ------------------------------------------------------------------

    def _record_step(self, title: str, pivot_row, pivot_col):
        """Snapshot the current tableau into self.steps."""
        tableau_copy = copy.deepcopy(self.tableau)
        n_cols = len(self.col_labels)

        # Format cells for display
        rows = []
        for r_i, row in enumerate(tableau_copy):
            is_obj = r_i == len(tableau_copy) - 1
            basis_label = (
                "Z" if is_obj else self.col_labels[self.basis[r_i]]
            )
            cells = []
            for c_i, val in enumerate(row):
                is_pivot = (r_i == pivot_row and c_i == pivot_col)
                cells.append({
                    "value": f"{val:.4f}",
                    "is_pivot": is_pivot,
                })
            rows.append({"basis": basis_label, "cells": cells})

        self.steps.append({
            "title": title,
            "col_labels": self.col_labels,
            "rows": rows,
            "pivot_row": pivot_row,
            "pivot_col": pivot_col,
        })
