/*
 * dashboard_table.js
 * ─────────────────────────────────────────────────────────
 * Client-side pagination + page-size selector for any <table>
 * marked with `data-paginated="1"`.
 *
 * Optional attributes on <table>:
 *   data-paginated="1"        ← required to activate
 *   data-page-size="20"       ← default page size (default: 20)
 *   data-page-sizes="10,20,50,100"  ← options for the size selector
 *
 * The script wraps the table inside the existing <div class="d-table-wrap">
 * and appends a footer controls bar after it.
 *
 * It paginates only rows in the FIRST <tbody>, ignoring rows
 * with class "no-paginate" (e.g. the "empty state" row).
 */
(function () {
  "use strict";

  function makeButton(label, opts) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "dpt-btn";
    btn.innerHTML = label;
    if (opts && opts.icon) btn.classList.add("dpt-btn-icon");
    return btn;
  }

  function buildControls(state) {
    var foot = document.createElement("div");
    foot.className = "dpt-foot";

    // Left: page size selector
    var sizeBox = document.createElement("div");
    sizeBox.className = "dpt-size-box";
    var sizeLabel = document.createElement("span");
    sizeLabel.className = "dpt-size-label";
    sizeLabel.textContent = "صفوف لكل صفحة:";
    var sizeSelect = document.createElement("select");
    sizeSelect.className = "dpt-size-select";
    state.sizes.forEach(function (n) {
      var opt = document.createElement("option");
      opt.value = String(n);
      opt.textContent = String(n);
      if (n === state.pageSize) opt.selected = true;
      sizeSelect.appendChild(opt);
    });
    sizeBox.appendChild(sizeLabel);
    sizeBox.appendChild(sizeSelect);

    // Center: info
    var info = document.createElement("div");
    info.className = "dpt-info";

    // Right: pager buttons
    var pager = document.createElement("div");
    pager.className = "dpt-pager";
    var first = makeButton('<i class="fa-solid fa-angles-right"></i>', { icon: true });
    first.title = "الأولى";
    var prev = makeButton('<i class="fa-solid fa-angle-right"></i>', { icon: true });
    prev.title = "السابقة";
    var pages = document.createElement("div");
    pages.className = "dpt-pages";
    var next = makeButton('<i class="fa-solid fa-angle-left"></i>', { icon: true });
    next.title = "التالية";
    var last = makeButton('<i class="fa-solid fa-angles-left"></i>', { icon: true });
    last.title = "الأخيرة";
    pager.appendChild(first);
    pager.appendChild(prev);
    pager.appendChild(pages);
    pager.appendChild(next);
    pager.appendChild(last);

    foot.appendChild(sizeBox);
    foot.appendChild(info);
    foot.appendChild(pager);

    state.ctrl = {
      foot: foot,
      sizeSelect: sizeSelect,
      info: info,
      pages: pages,
      first: first,
      prev: prev,
      next: next,
      last: last,
    };
    return foot;
  }

  function renderPageButtons(state) {
    var p = state.page;
    var total = state.pageCount;
    state.ctrl.pages.innerHTML = "";

    if (total <= 1) return;

    function btn(num, isActive) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "dpt-page" + (isActive ? " is-active" : "");
      b.textContent = String(num);
      b.addEventListener("click", function () { goTo(state, num); });
      return b;
    }
    function ellipsis() {
      var s = document.createElement("span");
      s.className = "dpt-ellipsis";
      s.textContent = "…";
      return s;
    }

    // smart: show 1, …, p-1, p, p+1, …, total
    var nums = new Set([1, total, p - 1, p, p + 1]);
    var arr = Array.from(nums).filter(function (n) { return n >= 1 && n <= total; }).sort(function (a, b) { return a - b; });
    var prevNum = 0;
    arr.forEach(function (n) {
      if (prevNum && n - prevNum > 1) state.ctrl.pages.appendChild(ellipsis());
      state.ctrl.pages.appendChild(btn(n, n === p));
      prevNum = n;
    });
  }

  function applyPage(state) {
    var size = state.pageSize;
    var p = state.page;
    var startIdx = (p - 1) * size;
    var endIdx = startIdx + size;
    var visibleCount = 0;
    state.rows.forEach(function (tr, idx) {
      if (idx >= startIdx && idx < endIdx) {
        tr.style.display = "";
        visibleCount++;
      } else {
        tr.style.display = "none";
      }
    });

    var totalRows = state.rows.length;
    var from = totalRows === 0 ? 0 : startIdx + 1;
    var to = Math.min(endIdx, totalRows);
    state.ctrl.info.innerHTML =
      "عرض <strong>" + from + "</strong> – <strong>" + to + "</strong> " +
      "من <strong>" + totalRows + "</strong>";

    state.ctrl.first.disabled = p <= 1;
    state.ctrl.prev.disabled = p <= 1;
    state.ctrl.next.disabled = p >= state.pageCount;
    state.ctrl.last.disabled = p >= state.pageCount;

    renderPageButtons(state);

    if (state.persistKey) {
      try {
        localStorage.setItem(state.persistKey + ":size", String(state.pageSize));
      } catch (e) {}
    }
  }

  function goTo(state, p) {
    if (p < 1) p = 1;
    if (p > state.pageCount) p = state.pageCount;
    state.page = p;
    applyPage(state);
  }

  function recomputePageCount(state) {
    state.pageCount = Math.max(1, Math.ceil(state.rows.length / state.pageSize));
    if (state.page > state.pageCount) state.page = state.pageCount;
    if (state.page < 1) state.page = 1;
  }

  function attach(table) {
    if (table.__dptAttached) return;
    table.__dptAttached = true;

    var tbody = table.tBodies[0];
    if (!tbody) return;
    var rows = Array.prototype.slice.call(tbody.rows).filter(function (tr) {
      return !tr.classList.contains("no-paginate");
    });

    // skip if there's only an "empty state" row or fewer rows than the smallest page
    var defaultSize = parseInt(table.getAttribute("data-page-size") || "20", 10);
    var sizesAttr = (table.getAttribute("data-page-sizes") || "10,20,50,100").split(",");
    var sizes = sizesAttr.map(function (x) { return parseInt(x.trim(), 10); }).filter(function (n) { return n > 0; });
    if (sizes.indexOf(defaultSize) === -1) sizes.unshift(defaultSize);

    var persistKey = table.getAttribute("data-persist-key") || "";
    if (persistKey) {
      try {
        var saved = parseInt(localStorage.getItem(persistKey + ":size") || "", 10);
        if (saved && sizes.indexOf(saved) !== -1) defaultSize = saved;
      } catch (e) {}
    }

    var state = {
      table: table,
      rows: rows,
      pageSize: defaultSize,
      page: 1,
      pageCount: 1,
      sizes: sizes,
      persistKey: persistKey,
      ctrl: null,
    };

    recomputePageCount(state);

    var foot = buildControls(state);
    // Insert footer just AFTER the table's wrapping element if it exists,
    // otherwise after the table itself.
    var wrap = table.closest(".d-table-wrap") || table;
    if (wrap.parentNode) {
      wrap.parentNode.insertBefore(foot, wrap.nextSibling);
    }

    // Hide footer when only 1 page AND a single size choice
    if (state.rows.length <= Math.min.apply(null, sizes)) {
      foot.classList.add("dpt-min");
    }

    // Wire events
    state.ctrl.sizeSelect.addEventListener("change", function () {
      var v = parseInt(state.ctrl.sizeSelect.value, 10) || defaultSize;
      state.pageSize = v;
      state.page = 1;
      recomputePageCount(state);
      applyPage(state);
    });
    state.ctrl.first.addEventListener("click", function () { goTo(state, 1); });
    state.ctrl.prev.addEventListener("click", function () { goTo(state, state.page - 1); });
    state.ctrl.next.addEventListener("click", function () { goTo(state, state.page + 1); });
    state.ctrl.last.addEventListener("click", function () { goTo(state, state.pageCount); });

    applyPage(state);
  }

  function init() {
    var tables = document.querySelectorAll("table[data-paginated]");
    tables.forEach(attach);
  }

  // public API لإعادة تهيئة الجدول بعد تعديل tbody (AJAX rerender)
  function reattach(table) {
    if (!table) return;
    var wrap = table.closest(".d-table-wrap") || table;
    // أزل الـ footer القديم
    var sib = wrap.nextSibling;
    while (sib) {
      var next = sib.nextSibling;
      if (sib.nodeType === 1 && sib.classList && sib.classList.contains("dpt-foot")) {
        sib.parentNode.removeChild(sib);
      }
      sib = next;
    }
    table.__dptAttached = false;
    attach(table);
  }
  window.DashboardTable = { attach: attach, reattach: reattach, init: init };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
