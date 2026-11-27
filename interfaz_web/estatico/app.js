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
  reportes: '<path d="M3 3v18h18"/><path d="M7 15l4-4 3 3 5-6"/>',
  caja: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M3 11h18M7 4h10v3M8 15h3"/>',
  tienda: '<path d="M3 9l1.5-5h15L21 9"/><path d="M4 9v11h16V9"/><path d="M3 9h18M9 20v-6h6v6"/>',
  respaldos: '<ellipse cx="12" cy="5.5" rx="7.5" ry="2.5"/><path d="M4.5 5.5v13c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5v-13M4.5 12c0 1.4 3.4 2.5 7.5 2.5s7.5-1.1 7.5-2.5"/>',
  usuarios: '<rect x="4" y="10" width="16" height="11" rx="2"/><path d="M8 10V7a4 4 0 018 0v3"/><circle cx="12" cy="15.5" r="1.5"/>',
};
const SECCIONES = [
  { id: 'pos', titulo: 'Punto de venta', grupo: 'Operación' },
  { id: 'ventas', titulo: 'Ventas', grupo: 'Operación' },
  { id: 'caja', titulo: 'Caja', grupo: 'Operación', permiso: 'manejar_caja' },
  { id: 'productos', titulo: 'Productos', grupo: 'Inventario' },
  { id: 'existencias', titulo: 'Existencias', grupo: 'Inventario' },
  { id: 'clientes', titulo: 'Clientes', grupo: 'Clientes y crédito' },
  { id: 'creditos', titulo: 'Créditos y abonos', grupo: 'Clientes y crédito' },
  { id: 'reportes', titulo: 'Reportes', grupo: 'Administración', permiso: 'ver_reportes' },
  { id: 'respaldos', titulo: 'Respaldos', grupo: 'Administración', permiso: 'gestionar_respaldos' },
  { id: 'tienda', titulo: 'Tienda', grupo: 'Administración', permiso: 'configurar_tienda' },
  { id: 'usuarios', titulo: 'Usuarios', grupo: 'Administración', permiso: 'gestionar_usuarios' },
];
const MENSAJE_FALLA = 'No se pudo completar la operación. Intente de nuevo; si sigue fallando, cierre y abra la tienda.';
const MAXIMO_SUGERENCIAS = 8;

let seccion = 'pos';
const estado = { busquedas: {}, verPagadas: false, sugerencias: [], sugSel: 0, turno: 0, carrito: null, cobro: null, periodo: 'hoy', sesion: null };

/* Fase 2: esconder un botón es solo comodidad; la barrera real está en la API de Python (@requiere). */
const puede = permiso => Boolean(estado.sesion && estado.sesion.permisos.includes(permiso));

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
  for (const s of SECCIONES.filter(s => !s.permiso || puede(s.permiso))) {
    if (s.grupo !== grupo) { grupo = s.grupo; html += `<div class="grupo">${esc(grupo.toUpperCase())}</div>`; }
    const activo = s.id === seccion;
    html += `<button class="nav${activo ? ' activo' : ''}" data-accion="ir" data-id="${s.id}"${activo ? ' aria-current="page"' : ''}>
      <span class="icono">${svg(s.id)}</span><span class="texto">${esc(s.titulo)}</span></button>`;
  }
  if (estado.sesion) {
    html += `<div class="sesion"><div><b>${esc(estado.sesion.nombre)}</b><div class="sec">${esc(estado.sesion.rol)}</div></div>
      <button class="btn btn-s btn-ch" data-accion="salir">Cerrar sesión</button></div>`;
  }
  $('menu').innerHTML = html;
}

/* ------------------------------------------------------------------ ingreso (fase 2, CR-01) */
async function iniciar() {
  const r = await llamar('estado_sesion');
  estado.sesion = r.usuario;
  if (estado.sesion) render(); else pintarIngreso(r.hay_usuarios);
}

function pintarIngreso(hayUsuarios) {
  $('menu').innerHTML = '';
  const primeraVez = !hayUsuarios;
  const clave = (id, texto) => campo(texto, id, `<input id="${id}" type="password" autocomplete="off">`);
  $('contenido').innerHTML = `<div class="ingreso"><div class="tarjeta" id="form-ingreso">
    <h2>${primeraVez ? 'Primera vez: cree la cuenta del jefe' : 'Ingresar'}</h2>
    <p class="sec">${primeraVez ? 'El jefe puede hacer todo y crea después los usuarios de los empleados.' : 'Escriba su usuario y su clave.'}</p>
    <div id="modal-error"></div>
    ${primeraVez ? campo('Nombre de la persona', 'i-nombre', '<input id="i-nombre" autocomplete="off">') : ''}
    ${campo('Usuario', 'i-usuario', '<input id="i-usuario" autocomplete="off" placeholder="Ej.: pedro">')}
    ${clave('i-clave', 'Clave')}
    ${primeraVez ? clave('i-confirmar', 'Repita la clave') : ''}
    <button class="btn btn-p" data-accion="${primeraVez ? 'crear-jefe' : 'ingresar'}">${primeraVez ? 'Crear y entrar' : 'Entrar'}</button>
  </div></div>`;
  $(primeraVez ? 'i-nombre' : 'i-usuario').focus();
}

async function terminarIngreso(r) {
  if (!r.exito) { errorModal(r.mensaje); $('i-clave').value = ''; $('i-clave').focus(); return; }
  estado.sesion = r.estado.usuario;
  seccion = 'pos';
  aviso(r.mensaje);
  render();
}

