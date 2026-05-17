/* dashboard_hub_search.js
 * ─────────────────────────────────────────────────────────
 * Generic live-search helper for any page that has:
 *   - A search/filter form
 *   - A table tbody to swap
 *   - (Optional) hub-stats values to refresh
 *
 * Strategy: fetches the FULL page URL with new query string, parses the
 * response HTML, then extracts the tbody (and other named regions) and
 * swaps them into the current DOM. No backend changes required.
 *
 * Usage:
 *   HubSearch.attach({
 *     formId: 'rc-filter-form',         // form element with the inputs
 *     tbodyId: 'rc-tbody',              // tbody to swap
 *     tableId: 'rc-table',              // (optional) for pagination reattach
 *     statusId: 'rc-search-status',     // (optional) spinner element
 *     countId: 'rc-results-count',      // (optional) "N results" number
 *     clearBtnId: 'rc-clear-btn',       // (optional) clear button
 *     debounce: 280,                    // (optional) input debounce ms
 *     watchInputs: ['rc-q', 'rc-status', ...],  // (optional) extra elements; auto-detected
 *     // selectors to swap (auto-detected if omitted):
 *     extraSwap: [{src:'.hub-stats',dst:'.hub-stats'}],
 *   });
 */
(function(){
  "use strict";

  function $(id){ return document.getElementById(id); }

  function setStatus(el, state, title){
    if(!el) return;
    el.innerHTML = '';
    el.classList.remove('is-on');
    el.removeAttribute('title');
    if(state === 'searching'){ el.classList.add('is-on'); el.title = title || 'جارٍ البحث…'; }
    else if(state === 'done'){
      el.innerHTML = '<i class="fa-solid fa-circle-check" style="color:#166534"></i>';
      el.title = title || 'تم';
      setTimeout(function(){ el.innerHTML = ''; el.removeAttribute('title'); }, 800);
    }
    else if(state === 'error'){
      el.innerHTML = '<i class="fa-solid fa-triangle-exclamation" style="color:#b91c1c"></i>';
      el.title = title || 'فشل';
    }
  }

  function reinitPagination(table){
    if(!table) return;
    if(window.DashboardTable && typeof window.DashboardTable.reattach === 'function'){
      window.DashboardTable.reattach(table);
    }
  }

  function attach(opts){
    var form    = $(opts.formId);
    var tbody   = $(opts.tbodyId);
    if(!form || !tbody) return;

    var table   = opts.tableId ? $(opts.tableId) : null;
    var status  = opts.statusId ? $(opts.statusId) : null;
    var countEl = opts.countId ? $(opts.countId) : null;
    var clearBtn = opts.clearBtnId ? $(opts.clearBtnId) : null;
    var debounceMs = opts.debounce || 280;

    // collect inputs: all form fields that should trigger search
    var inputs = [];
    if(opts.watchInputs && opts.watchInputs.length){
      opts.watchInputs.forEach(function(id){
        var el = $(id); if(el) inputs.push(el);
      });
    } else {
      // auto-detect: every input/select within the form (except hidden)
      Array.prototype.forEach.call(form.elements, function(el){
        if(!el.name || el.type === 'hidden' || el.type === 'submit' || el.type === 'button') return;
        inputs.push(el);
      });
    }

    function buildParams(){
      var p = new URLSearchParams();
      Array.prototype.forEach.call(form.elements, function(el){
        if(!el.name) return;
        if(el.type === 'submit' || el.type === 'button') return;
        var v = el.value;
        if(v == null || v === '') return;
        p.set(el.name, v);
      });
      return p;
    }

    function updateUrl(params){
      var qs = params.toString();
      try { history.replaceState(null, '', window.location.pathname + (qs ? ('?'+qs) : '')); } catch(e) {}
    }

    function doFetch(showStatus){
      var params = buildParams();
      updateUrl(params);
      if(showStatus) setStatus(status, 'searching');
      var url = window.location.pathname + (params.toString() ? ('?' + params.toString()) : '');
      fetch(url, {
        credentials:'same-origin',
        headers:{'Accept':'text/html','X-Requested-With':'XMLHttpRequest'}
      })
      .then(function(r){ return r.text(); })
      .then(function(html){
        var parser = new DOMParser();
        var doc = parser.parseFromString(html, 'text/html');

        // 1) Swap tbody
        var newTbody = doc.getElementById(opts.tbodyId);
        if(newTbody){
          tbody.innerHTML = newTbody.innerHTML;
        }

        // 2) Update count if specified
        if(countEl){
          var newCount = doc.getElementById(opts.countId);
          if(newCount){ countEl.textContent = newCount.textContent; }
          else {
            // fallback: count tr (excluding no-paginate)
            var rows = tbody.querySelectorAll('tr:not(.no-paginate)');
            countEl.textContent = rows.length;
          }
        }

        // 3) Swap hub-stats values if present in both DOMs
        var newHubStats = doc.querySelectorAll('.hub-stat .val');
        var curHubStats = document.querySelectorAll('.hub-stat .val');
        if(newHubStats.length && newHubStats.length === curHubStats.length){
          for(var i=0; i<newHubStats.length; i++){
            curHubStats[i].innerHTML = newHubStats[i].innerHTML;
          }
        }

        // 4) Swap qa-count pills in hub-pills if present
        var newPills = doc.querySelectorAll('.hub-pills .qa-count');
        var curPills = document.querySelectorAll('.hub-pills .qa-count');
        if(newPills.length && newPills.length === curPills.length){
          for(var j=0; j<newPills.length; j++){
            curPills[j].textContent = newPills[j].textContent;
          }
        }

        // 5) Custom extraSwap (caller-specified)
        if(opts.extraSwap && opts.extraSwap.length){
          opts.extraSwap.forEach(function(spec){
            var newEl = doc.querySelector(spec.src);
            var curEl = document.querySelector(spec.dst);
            if(newEl && curEl) curEl.innerHTML = newEl.innerHTML;
          });
        }

        // 6) Reattach pagination
        reinitPagination(table);
        setStatus(status, 'done');
        if(typeof opts.afterRender === 'function'){
          try { opts.afterRender(); } catch(e) {}
        }
      })
      .catch(function(){ setStatus(status, 'error'); });
    }

    // wire events
    form.addEventListener('submit', function(e){ e.preventDefault(); doFetch(true); });
    var timer = null;
    inputs.forEach(function(el){
      var ev = (el.tagName === 'SELECT' || el.type === 'date' || el.type === 'checkbox') ? 'change' : 'input';
      el.addEventListener(ev, function(){
        if(ev === 'change'){ doFetch(true); return; }
        clearTimeout(timer);
        setStatus(status, 'searching');
        timer = setTimeout(function(){ doFetch(true); }, debounceMs);
      });
    });
    if(clearBtn){
      clearBtn.addEventListener('click', function(){
        Array.prototype.forEach.call(form.elements, function(el){
          if(!el.name || el.type === 'hidden') return;
          if(el.tagName === 'SELECT'){ el.selectedIndex = 0; }
          else if(el.type !== 'submit' && el.type !== 'button'){ el.value = ''; }
        });
        doFetch(true);
        var firstInput = form.querySelector('input[type="search"], input[type="text"]');
        if(firstInput) firstInput.focus();
      });
    }
  }

  window.HubSearch = { attach: attach };
})();
