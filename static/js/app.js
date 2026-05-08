/**
 * LP Solver — Frontend JS
 * Handles: form generation, segmented controls, solve dispatch, result rendering.
 */

// ═══════════════════════════════════════════════════
// State
// ═══════════════════════════════════════════════════
const state = {
  method: "simplex",
  direction: "max",
  numVars: 2,
  numCons: 3,
};

// ═══════════════════════════════════════════════════
// DOM refs
// ═══════════════════════════════════════════════════
const $ = id => document.getElementById(id);
const methodSeg     = $("method-seg");
const directionSeg  = $("direction-seg");
const numVarsInput  = $("num-vars");
const numConsInput  = $("num-cons");
const btnGenerate   = $("btn-generate");
const btnSolve      = $("btn-solve");
const btnRandom     = $("btn-random");
const btnReset      = $("btn-reset");
const lpForm        = $("lp-form");
const objRow        = $("obj-row");
const objLabel      = $("obj-label");
const consContainer = $("constraints-container");
const nonnegRow     = $("nonneg-checkboxes");
const resultsPanel  = $("results-content");
const placeholder   = $("results-placeholder");
const loader        = $("loader");
const graphicalHint = $("graphical-hint");

// ═══════════════════════════════════════════════════
// Segmented controls
// ═══════════════════════════════════════════════════
function bindSeg(container, onChange) {
  container.querySelectorAll(".seg-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      container.querySelectorAll(".seg-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      onChange(btn.dataset.val);
    });
  });
}

bindSeg(methodSeg, val => {
  state.method = val;
  checkGraphicalWarning();
});

bindSeg(directionSeg, val => {
  state.direction = val;
  updateObjLabel();
});

// ═══════════════════════════════════════════════════
// Steppers
// ═══════════════════════════════════════════════════
document.querySelectorAll(".step-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const target = $(btn.dataset.target);
    let val = parseInt(target.value) + parseInt(btn.dataset.delta);
    val = Math.max(parseInt(target.min), Math.min(parseInt(target.max), val));
    target.value = val;
    target.dispatchEvent(new Event("input"));
  });
});

numVarsInput.addEventListener("input", () => {
  state.numVars = parseInt(numVarsInput.value) || 2;
  checkGraphicalWarning();
});
numConsInput.addEventListener("input", () => { state.numCons = parseInt(numConsInput.value) || 1; });

function checkGraphicalWarning() {
  const show = state.method === "graphical" && state.numVars !== 2;
  graphicalHint.style.display = show ? "block" : "none";
}

// ═══════════════════════════════════════════════════
// Variable helpers
// ═══════════════════════════════════════════════════
const varName = i => `x<sub>${i+1}</sub>`;   // HTML subscript
const varPlain = i => `x${i+1}`;             // plain text

// ═══════════════════════════════════════════════════
// Build the objective row
// ═══════════════════════════════════════════════════
function updateObjLabel() {
  if (objLabel) {
    const dir = state.direction === "max" ? "Max" : "Min";
    objLabel.textContent = `${dir}  Z =`;
  }
}

function buildObjRow(numVars, existingCoefs = []) {
  objRow.innerHTML = "";
  for (let i = 0; i < numVars; i++) {
    const term = document.createElement("div");
    term.className = "eq-term";
    const inp = document.createElement("input");
    inp.type = "number";
    inp.step = "any";
    inp.className = "coef-input";
    inp.dataset.varIndex = i;
    inp.dataset.role = "obj";
    inp.value = existingCoefs[i] !== undefined ? existingCoefs[i] : "";
    inp.placeholder = "0";
    const lbl = document.createElement("span");
    lbl.className = "var-label";
    lbl.innerHTML = varName(i);

    term.appendChild(inp);
    term.appendChild(lbl);

    if (i < numVars - 1) {
      const op = document.createElement("span");
      op.className = "op-label";
      op.textContent = "+";
      term.appendChild(op);
    }
    objRow.appendChild(term);
  }
}