async function salir() {
  cerrarModal();
  const r = await llamar('cerrar_sesion');
  estado.sesion = null;
  estado.carrito = null;
  pintarIngreso(r.hay_usuarios);
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
  html: `<div id="aviso-caja"></div><div class="pos"><div>
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
  despues: async () => {
    pintarCarrito(await llamar('carrito'));
    $('pos-q').focus();
    const caja = await llamar('estado_caja');       // fase 4: se puede vender con la caja cerrada, pero se avisa
    if (!caja.abierta && $('aviso-caja')) {
      $('aviso-caja').innerHTML = `<div class="aviso">La caja está cerrada: lo que se venda no entra en ningún cierre.
        <button class="btn btn-s btn-ch" data-accion="ir" data-id="caja">Abrir caja</button></div>`;
    }
  },
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

/* ---- cobro: de contado en efectivo, transferencia o mixto (CU-02, respuesta 1.2) o a crédito (CU-01) */
const FORMAS_DE_COBRO = [['EFECTIVO', 'Efectivo'], ['TRANSFERENCIA', 'Transferencia'], ['MIXTO', 'Mixto'], ['CREDITO', 'A crédito (fiado)']];

function abrirCobro(modo) {
  if (!estado.carrito || estado.carrito.vacio) { aviso('Agrega al menos un producto antes de cobrar.', true); return; }
  estado.cobro = { modo: modo === 'CONTADO' ? 'EFECTIVO' : modo, clientes: [] };
  pintarCobro();
}

function cuerpoDeContado(modo, carrito) {
  if (modo === 'EFECTIVO') {
    return campo('Efectivo recibido', 'c-recibido', `<input id="c-recibido" type="number" min="0" data-entrada="cobro-recibido" placeholder="${esc(carrito.total_numero)}">`,
      'Si lo dejas vacío se toma el valor exacto.');
  }
  if (modo === 'TRANSFERENCIA') {
    return `<div class="nota-pie">Revisa en el celular que llegó la transferencia (Nequi, Daviplata) por el total. No se da cambio.</div>`;
  }
  return `<div class="dos">${campo('Por transferencia', 'c-transferencia', '<input id="c-transferencia" type="number" min="0" data-entrada="cobro-recibido">', 'No puede pasar del total.')}
    ${campo('Efectivo recibido', 'c-efectivo', '<input id="c-efectivo" type="number" min="0" data-entrada="cobro-recibido">', 'El cambio sale de aquí.')}</div>`;
}

async function pintarCobro() {
  const { modo } = estado.cobro;
  const carrito = estado.carrito;
  const pestanas = `<div class="pestañas">${FORMAS_DE_COBRO.map(([valor, texto]) =>
    `<button class="${modo === valor ? 'sel' : ''}" data-accion="cobro-modo" data-modo="${valor}">${texto}</button>`).join('')}</div>`;
  const total = `<div class="total-grande"><div class="sec">Total a cobrar</div><div class="m">${esc(carrito.total)}</div></div>`;
  let cuerpo;
  if (modo !== 'CREDITO') {
    cuerpo = cuerpoDeContado(modo, carrito);
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

/* [efectivo, transferencia] según la pestaña elegida */
function pagos() {
  const total = String(estado.carrito.total_numero);
  if (estado.cobro.modo === 'TRANSFERENCIA') return ['0', total];
  if (estado.cobro.modo === 'MIXTO') return [val('c-efectivo').trim() || '0', val('c-transferencia').trim() || '0'];
  return [recibido(), '0'];
}

async function actualizarCobro() {
  if (!estado.cobro || !$('btn-confirmar')) return;
  if (estado.cobro.modo !== 'CREDITO') {
    const turno = ++estado.turno;
    const r = await llamar('cambio', ...pagos());
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
  const r = estado.cobro.modo !== 'CREDITO'
    ? await llamar('cobrar_de_contado', ...pagos())
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
    return `<tr><td><b>${esc(numero)}</b></td><td>${esc(fecha)}</td><td>${insignia(tipo === 'Crédito' ? 'i-av' : tipo === 'Efectivo' ? 'i-ok' : 'i-info', tipo === 'Crédito' ? 'Fiado' : tipo)}</td>
      <td>${cliente === '—' ? '<span class="sec">Mostrador</span>' : esc(cliente)} ${f.estado ? insignia(f.estado === 'Anulada' ? 'i-mal' : 'i-gris', f.estado) : ''}</td>
      <td class="num"><b>${esc(total)}</b></td>
      <td><button class="btn btn-s btn-ch" data-accion="ver-venta" data-id="${esc(f.id)}">Ver ticket</button>
      ${f.estado === 'Anulada' || !puede('devolver') ? '' : `<button class="btn btn-s btn-ch" data-accion="abrir-devolucion" data-id="${esc(f.id)}">Devolver</button>`}</td></tr>`;
  });
  return {
    sub: 'Las ventas registradas, de la más reciente a la más antigua',
    acciones: '<button class="btn btn-p" data-accion="ir" data-id="pos">Nueva venta</button>',
    html: `<div class="tabla-caja"><div class="cab-tabla"><h3>Últimas ventas</h3></div>
      ${tabla(['N.º', 'Fecha y hora', 'Tipo', 'Cliente', '>Total', ''], filas, 'Todavía no hay ventas registradas.')}
      <div class="nota-pie">Se muestran las 50 más recientes. Las ventas no se borran: una devolución o una anulación queda registrada con su motivo.</div></div>`,
  };
};

/* Devolver productos o anular la venta (respuesta 1.5). El motivo es obligatorio. */
async function abrirDevolucion(id) {
  const filas = (await llamar('para_devolver', id)).map(f => {
    const [nombre, vendidas, devueltas, pendientes, precio] = f.valores;
    return `<tr><td><b>${esc(nombre)}</b><div class="sec">Vendidas ${esc(vendidas)} · devueltas ${esc(devueltas)}</div></td><td class="num">${esc(precio)}</td>
      <td class="num">${pendientes > 0 ? `<input class="cant" type="number" min="0" max="${esc(pendientes)}" value="0" data-producto="${esc(f.id)}" aria-label="Unidades de ${esc(nombre)} a devolver">` : '<span class="sec">Nada</span>'}</td></tr>`;
  });
  abrirModal(`Devolver productos de la venta #${id}`, `${tabla(['Producto', '>Precio', '>Devolver'], filas, '')}
    ${campo('Motivo', 'd-motivo', '<input id="d-motivo" placeholder="Ej.: producto en mal estado">', 'Obligatorio. Queda guardado con la devolución.')}
    <div class="nota-pie">Lo devuelto vuelve al inventario. Si fue fiado, se descuenta de la deuda; si sobra, se devuelve en efectivo.</div>`,
  [{ texto: 'Cancelar', accion: 'cerrar-modal' }, { texto: 'Anular toda la venta', accion: 'anular-venta', datos: ` data-id="${esc(id)}"` },
   { texto: 'Devolver lo marcado', clase: 'btn-p', accion: 'guardar-devolucion', datos: ` data-id="${esc(id)}"` }]);
}

function cantidadesADevolver() {
  const cantidades = {};
  document.querySelectorAll('#modal-raiz [data-producto]').forEach(campo => { cantidades[campo.dataset.producto] = campo.value; });
  return cantidades;
}

async function terminarDevolucion(r, id) {
  if (!r.exito) { errorModal(r.mensaje); return; }
  aviso(r.mensaje);
  await render();
  mostrarTicket(`Venta #${id}`, r.ticket);
}

