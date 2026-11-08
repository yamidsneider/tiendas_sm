'use strict';
/* TIENDAS S.M — página de la app de escritorio (opción B en DECISIONES).
   Estructura y visual tomadas del borrador tiendas_sm_dashboard.html. Esta página NO tiene reglas de negocio ni guarda
   datos: pide todo a Python con window.pywebview.api.<método> (interfaz_web/api.py) y muestra lo que llega, incluidos
   los mensajes del dominio tal como vienen. Todo texto que viene de los datos pasa por esc() antes de ponerse en la página. */

const ICONOS = {
  pos: '<path d="M3 4h2l2.4 11h11L21 7H6.2"/><circle cx="9" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
  ventas: '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
  productos: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
  existencias: '<path d="M4 20V10M10 20V4M16 20v-7M2 20h20"/>',
  clientes: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5M16 4.5a3.5 3.5 0 010 7M18 14.8c1.8.8 3 2.5 3.5 5.2"/>',
  creditos: '<rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M2.5 10h19M6.5 15h4"/>',
};
const SECCIONES = [
  { id: 'pos', titulo: 'Punto de venta', grupo: 'Operación' },
  { id: 'ventas', titulo: 'Ventas', grupo: 'Operación' },
  { id: 'productos', titulo: 'Productos', grupo: 'Inventario' },
  { id: 'existencias', titulo: 'Existencias', grupo: 'Inventario' },
  { id: 'clientes', titulo: 'Clientes', grupo: 'Clientes y crédito' },
  { id: 'creditos', titulo: 'Créditos y abonos', grupo: 'Clientes y crédito' },
];
const MENSAJE_FALLA = 'No se pudo completar la operación. Intente de nuevo; si sigue fallando, cierre y abra la tienda.';
const MAXIMO_SUGERENCIAS = 8;

let seccion = 'pos';
const estado = { busquedas: {}, verPagadas: false, sugerencias: [], sugSel: 0, turno: 0, carrito: null, cobro: null };

