function initAdminCharts() {
  document.querySelectorAll('[data-chart]').forEach((el) => {
    const cfg = JSON.parse(el.dataset.chart || '{}');
    if (!cfg.labels) return;
    new Chart(el, {
      type: 'line',
      data: {
        labels: cfg.labels,
        datasets: [
          {
            label: cfg.label || '',
            data: cfg.values,
            tension: 0.4,
            fill: true,
            backgroundColor: 'rgba(32,107,196,0.2)',
            borderColor: '#206bc4',
          },
        ],
      },
      options: { scales: { y: { beginAtZero: true } }, plugins: { legend: { display: false } } },
    });
  });
}