// ═══════════════════════════════════════════════════
// Build constraint rows
// ═══════════════════════════════════════════════════
function buildConstraints(numVars, numCons, existingCons = []) {
  consContainer.innerHTML = "";
  for (let r = 0; r < numCons; r++) {
    const con = existingCons[r] || {};
    const row = document.createElement("div");
    row.className = "constraint-row";

    const idx = document.createElement("span");
    idx.className = "con-index";
    idx.textContent = `C${r+1}`;
    row.appendChild(idx);

    for (let i = 0; i < numVars; i++) {
      const term = document.createElement("div");
      term.className = "eq-term";

      const inp = document.createElement("input");
      inp.type = "number";
      inp.step = "any";
      inp.className = "coef-input";
      inp.dataset.row = r;
      inp.dataset.col = i;
      inp.dataset.role = "con";
      inp.value = (con.coefficients && con.coefficients[i] !== undefined) ? con.coefficients[i] : "";
      inp.placeholder = "0";

      const lbl = document.createElement("span");
      lbl.className = "var-label";
      lbl.innerHTML = varName(i);

      term.appendChild(inp);
      term.appendChild(lbl);

      if (i < numVars - 1) {
        const op = document.createElement("span");
        op.className = "op-label";
        op.textContent = "+";
        term.appendChild(op);
      }
      row.appendChild(term);
    }

    // Inequality select
    const sel = document.createElement("select");
    sel.className = "ineq-select";
    sel.dataset.row = r;
    ["<=", ">=", "="].forEach(op => {
      const opt = document.createElement("option");
      opt.value = op;
      opt.textContent = op;
      if (con.inequality === op) opt.selected = true;
      sel.appendChild(opt);
    });
    if (!con.inequality) sel.value = "<=";
    row.appendChild(sel);

    // RHS
    const rhsInp = document.createElement("input");
    rhsInp.type = "number";
    rhsInp.step = "any";
    rhsInp.className = "coef-input rhs-input";
    rhsInp.dataset.row = r;
    rhsInp.dataset.role = "rhs";
    rhsInp.value = con.rhs !== undefined ? con.rhs : "";
    rhsInp.placeholder = "0";
    row.appendChild(rhsInp);

    consContainer.appendChild(row);
  }
}

// ═══════════════════════════════════════════════════
// Build non-negativity checkboxes
// ═══════════════════════════════════════════════════
function buildNonNeg(numVars, existingNN = []) {
  nonnegRow.innerHTML = "";
  for (let i = 0; i < numVars; i++) {
    const label = document.createElement("label");
    label.className = "nonneg-item";
    const chk = document.createElement("input");
    chk.type = "checkbox";
    chk.dataset.varIndex = i;
    chk.checked = existingNN[i] !== undefined ? existingNN[i] : true;
    const span = document.createElement("span");
    span.innerHTML = `${varPlain(i)} ≥ 0`;
    label.appendChild(chk);
    label.appendChild(span);
    nonnegRow.appendChild(label);
  }
}

// ═══════════════════════════════════════════════════
// Read form data into payload object
// ═══════════════════════════════════════════════════
function readFormData() {
  const numVars = state.numVars;
  const numCons = state.numCons;

  // Objective
  const objective = [];
  objRow.querySelectorAll("input[data-role=obj]").forEach(inp => {
    objective.push(parseFloat(inp.value) || 0);
  });

  // Constraints
  const constraints = [];
  for (let r = 0; r < numCons; r++) {
    const coefs = [];
    consContainer.querySelectorAll(`input[data-role=con][data-row="${r}"]`).forEach(inp => {
      coefs.push(parseFloat(inp.value) || 0);
    });
    const sel = consContainer.querySelector(`select[data-row="${r}"]`);
    const rhs = parseFloat(consContainer.querySelector(`input[data-role=rhs][data-row="${r}"]`)?.value) || 0;
    constraints.push({ coefficients: coefs, inequality: sel?.value || "<=", rhs });
  }

  // Non-negativity
  const nonNeg = [];
  nonnegRow.querySelectorAll("input[type=checkbox]").forEach(chk => nonNeg.push(chk.checked));

  return {
    method: state.method,
    direction: state.direction,
    num_vars: numVars,
    num_constraints: numCons,
    objective,
    constraints,
    non_negative: nonNeg,
  };
}

// ═══════════════════════════════════════════════════
// Populate form from example object
// ═══════════════════════════════════════════════════
function loadExample(ex) {
  // Sync state
  state.direction = ex.direction || "max";
  state.numVars = ex.num_vars || 2;
  state.numCons = ex.num_constraints || (ex.constraints || []).length;

  numVarsInput.value = state.numVars;
  numConsInput.value = state.numCons;

  // Sync seg buttons
  methodSeg.querySelectorAll(".seg-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.val === state.method);
  });
  directionSeg.querySelectorAll(".seg-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.val === state.direction);
  });

  buildObjRow(state.numVars, ex.objective || []);
  buildConstraints(state.numVars, state.numCons, ex.constraints || []);
  buildNonNeg(state.numVars, ex.non_negative);
  updateObjLabel();
  lpForm.style.display = "flex";
}

