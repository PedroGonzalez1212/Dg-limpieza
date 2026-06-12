async function cambiarCantidad(productoId, delta) {
  const spanCantidad = document.getElementById(`cantidad-${productoId}`);
  const cantidadActual = parseInt(spanCantidad.textContent);
  const nuevaCantidad = cantidadActual + delta;

  const res = await fetch('/carrito/actualizar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ producto_id: productoId, cantidad: nuevaCantidad })
  });

  const data = await res.json();
  if (!data.ok) return;

  if (nuevaCantidad <= 0) {
    document.querySelector(`.carrito-item[data-id="${productoId}"]`).remove();
  } else {
    spanCantidad.textContent = nuevaCantidad;
    document.getElementById(`subtotal-${productoId}`).textContent =
      `$${data.subtotal.toFixed(2)}`;
  }

  actualizarResumen(data.total, data.total_items);
  verificarCarritoVacio();
}

async function eliminarItem(productoId) {
  const res = await fetch('/carrito/eliminar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ producto_id: productoId })
  });

  const data = await res.json();
  if (!data.ok) return;

  document.querySelector(`.carrito-item[data-id="${productoId}"]`).remove();
  actualizarResumen(data.total, data.total_items);
  verificarCarritoVacio();
}

async function vaciarCarrito() {
  if (!confirm('¿Vaciar todo el carrito?')) return;
  await fetch('/carrito/vaciar', { method: 'POST' });
  window.location.reload();
}

function actualizarResumen(total, totalItems) {
  document.getElementById('total-precio').textContent = `$${total.toFixed(2)}`;
  document.getElementById('total-items').textContent = totalItems;

  const badge = document.getElementById('carrito-badge');
  if (badge) badge.textContent = totalItems;
}

function verificarCarritoVacio() {
  const items = document.querySelectorAll('.carrito-item');
  if (items.length === 0) window.location.reload();
}

function confirmarPedido() {
  const items = document.querySelectorAll('.carrito-item');
  if (items.length === 0) return;

  document.getElementById('modal-nombre').value = '';
  document.getElementById('modal-telefono').value = '';
  document.getElementById('modal-horario').value = '';
  document.getElementById('modal-error').style.display = 'none';
  document.getElementById('modal-pedido-overlay').style.display = 'flex';
  document.getElementById('modal-nombre').focus();
}

function cerrarModal(event) {
  if (event && event.target !== document.getElementById('modal-pedido-overlay')) return;
  document.getElementById('modal-pedido-overlay').style.display = 'none';
}

async function enviarPedido() {
  const nombre   = document.getElementById('modal-nombre').value.trim();
  const telefono = document.getElementById('modal-telefono').value.trim();
  const horario  = document.getElementById('modal-horario').value.trim();
  const errorEl  = document.getElementById('modal-error');

  errorEl.textContent = 'Por favor completá todos los campos.';
  if (!nombre || !telefono || !horario) {
    errorEl.style.display = 'block';
    return;
  }
  errorEl.style.display = 'none';

  const btnEnviar = document.querySelector('.btn-modal-enviar');
  btnEnviar.disabled = true;
  btnEnviar.textContent = 'Enviando…';

  try {
    const res = await fetch('/carrito/confirmar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, telefono, horario })
    });

    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error('Respuesta inesperada del servidor.');
    }

    if (!res.ok || !data.ok) {
      throw new Error(data.error || 'Error al registrar el pedido.');
    }

    const items = document.querySelectorAll('.carrito-item');
    let lineasProductos = [];
    items.forEach(item => {
      const nomProd  = item.querySelector('.item-nombre').textContent.trim();
      const cantidad = item.querySelector('.item-cantidad').textContent.trim();
      const subtotal = item.querySelector('[id^="subtotal-"]').textContent.trim();
      lineasProductos.push(`- ${nomProd} x${cantidad} = ${subtotal}`);
    });

    const total = document.getElementById('total-precio').textContent.trim();

    const mensaje = [
      '*Nuevo pedido — DG Limpieza*',
      '',
      '*Datos del cliente*',
      `- Nombre: ${nombre}`,
      `- Teléfono: ${telefono}`,
      `- Horario para retirar: ${horario}`,
      '',
      '*Productos*',
      ...lineasProductos,
      '',
      `*Total: ${total}*`,
    ].join('\n');

    await fetch('/carrito/vaciar', { method: 'POST' });

    const numeroWA = '5493512515999';
    const textoEncoded = encodeURIComponent(mensaje);
    window.open(`https://wa.me/${numeroWA}?text=${textoEncoded}`, '_blank');

    window.location.href = '/catalogo';

  } catch (err) {
    errorEl.textContent = err.message || 'Ocurrió un error. Intentá de nuevo.';
    errorEl.style.display = 'block';
    btnEnviar.disabled = false;
    btnEnviar.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/><path d="M12 0C5.373 0 0 5.373 0 12c0 2.121.555 4.11 1.526 5.835L0 24l6.335-1.652A11.954 11.954 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.891 0-3-.4-4.3-1.1l-.3-.2-3.1.8.8-3-.2-.3C4.3 14.9 4 13.5 4 12c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8z"/></svg> Enviar pedido`;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  document.addEventListener('click', function(e) {
    const btnMinus = e.target.closest('[data-action="minus"]');
    if (btnMinus) { cambiarCantidad(btnMinus.dataset.productoId, -1); return; }

    const btnPlus = e.target.closest('[data-action="plus"]');
    if (btnPlus) { cambiarCantidad(btnPlus.dataset.productoId, 1); return; }

    const btnEliminar = e.target.closest('[data-action="eliminar"]');
    if (btnEliminar) { eliminarItem(btnEliminar.dataset.productoId); return; }
  });

  const btnConfirmar = document.getElementById('btn-confirmar');
  if (btnConfirmar) btnConfirmar.addEventListener('click', confirmarPedido);

  const btnVaciar = document.querySelector('.btn-vaciar');
  if (btnVaciar) btnVaciar.addEventListener('click', vaciarCarrito);

  const overlay = document.getElementById('modal-pedido-overlay');
  if (overlay) overlay.addEventListener('click', cerrarModal);

  const btnCancelar = document.querySelector('.btn-modal-cancelar');
  if (btnCancelar) btnCancelar.addEventListener('click', function() { cerrarModal(); });

  const btnEnviar = document.querySelector('.btn-modal-enviar');
  if (btnEnviar) btnEnviar.addEventListener('click', enviarPedido);
});
