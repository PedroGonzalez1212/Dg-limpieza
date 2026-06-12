function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

let stockActualGlobal = 0;

function abrirModalAjuste(id, nombre, stockActual) {
  stockActualGlobal = stockActual;

  document.getElementById('ajuste-nombre').textContent       = nombre;
  document.getElementById('ajuste-stock-actual').textContent = stockActual;
  document.getElementById('form-ajuste').action = `/admin/stock/${id}/ajustar`;

  document.getElementById('ajuste-cantidad').value = '';
  document.getElementById('ajuste-motivo').value   = '';
  document.getElementById('ajuste-preview').style.display = 'none';
  document.querySelector('input[name="tipo"][value="entrada"]').checked = true;
  actualizarHintCantidad();

  document.getElementById('modal-ajuste').style.display = 'flex';
}

function actualizarHintCantidad() {
  const tipo = document.querySelector('input[name="tipo"]:checked')?.value;
  const hint = document.getElementById('label-cantidad-hint');
  hint.textContent = tipo === 'entrada'
    ? 'unidades a sumar'
    : 'stock final que querés tener';
}

function actualizarPreview() {
  const tipo     = document.querySelector('input[name="tipo"]:checked')?.value;
  const cantidad = parseInt(document.getElementById('ajuste-cantidad').value) || 0;
  const preview  = document.getElementById('ajuste-preview');
  const texto    = document.getElementById('ajuste-preview-texto');

  if (!cantidad || cantidad <= 0) { preview.style.display = 'none'; return; }

  let mensaje;
  if (tipo === 'entrada') {
    const resultado = stockActualGlobal + cantidad;
    mensaje = `${stockActualGlobal} + ${cantidad} = ${resultado} unidades`;
  } else {
    const diff  = cantidad - stockActualGlobal;
    const signo = diff >= 0 ? '+' : '';
    mensaje = `Stock actual ${stockActualGlobal} → ${cantidad} (${signo}${diff})`;
  }

  texto.textContent     = mensaje;
  preview.style.display = 'block';
}

async function verHistorial(id, nombre) {
  document.getElementById('historial-nombre').textContent    = nombre;
  document.getElementById('historial-loading').style.display = 'block';
  document.getElementById('historial-content').style.display = 'none';
  document.getElementById('historial-empty').style.display   = 'none';
  document.getElementById('modal-historial').style.display   = 'flex';

  try {
    const res  = await fetch(`/admin/stock/${id}/historial`);
    const data = await res.json();

    document.getElementById('historial-stock').textContent = data.stock_actual;

    const tbody = document.getElementById('historial-tbody');
    tbody.innerHTML = '';

    if (!data.movimientos.length) {
      document.getElementById('historial-loading').style.display = 'none';
      document.getElementById('historial-empty').style.display   = 'block';
      return;
    }

    data.movimientos.forEach((m, idx) => {
      const signo = m.tipo === 'salida' ? '-' : '+';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="text-center text-muted" style="font-size:0.8rem">${idx + 1}</td>
        <td>${escHtml(m.fecha)}</td>
        <td><span class="tipo-${escHtml(m.tipo)}">${escHtml(m.tipo)}</span></td>
        <td class="text-center"><strong>${signo}${m.cantidad}</strong></td>
        <td>${escHtml(m.motivo)}</td>
        <td>${escHtml(m.usuario)}</td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('historial-loading').style.display = 'none';
    document.getElementById('historial-content').style.display = 'block';

  } catch (err) {
    document.getElementById('historial-loading').textContent = 'Error al cargar el historial.';
  }
}

async function verHistorialGlobal() {
  document.getElementById('hg-loading').style.display = 'block';
  document.getElementById('hg-content').style.display = 'none';
  document.getElementById('hg-empty').style.display   = 'none';
  document.getElementById('modal-historial-global').style.display = 'flex';

  try {
    const res  = await fetch('/admin/stock/historial-global');
    const data = await res.json();
    const tbody = document.getElementById('hg-tbody');
    tbody.innerHTML = '';

    if (!data.movimientos.length) {
      document.getElementById('hg-loading').style.display = 'none';
      document.getElementById('hg-empty').style.display   = 'block';
      return;
    }

    document.getElementById('hg-count').textContent =
      `${data.movimientos.length} movimiento${data.movimientos.length !== 1 ? 's' : ''} registrado${data.movimientos.length !== 1 ? 's' : ''}`;

    data.movimientos.forEach((m, idx) => {
      const signo = m.tipo === 'salida' ? '-' : '+';
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td class="text-center text-muted" style="font-size:0.8rem">${idx + 1}</td>
        <td style="white-space:nowrap">${escHtml(m.fecha)}</td>
        <td><strong>${escHtml(m.producto)}</strong></td>
        <td><span class="tipo-${escHtml(m.tipo)}">${escHtml(m.tipo)}</span></td>
        <td class="text-center"><strong>${signo}${m.cantidad}</strong></td>
        <td>${escHtml(m.motivo)}</td>
        <td>${escHtml(m.usuario)}</td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById('hg-loading').style.display = 'none';
    document.getElementById('hg-content').style.display = 'block';

  } catch(err) {
    document.getElementById('hg-loading').textContent = 'Error al cargar el historial.';
  }
}

function cerrarModal(id) {
  document.getElementById(id).style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('ajuste-cantidad').addEventListener('input', actualizarPreview);

  document.querySelectorAll('input[name="tipo"]').forEach(radio => {
    radio.addEventListener('change', () => {
      actualizarHintCantidad();
      actualizarPreview();
    });
  });

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-action]');
    if (btn) {
      const action = btn.dataset.action;
      if (action === 'ajustar') {
        abrirModalAjuste(btn.dataset.id, btn.dataset.nombre, parseInt(btn.dataset.stock));
      } else if (action === 'historial') {
        verHistorial(btn.dataset.id, btn.dataset.nombre);
      } else if (action === 'historial-global') {
        verHistorialGlobal();
      }
    }

    const closeBtn = e.target.closest('[data-modal-close]');
    if (closeBtn) {
      cerrarModal(closeBtn.dataset.modalClose);
    }

    const overlay = e.target.closest('.modal-overlay');
    if (overlay && e.target === overlay) {
      cerrarModal(overlay.id);
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay').forEach(m => {
        m.style.display = 'none';
      });
    }
  });
});
