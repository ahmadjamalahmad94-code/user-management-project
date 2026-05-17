# Auto-split from app/legacy.py lines 5904-6206. Loaded by app.legacy.
# ===== Runtime UI/UX patch =====
# CSS tweaks
BASE_TEMPLATE = BASE_TEMPLATE.replace(
    ".notes-box{min-height:90px}\n.ajax-saving{opacity:.65;pointer-events:none}",
    ".notes-box{min-height:90px}\n.note-preview{display:inline-flex;align-items:center;gap:6px;max-width:260px}\n.note-text{display:inline-block;max-width:190px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}\n.type-tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}\n.type-tab{padding:10px 14px;border-radius:999px;border:1px solid var(--line);background:#fff;color:var(--text);cursor:pointer;font-weight:700}\n.type-tab.active{background:var(--primary);color:#fff;border-color:var(--primary)}\n.ajax-saving{opacity:.65;pointer-events:none}"
)
# JS tweaks
BASE_TEMPLATE = BASE_TEMPLATE.replace(
"""function initBeneficiaryForms(){
  document.querySelectorAll('[data-beneficiary-scope]').forEach(function(scope){
    var input = scope.querySelector('select[name=\"user_type\"], input[name=\"user_type\"]');
    if(input){toggleBeneficiarySections(input, scope.id);}
  });
}
""",
"""function syncTypeTabs(scopeId, value){
  var container = document.getElementById(scopeId);
  if(!container) return;
  container.querySelectorAll('.type-tab').forEach(function(btn){ btn.classList.toggle('active', btn.dataset.value === value); });
}
function setBeneficiaryType(scopeId, value){
  var container = document.getElementById(scopeId);
  if(!container) return false;
  var input = container.querySelector('select[name=\"user_type\"], input[name=\"user_type\"]');
  if(input){ input.value = value; toggleBeneficiarySections(input, scopeId); }
  syncTypeTabs(scopeId, value);
  return false;
}
function initBeneficiaryForms(){
  document.querySelectorAll('[data-beneficiary-scope]').forEach(function(scope){
    var input = scope.querySelector('select[name=\"user_type\"], input[name=\"user_type\"]');
    if(input){toggleBeneficiarySections(input, scope.id); syncTypeTabs(scope.id, input.value || 'tawjihi');}
  });
}
"""
)
BASE_TEMPLATE = BASE_TEMPLATE.replace(
"""async function submitBeneficiaryEdit(form, rowId, modalId){
  form.classList.add('ajax-saving');
  try{
    const data = await ajaxPost(form.action, new FormData(form));
    replaceRowAndModal(data, rowId, modalId);
    window.location.hash = '#!';
  }catch(err){
    showLiveFlash(err.message || 'تعذر حفظ التعديل', 'error');
  }finally{
    form.classList.remove('ajax-saving');
  }
  return false;
}
""",
"""async function submitBeneficiaryEdit(form, rowId, modalId){
  form.classList.add('ajax-saving');
  try{
    const data = await ajaxPost(form.action, new FormData(form));
    replaceRowAndModal(data, rowId, modalId);
    window.location.hash = '#!';
  }catch(err){
    showLiveFlash(err.message || 'تعذر حفظ التعديل', 'error');
  }finally{
    form.classList.remove('ajax-saving');
  }
  return false;
}
function prependRowToTable(rowHtml){
  const tbody = document.querySelector('.table-wrap table tbody');
  if(!tbody || !rowHtml) return;
  const empty = tbody.querySelector('.empty-state');
  if(empty){ empty.parentElement.remove(); }
  tbody.insertAdjacentHTML('afterbegin', rowHtml);
}
function insertModalHtml(modalHtml){ if(modalHtml){ document.body.insertAdjacentHTML('beforeend', modalHtml); } }
function submitBeneficiaryAdd(form){ return guardSingleSubmit(form); }
async function resetWeeklyUsageAjax(url){
  try{
    const data = await ajaxPost(url);
    document.querySelectorAll('tr[id^="beneficiary-row-"]').forEach(function(row){
      if(row.dataset.limited === '1'){
        row.classList.remove('row-complete');
        const cell = row.querySelector('.usage-cell');
        if(cell){ cell.textContent = '0 / 3'; }
      }
    });
    if(data.message){ showLiveFlash(data.message, data.category || 'success'); }
  }catch(err){ showLiveFlash(err.message || 'تعذر تجديد البطاقات', 'error'); }
  return false;
}
"""
)

BASE_TEMPLATE = BASE_TEMPLATE.replace(
    "<div class=\"brand-text\">Hobe Hub<small>Professional+ Edition</small></div>",
    "<div class=\"brand-text\">Hobe Hub<small>منصة إدارة الوصول إلى الإنترنت</small></div>",
)