/* ------------------------------------------------------------------ productos (HU-01, HU-02) */
TABLAS.productos = async () => {
  const filas = (await llamar('productos', estado.busquedas.productos || '')).map(f => {
    const [nombre, compra, venta, disponibles] = f.valores;
    const estadoDelProducto = puede('configurar_tienda')
      ? `<button class="btn btn-s btn-ch" data-accion="activar-producto" data-id="${esc(f.id)}" data-activo="${f.activo ? '' : '1'}">${f.activo ? 'Desactivar' : 'Activar'}</button>` : '';
    return `<tr${f.activo ? '' : ' class="inactivo"'}><td><b>${esc(nombre)}</b> ${f.activo ? '' : insignia('i-gris', 'Inactivo')}</td>
      <td class="num">${esc(compra)}</td><td class="num"><b>${esc(venta)}</b></td><td class="num">${esc(disponibles)}</td>
      <td>${puede('gestionar_productos') ? `<button class="btn btn-s btn-ch" data-accion="editar-producto" data-id="${esc(f.id)}">Editar</button>` : ''}
      ${estadoDelProducto}</td></tr>`;
  });
  return tabla(['Producto', '>Precio de compra', '>Precio de venta', '>Disponibles', ''], filas, 'No hay productos con esa búsqueda.');
};

VISTAS.productos = async () => ({
  sub: 'Registra tus productos y corrige su nombre o sus precios',
  acciones: puede('gestionar_productos') ? '<button class="btn btn-p" data-accion="nuevo-producto">+ Nuevo producto</button>' : '',
  html: `<div class="tabla-caja"><div class="cab-tabla"><h3>Catálogo</h3>${buscador('productos', 'Buscar producto por nombre')}</div>
    <div id="tabla">${await TABLAS.productos()}</div>
    <div class="nota-pie">Cambiar el precio no cambia las ventas anteriores: cada venta guarda el precio con que se vendió. Los productos no se borran.</div></div>`,
});

function abrirNuevoProducto() {
  abrirModal('Nuevo producto', `${formularioDeProducto()}
    ${campo('Cantidad inicial', 'f-cantidad', '<input id="f-cantidad" type="number" min="0" value="0">', 'Las unidades que hay hoy en la tienda.')}`,
  botonesGuardar('Guardar producto', 'guardar-producto'));
}

