document.addEventListener('DOMContentLoaded', function () {
  var canvas = document.getElementById('graficoMetodos');
  if (!canvas) return;

  var labels = JSON.parse(canvas.dataset.labels);
  var values = JSON.parse(canvas.dataset.values);

  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Total ($)',
        data: values,
        backgroundColor: ['#39EBE1', '#0C0C62', '#27ae60', '#f39c12', '#8e44ad'],
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true } }
    }
  });
});
