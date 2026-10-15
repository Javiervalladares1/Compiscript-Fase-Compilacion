/* IDE de Compiscript: editor, panel de diagnosticos, AST y tabla de simbolos.
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

  const STARTER = [
    "// Bienvenido al IDE de Compiscript",
    "const PI: float = 3.1416;",
    "",
    "function area(radio: float): float {",
    "  return PI * radio * radio;",
    "}",
    "",
    "let radios: float[] = [1.0, 2.5, 3.0];",
    "foreach (r in radios) {",
    '  print("Area: " + area(r));',
    "}",
    "",
    "class Animal {",
    "  let nombre: string;",
    "  function constructor(nombre: string) { this.nombre = nombre; }",
    "  function hablar(): string { return this.nombre + \" hace ruido.\"; }",
    "}",
    "",
    "class Perro : Animal {",
    "  function hablar(): string { return this.nombre + \" ladra.\"; }",
    "}",
    "",
    "let perro: Perro = new Perro(\"Toby\");",
    "print(perro.hablar());",
    ""
  ].join("\n");

  let errorLines = new Set();

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
    }
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      compile();
    }
  });

  // --- pestanas ----------------------------------------------------------

  document.querySelectorAll(".tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".tab").forEach(function (t) { t.classList.remove("active"); });
      document.querySelectorAll(".tab-panel").forEach(function (p) { p.classList.remove("active"); });
      tab.classList.add("active");
      document.getElementById("panel-" + tab.dataset.tab).classList.add("active");
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

  function compile() {
    compileButton.disabled = true;
    setStatus("busy", "Compilando...");

    fetch("/api/compile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source: editor.value, strict: strictToggle.checked })
    })
      .then(function (response) { return response.json().then(function (b) { return { ok: response.ok, body: b }; }); })
      .then(function (payload) {
        if (!payload.ok) {
          setStatus("fail", payload.body.error || "Error del servidor");
          return;
        }
        const data = payload.body;
        renderDiagnostics(data.diagnostics || []);
        renderAst(data.ast);
        renderSymbols(data.symbolRows);
        if (data.success) {
          setStatus(
            "ok",
            "Compilacion exitosa" +
              (data.warningCount ? " · " + data.warningCount + " advertencia(s)" : "")
          );
        } else {
          setStatus(
            "fail",
            "Compilacion fallida · " +
              data.errorCount + " error(es), " + data.warningCount + " advertencia(s)"
          );
        }
      })
      .catch(function (error) { setStatus("fail", "No se pudo contactar al servidor: " + error.message); })
      .finally(function () { compileButton.disabled = false; });
  }

  compileButton.addEventListener("click", compile);

  document.getElementById("load-example").addEventListener("click", function () {
    fetch("/api/example")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        editor.value = data.source;
        renderGutter();
        compile();
      })
      .catch(function () { setStatus("fail", "No se pudo cargar el ejemplo."); });
  });

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
  compile();
})();
