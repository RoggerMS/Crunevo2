function initDropdowns(scope = document) {
  scope.querySelectorAll('[data-bs-toggle="dropdown"]').forEach((el) => {
    if (!bootstrap.Dropdown.getInstance(el)) {
      bootstrap.Dropdown.getOrCreateInstance(el);
    }

    if (el.title && !el.dataset.tooltipInitialized) {
      bootstrap.Tooltip.getOrCreateInstance(el);
      el.dataset.tooltipInitialized = 'true';
    }

    if (!el.dataset.dropdownTooltipBound) {
      el.addEventListener('show.bs.dropdown', () => {
        const t = bootstrap.Tooltip.getInstance(el);
        if (t) t.hide();
      });
      el.dataset.dropdownTooltipBound = 'true';
    }
  });
}

function initDataTables() {
  if (typeof simpleDatatables === 'undefined') return;
  document.querySelectorAll('[data-datatable]').forEach((table) => {
    const dt = new simpleDatatables.DataTable(table);
    const refresh = () => initDropdowns(table.parentElement);
    ['datatable.init', 'datatable.page', 'datatable.update', 'datatable.sort', 'datatable.search'].forEach((e) => dt.on(e, refresh));
    refresh();
  });
}