/* ------------------------------------------------------------------ utilidades */
const $ = id => document.getElementById(id);
const val = id => ($(id) ? $(id).value : '');
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const svg = nombre => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONOS[nombre]}</svg>`;
const insignia = (clase, texto) => `<span class="insignia ${clase}">${esc(texto)}</span>`;

async function llamar(metodo, ...argumentos) {
  try {
    return await window.pywebview.api[metodo](...argumentos);
  } catch (error) {
    aviso(MENSAJE_FALLA, true);
    throw error;
  }
}

function aviso(texto, mal = false) {
  const caja = document.createElement('div');
  if (mal) caja.className = 'mal';
  caja.textContent = texto;
  $('avisos').appendChild(caja);
  setTimeout(() => caja.remove(), mal ? 6000 : 3500);
}

function tabla(cabeceras, filas, vacio) {
  const th = cabeceras.map(c => (c.startsWith('>') ? `<th class="num">${esc(c.slice(1))}</th>` : `<th>${esc(c)}</th>`)).join('');
  const cuerpo = filas.length ? filas.join('') : `<tr><td colspan="${cabeceras.length}" class="vacio">${esc(vacio)}</td></tr>`;
  return `<table><thead><tr>${th}</tr></thead><tbody>${cuerpo}</tbody></table>`;
}

function campo(etiqueta, id, control, ayuda = '') {
  return `<div class="campo"><label for="${id}">${esc(etiqueta)}</label>${control}${ayuda ? `<div class="ayuda">${esc(ayuda)}</div>` : ''}</div>`;
}

const buscador = (clave, texto) =>
  `<input class="busca" data-entrada="filtro" placeholder="${esc(texto)}" value="${esc(estado.busquedas[clave] || '')}" aria-label="${esc(texto)}">`;
const papel = texto => `<div class="papel texto">${esc(texto)}</div>`;

/* ------------------------------------------------------------------ ventanas emergentes */
function abrirModal(titulo, cuerpo, botones) {
  const pie = botones.map(b => `<button class="btn ${b.clase || 'btn-o'}" data-accion="${b.accion}"${b.id ? ` id="${b.id}"` : ''}${b.datos || ''}>${esc(b.texto)}</button>`).join('');
  $('modal-raiz').innerHTML = `<div class="velo" data-accion="velo"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-titulo">
    <h3 id="modal-titulo">${esc(titulo)}</h3><div id="modal-error"></div>${cuerpo}<div class="modal-pie">${pie}</div></div></div>`;
  const primero = $('modal-raiz').querySelector('input:not([type=checkbox]), select');
  if (primero) primero.focus();
}

function cerrarModal() {
  $('modal-raiz').innerHTML = '';
  estado.cobro = null;
  if (seccion === 'pos' && $('pos-q')) $('pos-q').focus();
}

function errorModal(texto) {
  if ($('modal-error')) $('modal-error').innerHTML = texto ? `<div class="error-caja">${esc(texto)}</div>` : '';
}

const hayModal = () => Boolean($('modal-raiz').firstChild);
const botonesGuardar = (texto, accion, datos = '') => [{ texto: 'Cancelar', accion: 'cerrar-modal' }, { texto, clase: 'btn-p', accion, datos }];

/* Guarda con el método de la API; si el dominio lo rechaza, el mensaje queda en la ventana; si no, cierra y actualiza. */
async function guardar(metodo, ...argumentos) {
  const r = await llamar(metodo, ...argumentos);
  if (!r.exito) { errorModal(r.mensaje); return; }
  cerrarModal();
  aviso(r.mensaje);
  render();
}

/* ------------------------------------------------------------------ menú y secciones */
function pintarMenu() {
  let grupo = '';
  let html = '';
  for (const s of SECCIONES) {
    if (s.grupo !== grupo) { grupo = s.grupo; html += `<div class="grupo">${esc(grupo.toUpperCase())}</div>`; }
    const activo = s.id === seccion;
    html += `<button class="nav${activo ? ' activo' : ''}" data-accion="ir" data-id="${s.id}"${activo ? ' aria-current="page"' : ''}>
      <span class="icono">${svg(s.id)}</span><span class="texto">${esc(s.titulo)}</span></button>`;
  }
  $('menu').innerHTML = html;
}

const VISTAS = {};
const TABLAS = {};

async function render() {
  pintarMenu();
  const titulo = SECCIONES.find(s => s.id === seccion).titulo;
  const vista = await VISTAS[seccion]();
  $('contenido').innerHTML = `<div class="encabezado"><div><h2>${esc(titulo)}</h2><p>${esc(vista.sub)}</p></div>
    <div class="acciones">${vista.acciones || ''}</div></div>${vista.html}`;
  if (vista.despues) vista.despues();
}

function ir(id) {
  seccion = id;
  estado.sugerencias = [];
  render();
}

async function refrescarTabla() {
  if (TABLAS[seccion] && $('tabla')) $('tabla').innerHTML = await TABLAS[seccion]();
}

/* ------------------------------------------------------------------ punto de venta (HU-04, CU-01, CU-02) */
VISTAS.pos = async () => ({
  sub: 'Pasa el lector de código de barras o escribe el nombre y presiona Enter',
  acciones: '<button class="btn btn-o" data-accion="limpiar-carrito">Limpiar venta</button>',
  html: `<div class="pos"><div>
      <div class="tarjeta margen"><div class="pos-busca">
        <div class="pos-fila"><label class="ocultar-visual" for="pos-q">Nombre del producto</label>
          <input id="pos-q" class="grande" placeholder="Código de barras o nombre del producto  (F2)" autocomplete="off" data-entrada="pos-buscar">
          <label class="ocultar-visual" for="pos-cant">Cantidad</label><input id="pos-cant" class="cant" type="number" min="1" value="1"></div>
        <div id="pos-sug" class="sugerencias oculto" role="listbox"></div>
      </div><div class="nota-pie">Si pides más de lo que hay, el sistema te dice cuántas unidades quedan.</div></div>
      <div class="tabla-caja sin-margen ticket"><div id="pos-ticket"></div></div>
    </div><div>
      <div class="total-caja"><div class="t">TOTAL A COBRAR</div><div class="m" id="pos-total">$ 0</div><div class="s" id="pos-items">Sin productos</div></div>
      <div class="pos-botones">
        <button class="btn btn-p" id="btn-contado" data-accion="cobrar" data-modo="CONTADO">Cobrar de contado <span class="tecla">F9</span></button>
        <button class="btn btn-o" id="btn-credito" data-accion="cobrar" data-modo="CREDITO">Vender a crédito (fiado) <span class="tecla">F4</span></button>
      </div>
      <div class="tarjeta arriba"><h3>Atajos</h3><div class="sec atajos"><span class="tecla">F2</span> buscar producto · <span class="tecla">Enter</span> agregar<br>
        <span class="tecla">F9</span> cobrar de contado · <span class="tecla">F4</span> a crédito<br><span class="tecla">Esc</span> cerrar ventana o limpiar la búsqueda</div></div>
    </div></div>`,
  despues: async () => { pintarCarrito(await llamar('carrito')); $('pos-q').focus(); },
});

function pintarCarrito(carrito) {
  estado.carrito = carrito;
  if (!$('pos-ticket')) return;
  const filas = carrito.lineas.map((l, i) => `<tr><td>${i + 1}</td><td><b>${esc(l.nombre)}</b><div class="sec">Disponibles: ${esc(l.disponibles)}</div></td>
    <td class="num">${esc(l.precio)}</td><td class="num"><span class="cantidad-ctl"><button data-accion="menos" data-id="${esc(l.id)}" aria-label="Quitar una unidad de ${esc(l.nombre)}">−</button>
    <b>${esc(l.cantidad)}</b><button data-accion="mas" data-id="${esc(l.id)}" aria-label="Agregar una unidad de ${esc(l.nombre)}">+</button></span></td><td class="num"><b>${esc(l.importe)}</b></td>
    <td><button class="btn btn-ch btn-quitar" data-accion="quitar" data-id="${esc(l.id)}">Quitar</button></td></tr>`);
  $('pos-ticket').innerHTML = tabla(['#', 'Producto', '>Precio', '>Cantidad', '>Importe', ''], filas, 'La venta está vacía. Busca un producto para empezar.');
  $('pos-total').textContent = carrito.total;
  $('pos-items').textContent = carrito.resumen;
  $('btn-contado').disabled = $('btn-credito').disabled = carrito.vacio;
}

async function buscarSugerencias(texto) {
  const turno = ++estado.turno;                     // si llega una respuesta vieja después de una nueva, se ignora
  const encontrados = texto.trim() ? await llamar('buscar', texto) : [];
  if (turno !== estado.turno) return;
  estado.sugerencias = encontrados.slice(0, MAXIMO_SUGERENCIAS);
  estado.sugSel = 0;
  pintarSugerencias();
}

function pintarSugerencias() {
  const caja = $('pos-sug');
  if (!caja) return;
  caja.classList.toggle('oculto', !estado.sugerencias.length);
  caja.innerHTML = estado.sugerencias.map((p, i) => `<button class="${i === estado.sugSel ? 'sel' : ''}" role="option" data-accion="elegir-sug" data-indice="${i}">
    <span><b>${esc(p.nombre)}</b></span><span>${esc(p.precio)} · ${esc(p.disponibles)} und.</span></button>`).join('');
}

async function agregarProducto(producto) {
  const r = await llamar('agregar', producto.id, val('pos-cant') || '1');
  if (!r.exito) { aviso(r.mensaje, true); return; }
  pintarCarrito(r.carrito);
  $('pos-q').value = '';
  $('pos-cant').value = 1;
  estado.sugerencias = [];
  pintarSugerencias();
  $('pos-q').focus();
}

async function teclaEnBusqueda(ev) {
  const n = estado.sugerencias.length;
  if (ev.key === 'ArrowDown' && n) { ev.preventDefault(); estado.sugSel = (estado.sugSel + 1) % n; pintarSugerencias(); }
  else if (ev.key === 'ArrowUp' && n) { ev.preventDefault(); estado.sugSel = (estado.sugSel - 1 + n) % n; pintarSugerencias(); }
  else if (ev.key === 'Escape') { ev.target.value = ''; estado.sugerencias = []; pintarSugerencias(); }
  else if (ev.key === 'Enter') {
    ev.preventDefault();
    const texto = ev.target.value;
    // El lector escribe rápido y oprime Enter: se busca de nuevo con el texto completo (no con sugerencias viejas),
    // salvo que el vendedor haya elegido una sugerencia con las flechas.
    const elegida = n && estado.sugSel > 0;
    const lista = elegida ? estado.sugerencias : (texto.trim() ? await llamar('buscar', texto) : []);
    if (!lista.length) { aviso(texto.trim() ? `No encontré «${texto}». Revisa el nombre.` : 'Escribe el nombre de un producto.', true); return; }
    agregarProducto(lista[elegida ? estado.sugSel : 0]);
  }
}

/* ---- cobro: de contado (solo efectivo, CU-02) o a crédito (CU-01) */
function abrirCobro(modo) {
  if (!estado.carrito || estado.carrito.vacio) { aviso('Agrega al menos un producto antes de cobrar.', true); return; }
  estado.cobro = { modo, clientes: [] };
  pintarCobro();
}

async function pintarCobro() {
  const { modo } = estado.cobro;
  const carrito = estado.carrito;
  const pestanas = `<div class="pestañas"><button class="${modo === 'CONTADO' ? 'sel' : ''}" data-accion="cobro-modo" data-modo="CONTADO">De contado (efectivo)</button>
    <button class="${modo === 'CREDITO' ? 'sel' : ''}" data-accion="cobro-modo" data-modo="CREDITO">A crédito (fiado)</button></div>`;
  const total = `<div class="total-grande"><div class="sec">Total a cobrar</div><div class="m">${esc(carrito.total)}</div></div>`;
  let cuerpo;
  if (modo === 'CONTADO') {
    cuerpo = campo('Efectivo recibido', 'c-recibido', `<input id="c-recibido" type="number" min="0" data-entrada="cobro-recibido" placeholder="${esc(carrito.total_numero)}">`,
      'Si lo dejas vacío se toma el valor exacto.');
  } else {
    estado.cobro.clientes = await llamar('clientes_para_credito');
    const opciones = estado.cobro.clientes.map(k => `<option value="${esc(k.id)}">${esc(k.nombres)}</option>`).join('');
    cuerpo = campo('Cliente', 'c-cliente', `<select id="c-cliente" data-cambio="cobro-cliente"><option value="">Elige un cliente…</option>${opciones}</select>`);
  }
  abrirModal(modo === 'CREDITO' ? 'Vender a crédito' : 'Cobrar venta', `${pestanas}${total}${cuerpo}<div id="c-info"></div>`,
    [{ texto: 'Cancelar', accion: 'cerrar-modal' }, { texto: 'Confirmar venta', clase: 'btn-p', accion: 'confirmar-cobro', id: 'btn-confirmar' }]);
  actualizarCobro();
}

const recibido = () => val('c-recibido').trim() || String(estado.carrito.total_numero);

async function actualizarCobro() {
  if (!estado.cobro || !$('btn-confirmar')) return;
  if (estado.cobro.modo === 'CONTADO') {
    const turno = ++estado.turno;
    const r = await llamar('cambio', recibido());
    if (turno !== estado.turno || !$('c-info')) return;
    $('c-info').innerHTML = `<div class="${r.exito ? 'ok-caja' : 'error-caja'}">${esc(r.mensaje)}</div>`;
    $('btn-confirmar').disabled = !r.exito;
  } else {
    const cliente = estado.cobro.clientes.find(k => String(k.id) === val('c-cliente'));
    $('c-info').innerHTML = cliente ? papel(cliente.texto) : '';
    $('btn-confirmar').disabled = !cliente;
  }
}

async function confirmarCobro() {
  const boton = $('btn-confirmar');
  boton.disabled = true;
  const r = estado.cobro.modo === 'CONTADO'
    ? await llamar('cobrar_de_contado', recibido())
    : await llamar('vender_a_credito', val('c-cliente'));
  pintarCarrito(r.carrito);
  if (!r.exito) { errorModal(r.mensaje); boton.disabled = false; return; }
  aviso(r.mensaje);
  mostrarTicket('Venta registrada', r.ticket, 'Nueva venta');
}

function mostrarTicket(titulo, ticket, boton = 'Cerrar') {
  estado.cobro = null;
  abrirModal(titulo, papel(ticket), [{ texto: 'Imprimir', accion: 'imprimir' }, { texto: boton, clase: 'btn-p', accion: 'cerrar-modal' }]);
}

/* ------------------------------------------------------------------ ventas (RF-05) */
VISTAS.ventas = async () => {
  const filas = (await llamar('ventas')).map(f => {
    const [numero, fecha, tipo, cliente, total] = f.valores;
    return `<tr><td><b>${esc(numero)}</b></td><td>${esc(fecha)}</td><td>${insignia(tipo === 'Crédito' ? 'i-av' : 'i-ok', tipo === 'Crédito' ? 'Fiado' : 'Efectivo')}</td>
      <td>${cliente === '—' ? '<span class="sec">Mostrador</span>' : esc(cliente)}</td><td class="num"><b>${esc(total)}</b></td>
      <td><button class="btn btn-s btn-ch" data-accion="ver-venta" data-id="${esc(f.id)}">Ver ticket</button></td></tr>`;
  });
  return {
    sub: 'Las ventas registradas, de la más reciente a la más antigua',
    acciones: '<button class="btn btn-p" data-accion="ir" data-id="pos">Nueva venta</button>',
    html: `<div class="tabla-caja"><div class="cab-tabla"><h3>Últimas ventas</h3></div>
      ${tabla(['N.º', 'Fecha y hora', 'Tipo', 'Cliente', '>Total', ''], filas, 'Todavía no hay ventas registradas.')}
      <div class="nota-pie">Se muestran las 50 más recientes. Las ventas no se borran ni se anulan.</div></div>`,
  };
};

/* ------------------------------------------------------------------ productos (HU-01, HU-02) */
TABLAS.productos = async () => {
  const filas = (await llamar('productos', estado.busquedas.productos || '')).map(f => {
    const [nombre, compra, venta, disponibles] = f.valores;
    return `<tr><td><b>${esc(nombre)}</b></td><td class="num">${esc(compra)}</td><td class="num"><b>${esc(venta)}</b></td><td class="num">${esc(disponibles)}</td>
      <td><button class="btn btn-s btn-ch" data-accion="editar-producto" data-id="${esc(f.id)}">Editar</button></td></tr>`;
  });
  return tabla(['Producto', '>Precio de compra', '>Precio de venta', '>Disponibles', ''], filas, 'No hay productos con esa búsqueda.');
};

VISTAS.productos = async () => ({
  sub: 'Registra tus productos y corrige su nombre o sus precios',
  acciones: '<button class="btn btn-p" data-accion="nuevo-producto">+ Nuevo producto</button>',
  html: `<div class="tabla-caja"><div class="cab-tabla"><h3>Catálogo</h3>${buscador('productos', 'Buscar producto por nombre')}</div>
    <div id="tabla">${await TABLAS.productos()}</div>
    <div class="nota-pie">Cambiar el precio no cambia las ventas anteriores: cada venta guarda el precio con que se vendió. Los productos no se borran.</div></div>`,
});

function abrirNuevoProducto() {
  abrirModal('Nuevo producto', `${formularioDeProducto()}
    ${campo('Cantidad inicial', 'f-cantidad', '<input id="f-cantidad" type="number" min="0" value="0">', 'Las unidades que hay hoy en la tienda.')}`,
  botonesGuardar('Guardar producto', 'guardar-producto'));
}

function formularioDeProducto(datos = { nombre: '', compra: '', venta: '', minimo: '0', codigo: '' }) {
  return `${campo('Código de barras (opcional)', 'f-codigo', `<input id="f-codigo" data-lector autocomplete="off" placeholder="Pase el lector por el código" value="${esc(datos.codigo)}">`)}
    ${campo('Nombre del producto', 'f-nombre', `<input id="f-nombre" placeholder="Ej.: Arroz 500 g" value="${esc(datos.nombre)}">`)}
    <div class="dos">${campo('Precio de compra', 'f-compra', `<input id="f-compra" type="number" min="0" value="${esc(datos.compra)}">`)}
    ${campo('Precio de venta', 'f-venta', `<input id="f-venta" type="number" min="0" value="${esc(datos.venta)}">`)}</div>
    ${campo('Stock mínimo', 'f-minimo', `<input id="f-minimo" type="number" min="0" value="${esc(datos.minimo)}">`,
    'Cuando queden estas unidades o menos, el producto sale «por reponer». 0 = sin aviso.')}`;
}

async function abrirEdicionDeProducto(id) {
  const datos = await llamar('datos_producto', id);
  if (!datos) { aviso('Ese producto ya no existe.', true); return; }
  abrirModal('Editar producto', `${formularioDeProducto(datos)}<div class="nota-pie">Las existencias se cambian con «Registrar entrada» en Existencias.
    Las ventas anteriores conservan el precio con que se vendieron.</div>`, botonesGuardar('Guardar cambios', 'guardar-edicion-producto', ` data-id="${esc(id)}"`));
}

/* ------------------------------------------------------------------ existencias (HU-03, RF-04) */
TABLAS.existencias = async () => {
  const filas = (await llamar('existencias', estado.busquedas.existencias || '')).map(f => {
    const [nombre, disponibles] = f.valores;
    return `<tr><td><b>${esc(nombre)}</b> ${f.reponer ? insignia('i-av', 'Por reponer') : ''}</td><td class="num"><b>${esc(disponibles)}</b></td>
      <td><button class="btn btn-s btn-ch" data-accion="nueva-entrada" data-id="${esc(f.id)}">+ Entrada</button></td></tr>`;
  });
  return tabla(['Producto', '>Disponibles', ''], filas, 'No hay productos con esa búsqueda.');
};

async function panelPorReponer() {
  const filas = (await llamar('por_reponer')).map(f => {
    const [nombre, disponibles, minimo] = f.valores;
    return `<tr><td><b>${esc(nombre)}</b></td><td class="num">${esc(disponibles)}</td><td class="num">${esc(minimo)}</td>
      <td><button class="btn btn-s btn-ch" data-accion="nueva-entrada" data-id="${esc(f.id)}">+ Entrada</button></td></tr>`;
  });
  if (!filas.length) return '';
  return `<div class="tabla-caja"><div class="cab-tabla"><h3>Por reponer (${filas.length})</h3></div>
    ${tabla(['Producto', '>Quedan', '>Stock mínimo', ''], filas, '')}
    <div class="nota-pie">Productos que llegaron a su stock mínimo o menos. Salen de la lista al registrar una entrada.</div></div>`;
}

VISTAS.existencias = async () => {
  const movimientos = (await llamar('movimientos')).map(f => {
    const [fecha, producto, movimiento, cantidad] = f.valores;
    return `<tr><td>${esc(fecha)}</td><td><b>${esc(producto)}</b></td><td>${insignia(movimiento === 'Entrada' ? 'i-ok' : 'i-info', movimiento)}</td><td class="num">${esc(cantidad)}</td></tr>`;
  });
  return {
    sub: 'Cuánto hay de cada producto y qué entró o salió',
    acciones: '<button class="btn btn-p" data-accion="nueva-entrada" data-id="">+ Registrar entrada</button>',
    html: `${await panelPorReponer()}<div class="tabla-caja"><div class="cab-tabla"><h3>Existencias por producto</h3>${buscador('existencias', 'Buscar producto')}</div>
      <div id="tabla">${await TABLAS.existencias()}</div></div>
      <div class="tabla-caja"><div class="cab-tabla"><h3>Movimientos de inventario</h3></div>
      ${tabla(['Fecha y hora', 'Producto', 'Movimiento', '>Cantidad'], movimientos, 'Aún no hay movimientos.')}
      <div class="nota-pie">Se muestran los 50 más recientes. Las ventas descuentan el inventario solas.</div></div>`,
  };
};

async function abrirEntrada(id) {
  const productos = await llamar('existencias', '');
  if (!productos.length) { aviso('Primero registra un producto en la sección Productos.', true); return; }
  const opciones = productos.map(f => `<option value="${esc(f.id)}"${String(f.id) === String(id) ? ' selected' : ''}>${esc(f.valores[0])} (hay ${esc(f.valores[1])})</option>`).join('');
  abrirModal('Registrar entrada de mercancía', `${campo('Producto', 'e-producto', `<select id="e-producto">${opciones}</select>`)}
    ${campo('Cantidad que entra', 'e-cantidad', '<input id="e-cantidad" type="number" min="1" value="1">')}`,
  botonesGuardar('Registrar entrada', 'guardar-entrada'));
  if ($('e-cantidad') && id) $('e-cantidad').focus();
}

/* ------------------------------------------------------------------ clientes (HU-05, RF-07) */
TABLAS.clientes = async () => {
  const filas = (await llamar('clientes', estado.busquedas.clientes || '')).map(f => {
    const [nombre, limite, debe, disponible] = f.valores;
    return `<tr><td><b>${esc(nombre)}</b></td><td class="num">${esc(limite)}</td><td class="num">${esc(debe)}</td>
      <td class="num">${disponible === 'Sin crédito' ? insignia('i-gris', disponible) : `<b>${esc(disponible)}</b>`}</td>
      <td><button class="btn btn-s btn-ch" data-accion="ver-cliente" data-id="${esc(f.id)}">Ver detalle</button>
      <button class="btn btn-s btn-ch" data-accion="editar-cliente" data-id="${esc(f.id)}">Editar</button></td></tr>`;
  });
  return tabla(['Cliente', '>Límite', '>Debe', '>Disponible', ''], filas, 'No hay clientes con esa búsqueda.');
};

VISTAS.clientes = async () => ({
  sub: 'Personas a las que se les puede vender a crédito',
  acciones: '<button class="btn btn-p" data-accion="nuevo-cliente">+ Nuevo cliente</button>',
  html: `<div class="tabla-caja"><div class="cab-tabla"><h3>Clientes</h3>${buscador('clientes', 'Buscar cliente')}</div>
    <div id="tabla">${await TABLAS.clientes()}</div>
    <div class="nota-pie">El crédito disponible es el límite menos lo que debe. Los datos de los clientes son personales: protégelos.</div></div>`,
});

function formularioDeCliente(datos, ayudaDelLimite = '') {
  return `${campo('Nombre', 'k-nombre', `<input id="k-nombre" value="${esc(datos.nombres)}">`)}
    <div class="dos">${campo('Teléfono (opcional)', 'k-telefono', `<input id="k-telefono" inputmode="tel" value="${esc(datos.telefono || '')}">`)}
    ${campo('Dirección (opcional)', 'k-direccion', `<input id="k-direccion" value="${esc(datos.direccion || '')}">`)}</div>
    <div class="campo"><label class="check"><input type="checkbox" id="k-credito"${datos.credito ? ' checked' : ''}> Puede comprar a crédito (fiado)</label></div>
    <div class="dos">${campo('Límite de crédito', 'k-limite', `<input id="k-limite" type="number" min="0" value="${esc(datos.limite)}">`, ayudaDelLimite)}
    ${campo('Plazo máximo para pagar (días)', 'k-plazo', `<input id="k-plazo" type="number" min="1" value="${esc(datos.plazo)}">`)}</div>`;
}

async function abrirNuevoCliente() {
  const plazo = await llamar('plazo_por_defecto');
  abrirModal('Nuevo cliente', formularioDeCliente({ nombres: '', credito: true, limite: '0', plazo }), botonesGuardar('Guardar cliente', 'guardar-cliente'));
}

async function abrirEdicionDeCliente(id) {
  const datos = await llamar('datos_cliente', id);
  if (!datos) { aviso('Ese cliente ya no existe.', true); return; }
  abrirModal('Editar cliente', `${formularioDeCliente(datos, 'Si queda por debajo de lo que debe, no se le podrá fiar más hasta que abone.')}
    <div class="nota-pie">El nuevo plazo se usa en las próximas ventas; las cuentas que ya tiene conservan su fecha de vencimiento.</div>`,
  botonesGuardar('Guardar cambios', 'guardar-edicion-cliente', ` data-id="${esc(id)}"`));
}

/* ------------------------------------------------------------------ créditos y abonos (HU-06, RF-09) */
TABLAS.creditos = async () => {
  const respuesta = await llamar('creditos', estado.verPagadas);
  if ($('resumen-creditos')) $('resumen-creditos').textContent = respuesta.resumen;
  const filas = respuesta.filas.map(f => {
    const [cliente, saldo, vence, estadoCuenta] = f.valores;
    const abierta = estadoCuenta !== 'Pagada';
    const clase = { Abierta: 'i-av', Vencida: 'i-mal', Pagada: 'i-ok' }[estadoCuenta];
    return `<tr><td><b>${esc(cliente)}</b></td><td class="num"><b>${esc(saldo)}</b></td><td>${esc(vence)}</td>
      <td>${insignia(clase, estadoCuenta)}</td>
      <td><button class="btn btn-s btn-ch" data-accion="ver-credito" data-id="${esc(f.id)}">Detalle</button>
      ${abierta ? `<button class="btn btn-p btn-ch" data-accion="abonar" data-id="${esc(f.id)}">Abonar</button>` : ''}</td></tr>`;
  });
  return tabla(['Cliente', '>Saldo', 'Vence', 'Estado', ''], filas, estado.verPagadas ? 'No hay cuentas por cobrar.' : 'No hay cuentas pendientes.');
};

async function panelDeAtrasados() {
  const filas = (await llamar('atrasados')).map(f => {
    const [cliente, saldo, vencia, atraso] = f.valores;
    return `<tr><td><b>${esc(cliente)}</b></td><td class="num"><b>${esc(saldo)}</b></td><td>${esc(vencia)}</td><td>${insignia('i-mal', atraso)}</td>
      <td><button class="btn btn-p btn-ch" data-accion="abonar" data-id="${esc(f.id)}">Abonar</button></td></tr>`;
  });
  if (!filas.length) return '';
  return `<div class="tabla-caja"><div class="cab-tabla"><h3>Atrasados (${filas.length})</h3></div>
    ${tabla(['Cliente', '>Saldo', 'Vencía', 'Atraso', ''], filas, '')}
    <div class="nota-pie">Cuentas que pasaron el plazo del cliente sin pagarse. A estos clientes no se les puede fiar hasta que paguen. No se cobran intereses.</div></div>`;
}

VISTAS.creditos = async () => {
  const resumen = (await llamar('creditos', false)).resumen;
  const filtro = (valor, texto) => `<button class="${estado.verPagadas === valor ? 'sel' : ''}" data-accion="filtro-pagadas" data-valor="${valor}">${texto}</button>`;
  return {
    sub: 'Qué le deben a la tienda y cuánto va pagando cada cliente',
    html: `<div class="kpis"><div class="kpi azul"><div class="ic">${svg('creditos')}</div><div class="valor" id="resumen-creditos">${esc(resumen)}</div>
      <div class="rotulo">Cuentas abiertas</div></div></div>
      ${await panelDeAtrasados()}
      <div class="tabla-caja"><div class="cab-tabla"><h3>Cuentas por cobrar</h3><div class="filtros">${filtro(false, 'Pendientes')}${filtro(true, 'Todas (con pagadas)')}</div></div>
      <div id="tabla">${await TABLAS.creditos()}</div>
      <div class="nota-pie">El saldo es la deuda menos los abonos; un abono no puede ser mayor al saldo. El vencimiento usa el plazo máximo de cada cliente.</div></div>`,
  };
};

async function abrirAbono(id) {
  const detalle = await llamar('detalle_credito', id);
  abrirModal('Registrar abono', `<div class="papel texto margen">${esc(detalle)}</div>${campo('Valor del abono', 'a-valor', '<input id="a-valor" type="number" min="1">')}`,
    botonesGuardar('Registrar abono', 'guardar-abono', ` data-id="${esc(id)}"`));
}

/* ------------------------------------------------------------------ acciones (clic en un elemento con data-accion) */
const ACCIONES = {
  ir: el => ir(el.dataset.id),
  velo: cerrarModal,
  'cerrar-modal': cerrarModal,
  'limpiar-carrito': async () => { pintarCarrito(await llamar('limpiar')); $('pos-q').focus(); },
  quitar: async el => pintarCarrito(await llamar('quitar', el.dataset.id)),
  menos: async el => pintarCarrito(await llamar('quitar_uno', el.dataset.id)),
  mas: async el => { const r = await llamar('agregar', el.dataset.id, '1'); if (!r.exito) aviso(r.mensaje, true); pintarCarrito(r.carrito); },
  'elegir-sug': el => agregarProducto(estado.sugerencias[Number(el.dataset.indice)]),
  cobrar: el => abrirCobro(el.dataset.modo),
  'cobro-modo': el => { estado.cobro.modo = el.dataset.modo; pintarCobro(); },
  'confirmar-cobro': confirmarCobro,
  imprimir: () => window.print(),
  'ver-venta': async el => mostrarTicket(`Venta #${el.dataset.id}`, await llamar('ticket', el.dataset.id)),
  'nuevo-producto': abrirNuevoProducto,
  'guardar-producto': () => guardar('registrar_producto', val('f-nombre'), val('f-compra'), val('f-venta'), val('f-cantidad'), val('f-minimo'), val('f-codigo')),
  'editar-producto': el => abrirEdicionDeProducto(el.dataset.id),
  'guardar-edicion-producto': el => guardar('editar_producto', el.dataset.id, val('f-nombre'), val('f-compra'), val('f-venta'), val('f-minimo'), val('f-codigo')),
  'nueva-entrada': el => abrirEntrada(el.dataset.id),
  'guardar-entrada': () => guardar('registrar_entrada', val('e-producto'), val('e-cantidad')),
  'nuevo-cliente': abrirNuevoCliente,
  'guardar-cliente': () => guardar('registrar_cliente', val('k-nombre'), $('k-credito').checked, val('k-limite'), val('k-plazo'), val('k-telefono'), val('k-direccion')),
  'editar-cliente': el => abrirEdicionDeCliente(el.dataset.id),
  'guardar-edicion-cliente': el => guardar('editar_cliente', el.dataset.id, val('k-nombre'), $('k-credito').checked, val('k-limite'), val('k-plazo'), val('k-telefono'), val('k-direccion')),
  'ver-cliente': async el => abrirModal('Detalle del cliente', papel(await llamar('detalle_cliente', el.dataset.id)), [{ texto: 'Cerrar', clase: 'btn-p', accion: 'cerrar-modal' }]),
  'filtro-pagadas': el => { estado.verPagadas = el.dataset.valor === 'true'; render(); },
  'ver-credito': async el => abrirModal('Detalle de la cuenta', papel(await llamar('detalle_credito', el.dataset.id)), [{ texto: 'Cerrar', clase: 'btn-p', accion: 'cerrar-modal' }]),
  abonar: el => abrirAbono(el.dataset.id),
  'guardar-abono': el => guardar('abonar', el.dataset.id, val('a-valor')),
};