function formularioDeProducto(datos = { nombre: '', compra: '', venta: '', minimo: '0', codigo: '', aviso: '0' }) {
  return `${campo('Código de barras (opcional)', 'f-codigo', `<input id="f-codigo" data-lector autocomplete="off" placeholder="Pase el lector por el código" value="${esc(datos.codigo)}">`)}
    ${campo('Nombre del producto', 'f-nombre', `<input id="f-nombre" placeholder="Ej.: Arroz 500 g" value="${esc(datos.nombre)}">`)}
    <div class="dos">${campo('Precio de compra', 'f-compra', `<input id="f-compra" type="number" min="0" value="${esc(datos.compra)}">`)}
    ${campo('Precio de venta', 'f-venta', `<input id="f-venta" type="number" min="0" value="${esc(datos.venta)}">`)}</div>
    <div class="dos">${campo('Stock mínimo', 'f-minimo', `<input id="f-minimo" type="number" min="0" value="${esc(datos.minimo)}">`,
    'Con estas unidades o menos sale «por reponer». 0 = sin aviso.')}
    ${campo('Días de aviso de vencimiento', 'f-aviso', `<input id="f-aviso" type="number" min="0" value="${esc(datos.aviso)}">`,
    'Cuántos días antes avisar que un lote va a vencer.')}</div>`;
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
    return `<tr${f.activo ? '' : ' class="inactivo"'}><td><b>${esc(nombre)}</b> ${f.reponer ? insignia('i-av', 'Por reponer') : ''}${f.activo ? '' : insignia('i-gris', 'Inactivo')}</td><td class="num"><b>${esc(disponibles)}</b></td>
      <td><button class="btn btn-s btn-ch" data-accion="nueva-entrada" data-id="${esc(f.id)}">+ Entrada</button>
      <button class="btn btn-s btn-ch" data-accion="nueva-salida" data-id="${esc(f.id)}">− Salida</button></td></tr>`;
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

/* Lotes por vencer (RF-10, RF-13): solo un aviso; no cambian las existencias. El primero es el que vence antes. */
const CLASE_DEL_LOTE = { 'Vencido': 'i-mal', 'Por vencer': 'i-av', 'Al día': 'i-ok' };

async function panelDeLotes() {
  const lotes = await llamar('lotes');
  const filas = lotes.filas.map(f => {
    const [producto, numero, vence, cantidad, estadoLote, falta] = f.valores;
    return `<tr><td><b>${esc(producto)}</b><div class="sec">Lote ${esc(numero)} · ${esc(cantidad)} u.</div></td><td>${esc(vence)}<div class="sec">${esc(falta)}</div></td>
      <td>${insignia(CLASE_DEL_LOTE[estadoLote] || 'i-gris', estadoLote)}</td>
      <td><button class="btn btn-s btn-ch" data-accion="retirar-lote" data-id="${esc(f.id)}">Ya no está</button></td></tr>`;
  });
  return `<div class="tabla-caja"><div class="cab-tabla"><h3>Lotes por vencer${lotes.alerta ? ` (${lotes.alerta} en alerta)` : ''}</h3>
    <button class="btn btn-s btn-ch" data-accion="nuevo-lote">+ Registrar lote</button></div>
    ${tabla(['Producto', 'Vence', 'Estado', ''], filas, 'No hay lotes registrados.')}
    <div class="nota-pie">Ordenados por fecha: venda primero los de arriba. Es solo un aviso, no cambia las existencias. «Ya no está» lo quita de la lista.</div></div>`;
}

async function abrirLote() {
  const productos = await llamar('existencias', '');
  if (!productos.length) { aviso('Primero registra un producto en la sección Productos.', true); return; }
  const opciones = productos.map(f => `<option value="${esc(f.id)}">${esc(f.valores[0])}</option>`).join('');
  abrirModal('Registrar lote', `${campo('Producto', 'l-producto', `<select id="l-producto">${opciones}</select>`)}
    <div class="dos">${campo('Número de lote (opcional)', 'l-numero', '<input id="l-numero" placeholder="Ej.: L-2045">')}
    ${campo('Unidades del lote', 'l-cantidad', '<input id="l-cantidad" type="number" min="1" value="1">')}</div>
    ${campo('Fecha de vencimiento', 'l-fecha', '<input id="l-fecha" type="date">')}
    <div class="nota-pie">El lote no suma ni resta existencias: para eso está «Registrar entrada».</div>`,
  botonesGuardar('Registrar lote', 'guardar-lote'));
}

VISTAS.existencias = async () => {
  const movimientos = (await llamar('movimientos')).map(f => {
    const [fecha, producto, movimiento, cantidad] = f.valores;
    const clase = movimiento === 'Entrada' ? 'i-ok' : movimiento.startsWith('Salida manual') ? 'i-av' : 'i-info';
    return `<tr><td>${esc(fecha)}</td><td><b>${esc(producto)}</b></td><td>${insignia(clase, movimiento)}</td><td class="num">${esc(cantidad)}</td></tr>`;
  });
  return {
    sub: 'Cuánto hay de cada producto y qué entró o salió',
    acciones: `<button class="btn btn-o" data-accion="nueva-salida" data-id="">− Registrar salida</button>
      <button class="btn btn-p" data-accion="nueva-entrada" data-id="">+ Registrar entrada</button>`,
    html: `${await panelPorReponer()}${await panelDeLotes()}<div class="tabla-caja"><div class="cab-tabla"><h3>Existencias por producto</h3>${buscador('existencias', 'Buscar producto')}</div>
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

/* Salida manual (fase 3, respuesta 4.4): mercancía que sale sin venderse. Si quien está no es jefe, el jefe la
   autoriza escribiendo ahí su usuario y su clave (Python lo revisa; aquí solo se muestran los campos). */
async function abrirSalida(id) {
  const productos = await llamar('existencias', '');
  if (!productos.length) { aviso('Primero registra un producto en la sección Productos.', true); return; }
  const opciones = productos.map(f => `<option value="${esc(f.id)}"${String(f.id) === String(id) ? ' selected' : ''}>${esc(f.valores[0])} (hay ${esc(f.valores[1])})</option>`).join('');
  const motivos = (await llamar('motivos_de_salida')).map(m => `<option value="${esc(m)}">${esc(m)}</option>`).join('');
  const autorizacion = puede('registrar_salida') ? '' : `<div class="aviso">El jefe debe autorizar esta salida con su usuario y su clave.</div>
    <div class="dos">${campo('Usuario del jefe', 's-jefe', '<input id="s-jefe" autocomplete="off">')}
    ${campo('Clave del jefe', 's-clave', '<input id="s-clave" type="password" autocomplete="off">')}</div>`;
  abrirModal('Registrar salida de mercancía', `${campo('Producto', 's-producto', `<select id="s-producto">${opciones}</select>`)}
    <div class="dos">${campo('Cantidad que sale', 's-cantidad', '<input id="s-cantidad" type="number" min="1" value="1">')}
    ${campo('Motivo', 's-motivo', `<select id="s-motivo">${motivos}</select>`)}</div>
    ${campo('Detalle', 's-detalle', '<input id="s-detalle" placeholder="Ej.: se rompió el empaque">', 'Obligatorio si el motivo es «Otro».')}
    ${autorizacion}<div class="nota-pie">Baja las existencias y queda en el historial con su motivo. Su costo sale en Reportes.</div>`,
  botonesGuardar('Registrar salida', 'guardar-salida'));
  if ($('s-cantidad') && id) $('s-cantidad').focus();
}

/* ------------------------------------------------------------------ clientes (HU-05, RF-07) */
TABLAS.clientes = async () => {
  const filas = (await llamar('clientes', estado.busquedas.clientes || '')).map(f => {
    const [nombre, limite, debe, disponible] = f.valores;
    return `<tr><td><b>${esc(nombre)}</b></td><td class="num">${esc(limite)}</td><td class="num">${esc(debe)}</td>
      <td class="num">${disponible === 'Sin crédito' ? insignia('i-gris', disponible) : `<b>${esc(disponible)}</b>`}</td>
      <td><button class="btn btn-s btn-ch" data-accion="ver-cliente" data-id="${esc(f.id)}">Ver detalle</button>
      ${puede('gestionar_clientes') ? `<button class="btn btn-s btn-ch" data-accion="editar-cliente" data-id="${esc(f.id)}">Editar</button>` : ''}</td></tr>`;
  });
  return tabla(['Cliente', '>Límite', '>Debe', '>Disponible', ''], filas, 'No hay clientes con esa búsqueda.');
};

VISTAS.clientes = async () => ({
  sub: 'Personas a las que se les puede vender a crédito',
  acciones: puede('gestionar_clientes') ? '<button class="btn btn-p" data-accion="nuevo-cliente">+ Nuevo cliente</button>' : '',
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

/* ------------------------------------------------------------------ reportes (fase 1 de la hoja de ruta) */
const PERIODOS = [['hoy', 'Hoy'], ['semana', 'Últimos 7 días'], ['mes', 'Este mes']];
const COLOR_DE_TARJETA = ['', 'azul', 'ambar', 'azul'];   // '' = verde, el color base de .kpi

VISTAS.reportes = async () => {
  const r = await llamar('reporte', estado.periodo);
  const filtros = PERIODOS.map(([valor, texto]) =>
    `<button class="${r.periodo === valor ? 'sel' : ''}" data-accion="filtro-periodo" data-valor="${valor}">${esc(texto)}</button>`).join('');
  const tarjetas = r.tarjetas.map(([rotulo, valor], i) => `<div class="kpi ${COLOR_DE_TARJETA[i]}"><div class="ic">${svg('reportes')}</div>
    <div class="valor">${esc(valor)}</div><div class="rotulo">${esc(rotulo)}</div></div>`).join('');
  const formas = r.formas.map(([forma, valor]) => `<tr><td>${esc(forma)}</td><td class="num"><b>${esc(valor)}</b></td></tr>`);
  const productos = r.mas_vendidos.map(([nombre, unidades, valor], i) =>
    `<tr><td>${i + 1}</td><td><b>${esc(nombre)}</b></td><td class="num">${esc(unidades)}</td><td class="num">${esc(valor)}</td></tr>`);
  return {
    sub: `Cómo le fue a la tienda · ${r.rango}`,
    acciones: `<div class="filtros">${filtros}</div>`,
    html: `<div class="kpis">${tarjetas}</div>
      ${r.nota ? `<div class="aviso">${esc(r.nota)}</div>` : ''}
      <div class="tabla-caja"><div class="cab-tabla"><h3>Por forma de pago</h3></div>
        ${tabla(['Concepto', '>Valor'], formas, '')}
        <div class="nota-pie">Vendido (neto) = lo vendido menos lo devuelto. Lo fiado no es dinero en caja: entra cuando el cliente abona.</div></div>
      <div class="tabla-caja"><div class="cab-tabla"><h3>Productos más vendidos</h3></div>
        ${tabla(['#', 'Producto', '>Unidades', '>Valor'], productos, 'No hay ventas en este periodo.')}
        <div class="nota-pie">Ganancia = precio de venta menos precio de compra de lo vendido (sin gastos como arriendo o servicios).</div></div>`,
  };
};

/* ------------------------------------------------------------------ caja (fase 4) */
async function historialDeCaja() {
  if (!puede('ver_reportes')) return '';
  const filas = (await llamar('historial_caja')).map(f => {
    const [abrio, cerro, quienAbre, quienCierra, base, esperado, contado, diferencia] = f.valores;
    const clase = diferencia === 'La caja cuadra' ? 'i-ok' : diferencia.startsWith('Faltan') ? 'i-mal' : 'i-av';
    return `<tr><td>${esc(abrio)}<div class="sec">${esc(quienAbre)}</div></td><td>${esc(cerro)}<div class="sec">${esc(quienCierra)}</div></td>
      <td class="num">${esc(base)}</td><td class="num">${esc(esperado)}</td><td class="num"><b>${esc(contado)}</b></td><td>${insignia(clase, diferencia)}</td></tr>`;
  });
  return `<div class="tabla-caja"><div class="cab-tabla"><h3>Cierres anteriores</h3></div>
    ${tabla(['Abrió', 'Cerró', '>Base', '>Esperado', '>Contado', 'Resultado'], filas, 'Todavía no hay cierres.')}</div>`;
}

VISTAS.caja = async () => {
  const caja = await llamar('estado_caja');
  if (!caja.abierta) {
    return {
      sub: 'Abra la caja al empezar el día con el dinero que hay para dar cambio',
      html: `<div class="tarjeta margen caja-form"><h3>Abrir caja</h3>
        ${campo('Base (efectivo con que abre)', 'c-base', '<input id="c-base" type="number" min="0" placeholder="Ej.: 50000">', 'Cambia cada día: escriba lo que hay ahora en la caja.')}
        <button class="btn btn-p" data-accion="abrir-caja">Abrir caja</button></div>${await historialDeCaja()}`,
      despues: () => $('c-base').focus(),
    };
  }
  const filas = caja.detalle.map(([concepto, valor]) => `<tr><td>${esc(concepto)}</td><td class="num">${esc(valor)}</td></tr>`);
  filas.push(`<tr><td><b>Debería haber en efectivo</b></td><td class="num"><b>${esc(caja.esperado)}</b></td></tr>`);
  return {
    sub: `Abierta desde el ${caja.desde} por ${caja.abrio}`,
    acciones: '<button class="btn btn-p" data-accion="contar-caja">Cerrar caja</button>',
    html: `<div class="tabla-caja"><div class="cab-tabla"><h3>Efectivo del turno</h3></div>${tabla(['Concepto', '>Valor'], filas, '')}
      <div class="nota-pie">Las transferencias y lo fiado no están en la caja. Los abonos se cuentan como efectivo.
      Puede cerrar la aplicación sin cerrar la caja: el turno sigue abierto la próxima vez.</div></div>${await historialDeCaja()}`,
  };
};

function abrirConteo() {
  abrirModal('Cerrar caja', `${campo('¿Cuánto efectivo hay en la caja?', 'c-contado', '<input id="c-contado" type="number" min="0">', 'Cuente billetes y monedas, incluida la base.')}`,
    [{ texto: 'Cancelar', accion: 'cerrar-modal' }, { texto: 'Revisar', clase: 'btn-p', accion: 'revisar-caja' }]);
}

/* Muestra cuánto falta o sobra; «Contar de nuevo» vuelve al conteo sin cerrar y «Cerrar caja» confirma. */
async function revisarCaja() {
  const contado = val('c-contado');
  const r = await llamar('revisar_cierre', contado);
  if (!r.exito) { errorModal(r.mensaje); return; }
  const clase = r.cuadra ? 'verde' : 'roja';
  abrirModal('Cerrar caja', `<div class="aviso ${clase}"><b>${esc(r.mensaje)}</b></div>
    ${tabla(['Concepto', '>Valor'], [`<tr><td>Debería haber</td><td class="num">${esc(r.esperado)}</td></tr>`,
      `<tr><td>Contó</td><td class="num"><b>${esc(r.contado)}</b></td></tr>`], '')}
    <div class="nota-pie">Si cree que se equivocó al contar, cuente de nuevo antes de cerrar.</div>`,
  [{ texto: 'Contar de nuevo', accion: 'contar-caja' }, { texto: 'Cerrar caja', clase: 'btn-p', accion: 'confirmar-cierre', datos: ` data-contado="${esc(contado)}"` }]);
}

/* ------------------------------------------------------------------ datos de la tienda (fase 6, solo el jefe) */
VISTAS.tienda = async () => {
  const d = await llamar('datos_tienda');
  const entrada = (id, valor, ejemplo = '') => `<input id="${id}" value="${esc(valor)}" placeholder="${esc(ejemplo)}">`;
  return {
    sub: 'Los datos que salen en el ticket de cada venta',
    html: `<div class="tienda"><div class="tarjeta margen"><h3>Datos del ticket</h3>
        ${campo('Nombre de la tienda', 't-nombre', entrada('t-nombre', d.nombre))}
        <div class="dos">${campo('NIT (opcional)', 't-nit', entrada('t-nit', d.nit, 'Ej.: 900123456-7'))}
        ${campo('Teléfono (opcional)', 't-telefono', entrada('t-telefono', d.telefono))}</div>
        ${campo('Dirección (opcional)', 't-direccion', entrada('t-direccion', d.direccion))}
        ${campo('Mensaje al final del ticket (opcional)', 't-mensaje', entrada('t-mensaje', d.mensaje, 'Ej.: Gracias por su compra'))}
        <button class="btn btn-p" data-accion="guardar-tienda">Guardar datos</button></div>
      <div class="tarjeta margen"><h3>Así empieza el ticket</h3>${papel(d.vista_previa)}
        <div class="nota-pie">El ticket no es una factura: es un comprobante interno.</div></div></div>`,
  };
};

/* ------------------------------------------------------------------ respaldos (fase 5, solo el jefe) */
VISTAS.respaldos = async () => {
  const datos = await llamar('respaldos');
  const filas = datos.filas.map(f => {
    const [fecha, tipo, tamano] = f.valores;
    return `<tr><td><b>${esc(fecha)}</b><div class="sec">${esc(f.id)}</div></td><td>${insignia(tipo === 'Respaldo' ? 'i-ok' : 'i-gris', tipo)}</td>
      <td class="num">${esc(tamano)}</td>
      <td><button class="btn btn-s btn-ch" data-accion="restaurar-respaldo" data-id="${esc(f.id)}">Restaurar</button></td></tr>`;
  });
  return {
    sub: 'Copias de seguridad de la tienda en una carpeta de este computador',
    acciones: '<button class="btn btn-p" data-accion="respaldar-ahora">Respaldar ahora</button>',
    html: `<div class="tarjeta margen"><h3>Carpeta de los respaldos</h3>
        ${campo('Ruta completa de la carpeta', 'r-carpeta', `<input id="r-carpeta" value="${esc(datos.carpeta)}" placeholder="Ej.: C:\\Respaldos de la tienda">`,
          'Se copia sola al cerrar la aplicación y al cerrar la caja. Se guardan las 30 más recientes.')}
        <button class="btn btn-s" data-accion="guardar-carpeta">Guardar carpeta</button></div>
      <div class="tabla-caja"><div class="cab-tabla"><h3>Respaldos guardados</h3></div>
        ${tabla(['Fecha', 'Tipo', '>Tamaño', ''], filas, 'Todavía no hay respaldos en esta carpeta.')}
        <div class="nota-pie">Restaurar reemplaza los datos actuales por los del respaldo. Antes se guarda una «copia de antes de restaurar»,
        por si se eligió mal. Después hay que volver a ingresar.</div></div>`,
  };
};

async function restaurarRespaldo(el) {
  if (!el.dataset.confirmado) {                    // segundo clic confirma, como al anular una venta
    el.dataset.confirmado = '1'; el.textContent = 'Sí, restaurar este'; el.classList.add('btn-p'); return;
  }
  const r = await llamar('restaurar_respaldo', el.dataset.id);
  if (!r.exito) { aviso(r.mensaje, true); render(); return; }
  aviso(r.mensaje);
  estado.sesion = null;
  estado.carrito = null;
  pintarIngreso(r.estado.hay_usuarios);
}

/* ------------------------------------------------------------------ usuarios (fase 2, solo el jefe) */
VISTAS.usuarios = async () => {
  const filas = (await llamar('usuarios')).map(f => {
    const [nombre, usuario, rol, activo] = f.valores;
    const estaActivo = activo === 'Activo';
    return `<tr><td><b>${esc(nombre)}</b></td><td>${esc(usuario)}</td><td>${insignia(rol === 'Jefe' ? 'i-info' : 'i-gris', rol)}</td>
      <td>${insignia(estaActivo ? 'i-ok' : 'i-mal', activo)}</td>
      <td><button class="btn btn-s btn-ch" data-accion="clave-usuario" data-id="${esc(f.id)}" data-usuario="${esc(usuario)}">Cambiar clave</button>
      <button class="btn btn-s btn-ch" data-accion="activar-usuario" data-id="${esc(f.id)}" data-activo="${estaActivo ? '' : '1'}">${estaActivo ? 'Desactivar' : 'Activar'}</button></td></tr>`;
  });
  return {
    sub: 'Quién puede entrar a la tienda y qué puede hacer',
    acciones: '<button class="btn btn-p" data-accion="nuevo-usuario">+ Nuevo usuario</button>',
    html: `<div class="tabla-caja"><div class="cab-tabla"><h3>Usuarios</h3></div>
      ${tabla(['Nombre', 'Usuario', 'Rol', 'Estado', ''], filas, '')}
      <div class="nota-pie">El empleado vende, consulta, registra entradas y lotes y recibe abonos. Solo el jefe devuelve o anula ventas,
      crea o edita productos, precios y clientes, ve los reportes y maneja los usuarios. Un usuario desactivado no puede entrar.</div></div>`,
  };
};

function abrirNuevoUsuario() {
  const clave = (id, texto) => campo(texto, id, `<input id="${id}" type="password" autocomplete="off">`);
  abrirModal('Nuevo usuario', `${campo('Nombre de la persona', 'u-nombre', '<input id="u-nombre">')}
    <div class="dos">${campo('Usuario', 'u-usuario', '<input id="u-usuario" autocomplete="off" placeholder="Ej.: pedro">', 'Sin espacios.')}
    ${campo('Rol', 'u-rol', '<select id="u-rol"><option value="EMPLEADO">Empleado</option><option value="JEFE">Jefe</option></select>')}</div>
    <div class="dos">${clave('u-clave', 'Clave')}${clave('u-confirmar', 'Repita la clave')}</div>`,
  botonesGuardar('Crear usuario', 'guardar-usuario'));
}

function abrirCambioDeClave(id, usuario) {
  const clave = (campoId, texto) => campo(texto, campoId, `<input id="${campoId}" type="password" autocomplete="off">`);
  abrirModal(`Cambiar la clave de «${usuario}»`, `<div class="dos">${clave('u-clave', 'Clave nueva')}${clave('u-confirmar', 'Repita la clave')}</div>`,
    botonesGuardar('Cambiar clave', 'guardar-clave', ` data-id="${esc(id)}"`));
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
  'abrir-devolucion': el => abrirDevolucion(el.dataset.id),
  'guardar-devolucion': async el => terminarDevolucion(await llamar('devolver', el.dataset.id, cantidadesADevolver(), val('d-motivo')), el.dataset.id),
  'anular-venta': async el => {
    if (!val('d-motivo').trim()) { errorModal('Escribe el motivo de la devolución'); return; }
    if (!el.dataset.confirmado) { el.dataset.confirmado = '1'; el.textContent = 'Sí, anular toda la venta'; el.classList.add('btn-p'); return; }  // segundo clic confirma
    terminarDevolucion(await llamar('anular', el.dataset.id, val('d-motivo')), el.dataset.id);
  },
  'nuevo-producto': abrirNuevoProducto,
  'guardar-producto': () => guardar('registrar_producto', val('f-nombre'), val('f-compra'), val('f-venta'), val('f-cantidad'), val('f-minimo'), val('f-codigo'), val('f-aviso')),
  'editar-producto': el => abrirEdicionDeProducto(el.dataset.id),
  'guardar-edicion-producto': el => guardar('editar_producto', el.dataset.id, val('f-nombre'), val('f-compra'), val('f-venta'), val('f-minimo'), val('f-codigo'), val('f-aviso')),
  'nueva-entrada': el => abrirEntrada(el.dataset.id),
  'guardar-entrada': () => guardar('registrar_entrada', val('e-producto'), val('e-cantidad')),
  'nueva-salida': el => abrirSalida(el.dataset.id),
  'abrir-caja': async () => { const r = await llamar('abrir_caja', val('c-base')); aviso(r.mensaje, !r.exito); if (r.exito) render(); },
  'contar-caja': abrirConteo,
  'respaldar-ahora': async () => { const r = await llamar('respaldar_ahora'); aviso(r.mensaje, !r.exito); render(); },
  'guardar-carpeta': async () => { const r = await llamar('cambiar_carpeta_respaldos', val('r-carpeta')); aviso(r.mensaje, !r.exito); if (r.exito) render(); },
  'restaurar-respaldo': restaurarRespaldo,
  'guardar-tienda': async () => {
    const r = await llamar('guardar_datos_tienda', val('t-nombre'), val('t-nit'), val('t-direccion'), val('t-telefono'), val('t-mensaje'));
    aviso(r.mensaje, !r.exito); if (r.exito) render();
  },
  'activar-producto': async el => { const r = await llamar('activar_producto', el.dataset.id, Boolean(el.dataset.activo)); aviso(r.mensaje, !r.exito); refrescarTabla(); },
  'revisar-caja': revisarCaja,
  'confirmar-cierre': el => guardar('cerrar_caja', el.dataset.contado),
  'guardar-salida': () => guardar('registrar_salida', val('s-producto'), val('s-cantidad'), val('s-motivo'), val('s-detalle'), val('s-jefe'), val('s-clave')),
  'nuevo-lote': abrirLote,
  'guardar-lote': () => guardar('registrar_lote', val('l-producto'), val('l-numero'), val('l-fecha'), val('l-cantidad')),
  'retirar-lote': async el => { const r = await llamar('retirar_lote', el.dataset.id); aviso(r.mensaje, !r.exito); render(); },
  'nuevo-cliente': abrirNuevoCliente,
  'guardar-cliente': () => guardar('registrar_cliente', val('k-nombre'), $('k-credito').checked, val('k-limite'), val('k-plazo'), val('k-telefono'), val('k-direccion')),
  'editar-cliente': el => abrirEdicionDeCliente(el.dataset.id),
  'guardar-edicion-cliente': el => guardar('editar_cliente', el.dataset.id, val('k-nombre'), $('k-credito').checked, val('k-limite'), val('k-plazo'), val('k-telefono'), val('k-direccion')),
  'ver-cliente': async el => abrirModal('Detalle del cliente', papel(await llamar('detalle_cliente', el.dataset.id)), [{ texto: 'Cerrar', clase: 'btn-p', accion: 'cerrar-modal' }]),
  'filtro-pagadas': el => { estado.verPagadas = el.dataset.valor === 'true'; render(); },
  'ver-credito': async el => abrirModal('Detalle de la cuenta', papel(await llamar('detalle_credito', el.dataset.id)), [{ texto: 'Cerrar', clase: 'btn-p', accion: 'cerrar-modal' }]),
  abonar: el => abrirAbono(el.dataset.id),
  'guardar-abono': el => guardar('abonar', el.dataset.id, val('a-valor')),
  'filtro-periodo': el => { estado.periodo = el.dataset.valor; render(); },
  ingresar: async () => terminarIngreso(await llamar('iniciar_sesion', val('i-usuario'), val('i-clave'))),
  'crear-jefe': async () => terminarIngreso(await llamar('crear_primer_jefe', val('i-nombre'), val('i-usuario'), val('i-clave'), val('i-confirmar'))),
  salir,
  'nuevo-usuario': abrirNuevoUsuario,
  'guardar-usuario': () => guardar('crear_usuario', val('u-nombre'), val('u-usuario'), val('u-rol'), val('u-clave'), val('u-confirmar')),
  'clave-usuario': el => abrirCambioDeClave(el.dataset.id, el.dataset.usuario),
  'guardar-clave': el => guardar('cambiar_clave_usuario', el.dataset.id, val('u-clave'), val('u-confirmar')),
  'activar-usuario': async el => { const r = await llamar('activar_usuario', el.dataset.id, Boolean(el.dataset.activo)); aviso(r.mensaje, !r.exito); render(); },
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
  if (!estado.sesion) {                                   // pantalla de ingreso: Enter entra; los atajos no hacen nada
    if (ev.key === 'Enter' && ev.target.closest('#form-ingreso')) { ev.preventDefault(); $('form-ingreso').querySelector('.btn-p').click(); }
    return;
  }
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
window.addEventListener('pywebviewready', iniciar);
