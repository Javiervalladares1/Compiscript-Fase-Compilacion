/* IDE de Compiscript: editor, diagnosticos, AST, simbolos, TAC, MIPS y SPIM.
 * No contiene logica de compilacion: solo envia el codigo a /api/compile. */

(function () {
  "use strict";

  const editor = document.getElementById("editor");
  const gutter = document.getElementById("gutter");
  const status = document.getElementById("status");
  const diagnosticsList = document.getElementById("diagnostics-list");
  const diagBadge = document.getElementById("diag-badge");
  const astTree = document.getElementById("ast-tree");
  const symbolsTable = document.getElementById("symbols-table");
  const cursorPosition = document.getElementById("cursor-position");
  const compileButton = document.getElementById("compile");
  const strictToggle = document.getElementById("strict");
  const runButton = document.getElementById("run");
  const phase = document.getElementById("phase");
  const allocation = document.getElementById("allocation");
  const exampleSelect = document.getElementById("example");
  const loadButton = document.getElementById("load-example");
  const tacOutput = document.getElementById("tac-output");
  const mipsOutput = document.getElementById("mips-output");
  const executionOutput = document.getElementById("execution-output");
  const downloadTac = document.getElementById("download-tac");
  const downloadMips = document.getElementById("download-mips");

  const STARTER = [
    "// Factorial recursivo: salida 120, 720, 5040",
    "function factorial(n: integer): integer {",
    "  if (n <= 1) { return 1; }",
    "  return n * factorial(n - 1);",
    "}",
    "print(factorial(5));",
    "print(factorial(6));",
    "print(factorial(7));",
    ""
  ].join("\n");

  let errorLines = new Set();
  let busy = false;
  let latestRequest = 0;
  let artifacts = { tac: null, mips: null };

  // --- editor ------------------------------------------------------------

  function renderGutter() {
    const total = editor.value.split("\n").length;
    let html = "";
    for (let i = 1; i <= total; i += 1) {
      html += errorLines.has(i) ? '<span class="hl">' + i + "</span>\n" : i + "\n";
    }
    gutter.innerHTML = html;
    gutter.scrollTop = editor.scrollTop;
  }

  function updateCursor() {
    const upto = editor.value.slice(0, editor.selectionStart);
    const lines = upto.split("\n");
    cursorPosition.textContent = "Ln " + lines.length + ", Col " + (lines[lines.length - 1].length + 1);
  }

  function goToPosition(line, column) {
    const lines = editor.value.split("\n");
    let offset = 0;
    for (let i = 0; i < line - 1 && i < lines.length; i += 1) {
      offset += lines[i].length + 1;
    }
    offset += Math.max(0, column - 1);
    editor.focus();
    editor.setSelectionRange(offset, offset);
    updateCursor();
  }

  editor.addEventListener("input", renderGutter);
  editor.addEventListener("input", invalidate);
  editor.addEventListener("scroll", function () { gutter.scrollTop = editor.scrollTop; });
  editor.addEventListener("keyup", updateCursor);
  editor.addEventListener("click", updateCursor);

  editor.addEventListener("keydown", function (event) {
    if (event.key === "Tab") {
      event.preventDefault();
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      editor.value = editor.value.slice(0, start) + "  " + editor.value.slice(end);
      editor.selectionStart = editor.selectionEnd = start + 2;
      renderGutter();
      invalidate();
    }
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      compile();
    }
  });

  // --- pestanas ----------------------------------------------------------

  function showTab(name) {
    document.querySelectorAll(".tab").forEach(function (tab) {
      const active = tab.dataset.tab === name;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", String(active));
    });
    document.querySelectorAll(".tab-panel").forEach(function (panel) {
      panel.classList.toggle("active", panel.id === "panel-" + name);
    });
  }

  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      showTab(tab.dataset.tab);
    });
  });

  // --- render de resultados ----------------------------------------------

  function setStatus(kind, text) {
    status.className = "status " + kind;
    status.textContent = text;
  }

  function renderDiagnostics(diagnostics) {
    errorLines = new Set();
    diagnosticsList.innerHTML = "";

    if (!diagnostics.length) {
      diagnosticsList.innerHTML = '<p class="muted empty">Sin errores ni advertencias.</p>';
      diagBadge.textContent = "0";
      diagBadge.className = "badge";
      renderGutter();
      return;
    }

    let errors = 0;
    let warnings = 0;

    diagnostics.forEach(function (d) {
      if (d.severity === "error") { errors += 1; errorLines.add(d.line); } else { warnings += 1; }

      const item = document.createElement("div");
      item.className = "diagnostic " + d.severity;
      item.title = "Ir a la linea " + d.line;

      const loc = document.createElement("span");
      loc.className = "loc";
      loc.textContent = d.line + ":" + d.column;

      const code = document.createElement("span");
      code.className = "code";
      code.textContent = d.code;

      const msg = document.createElement("span");
      msg.className = "msg";
      msg.textContent = d.message;

      if (d.expectedType || d.actualType) {
        const types = document.createElement("span");
        types.className = "types";
        types.textContent =
          "esperado: " + (d.expectedType || "-") + "  ·  recibido: " + (d.actualType || "-");
        msg.appendChild(types);
      }

      item.appendChild(loc);
      item.appendChild(code);
      item.appendChild(msg);
      item.addEventListener("click", function () { goToPosition(d.line, d.column); });
      diagnosticsList.appendChild(item);
    });

    diagBadge.textContent = String(diagnostics.length);
    diagBadge.className = "badge" + (errors ? " has-errors" : warnings ? " has-warnings" : "");
    renderGutter();
  }

  function renderAst(node) {
    astTree.innerHTML = "";
    if (!node) {
      astTree.innerHTML =
        '<p class="muted empty">No se genero AST (revise los errores de sintaxis).</p>';
      return;
    }
    astTree.appendChild(buildAstNode(node));
  }

  function buildAstNode(node) {
    const container = document.createElement("div");
    container.className = "ast-node";

    const row = document.createElement("div");
    row.className = "ast-row";

    const children = node.children || [];
    const toggle = document.createElement("span");
    toggle.className = "ast-toggle";
    toggle.textContent = children.length ? "▾" : "·";

    const label = document.createElement("span");
    label.className = "ast-label";
    label.textContent = node.label;

    const meta = document.createElement("span");
    meta.className = "ast-meta";
    meta.textContent = node.span ? node.span.line + ":" + node.span.column : "";

    row.appendChild(toggle);
    row.appendChild(label);
    row.appendChild(meta);

    const type = node.attributes && node.attributes.resolved_type;
    if (type) {
      const typeTag = document.createElement("span");
      typeTag.className = "ast-type";
      typeTag.textContent = ":: " + type;
      row.appendChild(typeTag);
    }

    container.appendChild(row);

    if (children.length) {
      const childBox = document.createElement("div");
      childBox.className = "ast-children";
      children.forEach(function (child) { childBox.appendChild(buildAstNode(child)); });
      container.appendChild(childBox);

      toggle.addEventListener("click", function () {
        const collapsed = childBox.classList.toggle("collapsed");
        toggle.textContent = collapsed ? "▸" : "▾";
      });
    }
    return container;
  }

  function renderSymbols(rows) {
    if (!rows || !rows.length) {
      symbolsTable.innerHTML = '<p class="muted empty">La tabla de simbolos esta vacia.</p>';
      return;
    }
    const headers = ["Ambito", "Nombre", "Categoria", "Tipo", "Linea", "Col", "Detalles"];
    const keys = ["scope", "name", "category", "type", "line", "column", "details"];

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    headers.forEach(function (h) {
      const th = document.createElement("th");
      th.textContent = h;
      headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    rows.forEach(function (row) {
      const tr = document.createElement("tr");
      keys.forEach(function (key) {
        const td = document.createElement("td");
        if (key === "category") {
          const pill = document.createElement("span");
          pill.className = "pill";
          pill.textContent = row[key];
          td.appendChild(pill);
        } else {
          td.textContent = row[key];
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);

    symbolsTable.innerHTML = "";
    symbolsTable.appendChild(table);
  }

  // --- acciones ----------------------------------------------------------

  function updateControls() {
    compileButton.disabled = busy;
    runButton.disabled = busy || phase.value !== "mips";
    loadButton.disabled = busy;
    phase.disabled = busy;
    allocation.disabled = busy || phase.value !== "mips";
    strictToggle.disabled = busy;
    exampleSelect.disabled = busy;
  }

  function clearArtifacts() {
    artifacts = { tac: null, mips: null };
    tacOutput.textContent = "Compile en la fase MIPS para ver el código de tres direcciones.";
    mipsOutput.textContent = "El assembler MIPS aparecerá aquí.";
    executionOutput.textContent = "Pulse «Ejecutar en SPIM» para correr el programa.";
    downloadTac.disabled = true;
    downloadMips.disabled = true;
  }

  function invalidate() {
    latestRequest += 1;
    clearArtifacts();
    setStatus("idle", "Código u opciones modificadas: vuelve a compilar.");
    updateControls();
  }

  function compile(execute) {
    if (busy) { return; }
    execute = execute === true;
    const requestId = ++latestRequest;
    busy = true;
    clearArtifacts();
    updateControls();
    compileButton.disabled = true;
    setStatus("busy", execute ? "Compilando y ejecutando en SPIM..." : "Compilando...");

    return fetch(execute ? "/api/run" : "/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: editor.value, strict: strictToggle.checked,
        generate_mips: phase.value === "mips", allocation: allocation.value
      })
    })
      .then(function (response) { return response.json().then(function (b) { return { ok: response.ok, body: b }; }); })
      .then(function (payload) {
        if (requestId !== latestRequest) { return; }
        if (!payload.ok) {
          setStatus("fail", payload.body.error || "Error del servidor");
          return;
        }
        const data = payload.body;
        renderDiagnostics(data.diagnostics || []);
        renderAst(data.ast);
        renderSymbols(data.symbolRows);
        artifacts = { tac: data.success ? data.tac : null, mips: data.success ? data.mips : null };
        tacOutput.textContent = artifacts.tac || "No se generó TAC. Revise la fase seleccionada y los diagnósticos.";
        mipsOutput.textContent = artifacts.mips || "No se generó MIPS. Revise la fase seleccionada y los diagnósticos.";
        downloadTac.disabled = !artifacts.tac;
        downloadMips.disabled = !artifacts.mips;
        if (data.execution) {
          executionOutput.textContent = data.execution.success
            ? (data.execution.output || "El programa terminó sin imprimir salida.")
            : data.execution.error;
          showTab("execution");
        } else if (execute) {
          executionOutput.textContent = "No se ejecutó el programa porque la compilación falló.";
        }
        if (data.success) {
          setStatus(
            data.execution && !data.execution.success ? "fail" : "ok",
            (data.execution ? (data.execution.success ? "Ejecución en SPIM exitosa" : "Error de ejecución en SPIM") : "Compilacion exitosa") +
              (data.warningCount ? " · " + data.warningCount + " advertencia(s)" : "")
          );
        } else {
          showTab("diagnostics");
          setStatus(
            "fail",
            "Compilacion fallida · " +
              data.errorCount + " error(es), " + data.warningCount + " advertencia(s)"
          );
        }
      })
      .catch(function (error) {
        if (requestId === latestRequest) {
          setStatus("fail", "No se pudo contactar al servidor: " + error.message);
        }
      })
      .finally(function () { busy = false; updateControls(); });
  }

  compileButton.addEventListener("click", function () { compile(false); });
  runButton.addEventListener("click", function () { compile(true); });
  phase.addEventListener("change", invalidate);
  allocation.addEventListener("change", invalidate);
  strictToggle.addEventListener("change", invalidate);

  function loadExample() {
    fetch("/api/example?name=" + encodeURIComponent(exampleSelect.value))
      .then(function (r) { return r.json().then(function (data) {
        if (!r.ok) { throw new Error(data.error || "Ejemplo no disponible"); }
        return data;
      }); })
      .then(function (data) {
        editor.value = data.source;
        phase.value = data.phase;
        invalidate();
        renderGutter();
        updateCursor();
        return compile(false);
      })
      .catch(function (error) { setStatus("fail", "No se pudo cargar el ejemplo: " + error.message); });
  }
  loadButton.addEventListener("click", loadExample);

  function download(content, filename) {
    if (!content) { return; }
    const url = URL.createObjectURL(new Blob([content], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }
  downloadTac.addEventListener("click", function () { download(artifacts.tac, "programa.tac"); });
  downloadMips.addEventListener("click", function () { download(artifacts.mips, "programa.asm"); });

  document.getElementById("expand-all").addEventListener("click", function () {
    astTree.querySelectorAll(".ast-children").forEach(function (box) { box.classList.remove("collapsed"); });
    astTree.querySelectorAll(".ast-toggle").forEach(function (t) { if (t.textContent === "▸") t.textContent = "▾"; });
  });

  document.getElementById("collapse-all").addEventListener("click", function () {
    astTree.querySelectorAll(".ast-children").forEach(function (box) { box.classList.add("collapsed"); });
    astTree.querySelectorAll(".ast-toggle").forEach(function (t) { if (t.textContent === "▾") t.textContent = "▸"; });
  });

  // --- arranque ----------------------------------------------------------

  editor.value = STARTER;
  renderGutter();
  updateCursor();
  showTab("diagnostics");
  updateControls();
  loadExample();
})();