// ═══════════════════════════════════════════════════
// Generate form button
// ═══════════════════════════════════════════════════
btnGenerate.addEventListener("click", () => {
  state.numVars = parseInt(numVarsInput.value) || 2;
  state.numCons = parseInt(numConsInput.value) || 1;
  buildObjRow(state.numVars);
  buildConstraints(state.numVars, state.numCons);
  buildNonNeg(state.numVars);
  updateObjLabel();
  lpForm.style.display = "flex";
  checkGraphicalWarning();
});

// ═══════════════════════════════════════════════════
// Solve
// ═══════════════════════════════════════════════════
btnSolve.addEventListener("click", async () => {
  const payload = readFormData();
  loader.style.display = "flex";
  try {
    const res = await fetch("/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    renderResults(data);
  } catch (err) {
    renderResults({ status: "error", message: "Network error: " + err.message, steps: [] });
  } finally {
    loader.style.display = "none";
  }
});

// ═══════════════════════════════════════════════════
// Random problem
// ═══════════════════════════════════════════════════
btnRandom.addEventListener("click", async () => {
  const res = await fetch("/random");
  const ex = await res.json();
  loadExample(ex);
  clearResults();
});

// ═══════════════════════════════════════════════════
// Reset
// ═══════════════════════════════════════════════════
btnReset.addEventListener("click", () => {
  loadExample(window.__DEFAULT_EXAMPLE__);
  clearResults();
});

function clearResults() {
  resultsPanel.style.display = "none";
  resultsPanel.innerHTML = "";
  placeholder.style.display = "flex";
}

// ═══════════════════════════════════════════════════
// Result rendering
// ═══════════════════════════════════════════════════
function renderResults(data) {
  placeholder.style.display = "none";
  resultsPanel.style.display = "block";
  resultsPanel.innerHTML = "";

  const status = data.status || "error";

  // ── Summary card ──
  const card = document.createElement("div");
  card.className = `solution-card ${status}`;

  const statusEl = document.createElement("div");
  statusEl.className = `sol-status ${status}`;
  statusEl.textContent = status === "optimal" ? "✓ Optimal Solution Found"
    : status === "infeasible" ? "✗ Infeasible"
    : status === "unbounded" ? "∞ Unbounded"
    : "⚠ Error";
  card.appendChild(statusEl);

  if (status === "optimal" && data.objective_value !== null) {
    const objEl = document.createElement("div");
    objEl.className = "sol-obj";
    const dir = state.direction === "max" ? "Max" : "Min";
    objEl.innerHTML = `Z<sub>${dir}</sub> = <span>${data.objective_value}</span>`;
    card.appendChild(objEl);

    if (data.variables && Object.keys(data.variables).length) {
      const varRow = document.createElement("div");
      varRow.className = "sol-vars";
      Object.entries(data.variables).forEach(([k, v]) => {
        const chip = document.createElement("div");
        chip.className = "sol-var-chip";
        chip.innerHTML = `<strong>${k}</strong> = ${v}`;
        varRow.appendChild(chip);
      });
      card.appendChild(varRow);
    }
  } else {
    const msg = document.createElement("p");
    msg.style.cssText = "font-size:0.9rem;color:var(--text2);margin-top:.5rem;";
    msg.textContent = data.message || "No solution.";
    card.appendChild(msg);
  }

  resultsPanel.appendChild(card);

  // ── Export button ──
  if (status === "optimal") {
    const expBtn = document.createElement("button");
    expBtn.className = "btn btn-export";
    expBtn.textContent = "⬇ Export Results (PNG)";
    expBtn.addEventListener("click", () => exportResults(data));
    resultsPanel.appendChild(expBtn);
  }

  // ── Graphical plot ──
  if (data.method === "graphical" && data.graph_image) {
    const graphSec = document.createElement("div");
    graphSec.className = "graph-section";

    const title = document.createElement("div");
    title.className = "tableaux-title";
    title.textContent = "Feasible Region Plot";
    graphSec.appendChild(title);

    const img = document.createElement("img");
    img.className = "graph-img";
    img.src = `data:image/png;base64,${data.graph_image}`;
    img.alt = "Graphical solution";
    graphSec.appendChild(img);

    // Corner point table
    const corners = data.steps.find(s => s.corners)?.corners;
    if (corners && corners.length) {
      const tbl = document.createElement("table");
      tbl.className = "corner-table";
      tbl.innerHTML = `<thead><tr><th>Corner Point</th><th>Z value</th><th>Status</th></tr></thead>`;
      const tbody = document.createElement("tbody");
      corners.forEach(c => {
        const tr = document.createElement("tr");
        if (c.optimal) tr.className = "optimal-row";
        tr.innerHTML = `
          <td>(${c.point[0]}, ${c.point[1]})</td>
          <td>${c.value}</td>
          <td>${c.optimal ? "★ Optimal" : ""}</td>`;
        tbody.appendChild(tr);
      });
      tbl.appendChild(tbody);
      graphSec.appendChild(tbl);
    }

    resultsPanel.appendChild(graphSec);
  }

  // ── Simplex tableaux ──
  if (data.method === "simplex" && data.steps && data.steps.length) {
    const sec = document.createElement("div");
    sec.className = "tableaux-section";

    const header = document.createElement("div");
    header.style.cssText = "display:flex;align-items:center;gap:1rem;margin-bottom:.75rem;";

    const title = document.createElement("div");
    title.className = "tableaux-title";
    title.style.margin = "0";
    title.textContent = `Simplex Tableau (${data.steps.length} step${data.steps.length > 1 ? "s" : ""})`;
    header.appendChild(title);

    // Step-by-step toggle
    const toggleLabel = document.createElement("label");
    toggleLabel.className = "steps-toggle";
    const chk = document.createElement("input");
    chk.type = "checkbox";
    chk.checked = true;
    chk.id = "steps-chk";
    const toggleSpan = document.createElement("span");
    toggleSpan.textContent = "Show all steps";
    toggleLabel.appendChild(chk);
    toggleLabel.appendChild(toggleSpan);
    header.appendChild(toggleLabel);
    sec.appendChild(header);

    const stepsWrap = document.createElement("div");
    stepsWrap.id = "steps-wrap";

    data.steps.forEach((step, si) => {
      const block = document.createElement("div");
      block.className = "step-block";

      const lbl = document.createElement("div");
      lbl.className = "step-label";
      lbl.textContent = step.title || `Step ${si + 1}`;
      block.appendChild(lbl);

      const scroll = document.createElement("div");
      scroll.className = "tableau-scroll";

      const tbl = document.createElement("table");
      tbl.className = "tableau-table";

      // Header row
      const thead = document.createElement("thead");
      const headRow = document.createElement("tr");
      const thBasis = document.createElement("th");
      thBasis.textContent = "Basis";
      headRow.appendChild(thBasis);
      (step.col_labels || []).forEach(lbl => {
        const th = document.createElement("th");
        th.textContent = lbl;
        headRow.appendChild(th);
      });
      thead.appendChild(headRow);
      tbl.appendChild(thead);

      // Body
      const tbody = document.createElement("tbody");
      (step.rows || []).forEach((row, ri) => {
        const tr = document.createElement("tr");
        const tdBasis = document.createElement("td");
        tdBasis.className = "basis-col";
        tdBasis.textContent = row.basis;
        tr.appendChild(tdBasis);
        (row.cells || []).forEach(cell => {
          const td = document.createElement("td");
          td.textContent = cell.value;
          if (cell.is_pivot) td.className = "pivot-cell";
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
      tbl.appendChild(tbody);

      scroll.appendChild(tbl);
      block.appendChild(scroll);

      // Only show last step by default
      if (si < data.steps.length - 1) block.style.display = "none";
      stepsWrap.appendChild(block);
    });

    sec.appendChild(stepsWrap);
    resultsPanel.appendChild(sec);

    // Toggle listener
    chk.addEventListener("change", () => {
      stepsWrap.querySelectorAll(".step-block").forEach((block, i) => {
        block.style.display = (chk.checked || i === data.steps.length - 1) ? "block" : "none";
      });
    });
  }
}

// ═══════════════════════════════════════════════════
// Export as PNG (canvas capture)
// ═══════════════════════════════════════════════════
function exportResults(data) {
  if (data.graph_image) {
    const a = document.createElement("a");
    a.href = `data:image/png;base64,${data.graph_image}`;
    a.download = "lp_graphical_solution.png";
    a.click();
  } else {
    // For simplex, create a simple text summary
    let txt = `LP Solver Result\n`;
    txt += `=================\n`;
    txt += `Status: ${data.status}\n`;
    txt += `Z = ${data.objective_value}\n`;
    Object.entries(data.variables || {}).forEach(([k,v]) => {
      txt += `${k} = ${v}\n`;
    });
    const blob = new Blob([txt], { type: "text/plain" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "lp_solution.txt";
    a.click();
  }
}

// ═══════════════════════════════════════════════════
// Init — load default example
// ═══════════════════════════════════════════════════
document.addEventListener("DOMContentLoaded", () => {
  loadExample(window.__DEFAULT_EXAMPLE__);
});
