const _stepperMap = new Map();

function mostrarStepper(productoId, stock, wrap) {
  _stepperMap.set(productoId, wrap.innerHTML);
  wrap.innerHTML = `
    <div style="flex:1;display:flex;align-items:stretch;border:1.5px solid var(--line);border-radius:10px;overflow:hidden;background:#f0f4f8;">
      <button type="button" data-stepper="minus"
        style="flex:1;background:transparent;border:none;font-size:17px;font-weight:700;color:var(--navy);cursor:pointer;padding:0 4px;">−</button>
      <span style="flex:0 0 36px;display:flex;align-items:center;justify-content:center;font-family:var(--font-display);font-size:15px;font-weight:700;color:var(--navy);border-left:1px solid var(--line);border-right:1px solid var(--line);" data-max="${stock}">1</span>
      <button type="button" data-stepper="plus"
        style="flex:1;background:transparent;border:none;font-size:17px;font-weight:700;color:var(--navy);cursor:pointer;padding:0 4px;">+</button>
    </div>
    <button class="producto-card__btn" type="button" data-stepper="confirm" data-producto-id="${productoId}"
      style="flex:0 0 auto;width:42px;padding:12px;margin-top:0;">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
    </button>`;
}

function agregarComboAlCarrito(comboId, nombre, precio) {
  fetch('/carrito/agregar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      producto_id: 'combo_' + comboId,
      nombre: nombre,
      precio: precio,
      cantidad: 1,
      es_combo: true
    })
  })
  .then(r => r.json())
  .then(data => {
    if (data.ok) {
      alert('✅ ' + nombre + ' agregado al carrito');
    }
  });
}

document.addEventListener('click', function(e) {
  const btnAgregar = e.target.closest('[data-agregar-producto]');
  if (btnAgregar) {
    mostrarStepper(
      parseInt(btnAgregar.dataset.productoId),
      parseInt(btnAgregar.dataset.stock),
      btnAgregar.parentElement
    );
    return;
  }

  const stepperBtn = e.target.closest('[data-stepper]');
  if (stepperBtn) {
    const action = stepperBtn.dataset.stepper;

    if (action === 'minus' || action === 'plus') {
      const delta = action === 'minus' ? -1 : 1;
      const span = stepperBtn.parentElement.querySelector('span');
      const max = parseInt(span.dataset.max) || 999;
      span.textContent = Math.max(1, Math.min(max, parseInt(span.textContent) + delta));
    } else if (action === 'confirm') {
      const productoId = parseInt(stepperBtn.dataset.productoId);
      const wrap = stepperBtn.parentElement;
      const cantidad = parseInt(wrap.querySelector('span').textContent);
      wrap.querySelectorAll('button').forEach(b => b.disabled = true);

      fetch('/carrito/agregar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ producto_id: productoId, cantidad, es_combo: false })
      })
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          const badge = document.getElementById('cartBadge');
          if (badge) {
            badge.textContent = data.total_items > 99 ? '99+' : data.total_items;
            badge.style.display = 'flex';
          }
        }
        wrap.innerHTML = _stepperMap.get(productoId);
        _stepperMap.delete(productoId);
      })
      .catch(() => {
        wrap.innerHTML = _stepperMap.get(productoId);
        _stepperMap.delete(productoId);
      });
    }
    return;
  }

  const btnCombo = e.target.closest('[data-combo-id]');
  if (btnCombo) {
    agregarComboAlCarrito(
      btnCombo.dataset.comboId,
      btnCombo.dataset.comboNombre,
      parseFloat(btnCombo.dataset.comboPrecio)
    );
  }
});