const ENTRADAS = {
  'pos-buscar': el => buscarSugerencias(el.value),
  'cobro-recibido': actualizarCobro,
  filtro: el => { estado.busquedas[seccion] = el.value; refrescarTabla(); },
};
const CAMBIOS = { 'cobro-cliente': actualizarCobro };

document.addEventListener('click', ev => {
  const el = ev.target.closest('[data-accion]');
  if (!el || el.disabled) return;
  if (el.dataset.accion === 'velo' && ev.target !== el) return;   // un clic dentro de la ventana no la cierra
  ACCIONES[el.dataset.accion](el);
});
document.addEventListener('input', ev => { const f = ENTRADAS[ev.target.dataset.entrada]; if (f) f(ev.target); });
document.addEventListener('change', ev => { const f = CAMBIOS[ev.target.dataset.cambio]; if (f) f(ev.target); });

document.addEventListener('keydown', ev => {
  if (ev.target.id === 'pos-q' && ['ArrowDown', 'ArrowUp', 'Enter', 'Escape'].includes(ev.key)) { teclaEnBusqueda(ev); return; }
  if (ev.key === 'Escape' && hayModal()) { cerrarModal(); return; }
  if (ev.key === 'Enter' && ev.target.dataset.lector !== undefined) { ev.preventDefault(); $('f-nombre').focus(); return; }  // Enter del lector
  if (ev.key === 'Enter' && hayModal() && ev.target.tagName === 'INPUT') {
    ev.preventDefault();
    const principal = $('modal-raiz').querySelector('.modal-pie .btn-p');
    if (principal && !principal.disabled) principal.click();
    return;
  }
  if (ev.key === 'F2') { ev.preventDefault(); if (seccion !== 'pos') ir('pos'); else $('pos-q').focus(); }
  if ((ev.key === 'F9' || ev.key === 'F4') && seccion === 'pos' && !hayModal()) { ev.preventDefault(); abrirCobro(ev.key === 'F9' ? 'CONTADO' : 'CREDITO'); }
});

window.addEventListener('unhandledrejection', ev => ev.preventDefault());   // el aviso ya se mostró en llamar()
window.addEventListener('pywebviewready', render);
