// CSRF interceptor — parchea window.fetch para inyectar X-CSRFToken en POST
(function () {
  var _fetch = window.fetch;
  window.fetch = function (url, opts) {
    opts = opts || {};
    if (opts.method && opts.method.toUpperCase() === 'POST') {
      var meta = document.querySelector('meta[name="csrf-token"]');
      if (meta) {
        var token = meta.getAttribute('content');
        if (opts.headers instanceof Headers) {
          opts.headers.set('X-CSRFToken', token);
        } else {
          opts.headers = Object.assign({ 'X-CSRFToken': token }, opts.headers || {});
        }
      }
    }
    return _fetch.apply(this, arguments);
  };
})();

// Confirmación declarativa: <form data-confirm="¿Seguro?"> sin onclick
document.addEventListener('submit', function (e) {
  var msg = e.target.dataset.confirm;
  if (msg && !confirm(msg)) e.preventDefault();
});

document.addEventListener('DOMContentLoaded', function () {
  // Inicializar iconos Lucide
  if (window.lucide) lucide.createIcons();

  // Menú hamburguesa
  var navToggle = document.getElementById('navToggle');
  var navLinks  = document.getElementById('navLinks');
  if (navToggle && navLinks) {
    navToggle.addEventListener('click', function () {
      var isOpen = navLinks.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', isOpen);
    });
  }

  // Badge del carrito
  fetch('/carrito/total')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var badge = document.getElementById('cartBadge');
      if (badge && data.total_items > 0) {
        badge.textContent = data.total_items > 99 ? '99+' : data.total_items;
        badge.style.display = 'flex';
      }
    })
    .catch(function () {});
});
