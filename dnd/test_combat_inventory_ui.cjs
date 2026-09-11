// node test_combat_inventory_ui.cjs — lógica del DOM, sin dependencias ni partidas.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map(), keyListeners = [];
class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.children = []; this.dataset = {}; this.attributes = {}; this.style = {};
    this.className = ''; this.disabled = false; this.scrollTop = 0;
    this.classList = {add: c => this.toggleClass(c, true), remove: c => this.toggleClass(c, false), toggle: (c, on) => this.toggleClass(c, on)};
  }
  toggleClass(c, on) {const values = new Set(this.className.split(' ')); if (on) values.add(c); else values.delete(c); this.className = [...values].join(' ');}
  append(...nodes) {for (const n of nodes) {n.parent = this; this.children.push(n);}}
  replaceChildren(...nodes) {for (const n of this.children) n.parent = null; this.children = []; this.append(...nodes);}
  setAttribute(k, v) {this.attributes[k] = v;}
  addEventListener(name, fn) {if (name === 'keydown') this.keydown = fn;}
  contains(n) {return n === this || this.children.some(c => c.contains(n));}
  get isConnected() {return this.root || Boolean(this.parent?.isConnected);}
  focus() {document.activeElement = this; this.onfocus?.();}
  querySelectorAll(selector) {
    const matches = n => selector === 'button' ? n.tag === 'button' : selector === '[aria-selected="true"]' ? n.attributes['aria-selected'] === 'true' : selector.startsWith('[data-body-slot=') ? n.dataset.bodySlot === selector.slice(17, -2) : n.tag === 'button' && !n.disabled;
    return this.children.flatMap(c => [...(matches(c) ? [c] : []), ...c.querySelectorAll(selector)]);
  }
  querySelector(selector) {return this.querySelectorAll(selector)[0] || null;}
  getClientRects() {return [1];}
}
const document = {
  activeElement: null, createElement: tag => new Element(tag),
  getElementById(id) {assert(elements.has(id), `Falta ${id} en index.html`); return elements.get(id);},
  addEventListener(name, fn) {if (name === 'keydown') keyListeners.push(fn);}
};
for (const [, tag, id] of fs.readFileSync('web/index.html', 'utf8').matchAll(/<(\w+)\b[^>]*\bid="([^"]+)"/g)) {
  const n = new Element(tag); n.root = true; elements.set(id, n);
}
for (const category of ['consumible', 'arma', 'equipo', 'todos']) {
  const n = new Element('button'); n.dataset.category = category; elements.get('inventoryTabs').append(n);
}
for (const [id, tab] of [['characterTabOverview', 'personaje'], ['characterTabClass', 'clase'], ['characterTabInventory', 'inventario'], ['characterTabSpark', 'chispa']]) {
  elements.get(id).dataset.characterTab = tab; elements.get('characterTabs').append(elements.get(id));
}
elements.get('collectionPanel').append(elements.get('characterTabs'), elements.get('closeCollectionButton'), elements.get('inventoryList'), elements.get('equipmentList'));
let requestCount = 0, resolveFetch;
const context = vm.createContext({document, URLSearchParams, URL,
  window: {clearTimeout, setTimeout, location: {search: '', href: 'http://localhost/', replace() {throw Error('Unexpected reload');}}},
  fetch: async (url, args) => {
    requestCount++;
    return new Promise(resolve => {resolveFetch = response => resolve({ok: true, json: async () => response});});
  }
});
const run = code => vm.runInContext(code, context);
run(fs.readFileSync('web/combat-inventory.js', 'utf8'));
run(fs.readFileSync('web/character-panel.js', 'utf8'));
const app = fs.readFileSync('web/app.js', 'utf8');
run(app.slice(0, app.lastIndexOf('fetch("/api/estado")')));
run('renderizar = () => {renderizarInventario(estado.jugador); renderizarEquipo(estado.jugador); renderizarFichaPersonaje(estado.jugador); renderizarHabilidades(estado.jugador);};');
const sword = {id: 'espada', nombre: 'Espada', clase: 'arma', slot: 'mano_principal', cantidad: 1, equipado: true, puede_equipar: true, tipo_arma: 'espada', tier: 1, ataque: [3, 5], dos_manos: false, estadistica_escalado: 'fuerza', crecimiento_por_punto: .1, requisitos: {}, velocidad: 1, critico: .05, penetracion: 1, durabilidad: 100};
const hammer = {...sword, id: 'maza', nombre: 'Maza', equipado: false, dos_manos: true};
const helmet = {id: 'casco', nombre: 'Casco', clase: 'armadura', slot: 'casco', cantidad: 1, equipado: false, puede_equipar: false, requisitos: {fuerza: 12}, defensa: 3};
const potion = {id: 'pocion', nombre: 'Poción', clase: 'consumible', cantidad: 2, efecto: 'curacion', valor: 20};
const fixture = {fase: 'combate', ui_version: '23', clases: {guerrero: {nombre: 'Guerrero'}}, jugador: {nombre: 'Prueba', nivel: 9, clase: null, clase_nombre: 'Sin clase', chispa: null, chispa_nivel_desbloqueo: 30, habilidades: [], puntos_habilidad: 0, fuerza: 12, destreza: 8, constitucion: 7, stats_base: {fuerza: 10, destreza: 8, constitucion: 7}, bonus_equipo: {fuerza: 2, destreza: 0, constitucion: 0}, ataque_minimo: 13, ataque_maximo: 15, velocidad: 6, evasion: .15, hp: 5, salud_maxima: 60, armadura: 7, armadura_equipo: 3, inventario: [sword, hammer, helmet, potion], equipamiento: {mano_principal: sword, mano_secundaria: null, casco: null, pecho: null, brazos: null, piernas: null}}};
context.fixture = fixture;
const items = () => elements.get('inventoryList').children.filter(n => n.tag === 'button');
(async () => {
  assert(elements.has('characterButton'));
  for (const id of ['skillsButton', 'inventoryButton', 'equipmentButton']) assert(!elements.has(id));
  run('estado = fixture; abrirColeccion()');
  assert.equal(run('coleccionAbierta'), 'personaje');
  assert(!elements.get('characterSummaryPanel').className.includes('hidden'));
  assert(elements.get('inventoryPanel').className.includes('hidden'));
  assert.equal(elements.get('primaryStats').children[0].children[1].textContent, '12');
  assert.equal(elements.get('secondaryStats').children.find(n => n.children[0].textContent === 'Daño del personaje').children[1].textContent, '13–15');
  elements.get('characterTabOverview').onkeydown({key: 'ArrowRight', preventDefault() {}});
  assert.equal(run('coleccionAbierta'), 'clase'); assert.equal(document.activeElement, elements.get('characterTabClass'));
  elements.get('characterTabClass').onkeydown({key: 'End', preventDefault() {}});
  assert.equal(run('coleccionAbierta'), 'chispa'); assert(elements.get('sparkStatus').textContent.includes('30'));
  run('estado.jugador.chispa = "chispa_latente"; renderizarFichaPersonaje(estado.jugador)');
  assert.equal(elements.get('sparkTitle').textContent, 'Chispa latente');
  assert(elements.get('sparkHelp').textContent.includes('aún no está habilitada'));
  assert.equal(elements.get('characterTabSpark').tabIndex, 0);
  assert.equal(elements.get('characterTabClass').tabIndex, -1);
  run('estado = fixture; abrirColeccion("inventario")');
  assert.equal(items().length, 1); assert.equal(items()[0].dataset.inventoryId, 'pocion');
  assert.equal(elements.get('equipmentList').children.length, 6);
  run('filtrarInventario("arma")');
  assert.equal(items().length, 2);
  assert.equal(items()[1].attributes['aria-disabled'], 'true');
  items()[1].onclick(); assert.equal(requestCount, 0, 'Equipo bloqueado en combate');
  run('filtrarInventario("consumible")');
  const button = items()[0]; button.onclick(); button.onclick();
  assert.equal(requestCount, 1, 'Doble clic sólo envía una petición');
  const duplicate = await run('llamarApi("accion", {accion: "atacar"})');
  assert.equal(duplicate, false); assert.equal(requestCount, 1, 'No se permite otra acción mientras espera');
  const next = structuredClone(fixture); next.jugador.hp = 20; next.jugador.inventario.find(i => i.id === 'pocion').cantidad = 1;
  resolveFetch(next);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(run('coleccionAbierta'), null, 'Cierra para mostrar el turno resuelto');
  assert.equal(run('gestionPendiente || solicitudEnCurso'), false);
  run('estado.jugador.hp = estado.jugador.salud_maxima; abrirColeccion("inventario")');
  items()[0].onclick(); assert.equal(requestCount, 1, 'No consume con vida completa');
  run('estado.fase = "muerte"; estado.jugador.hp = 0; renderizar()');
  items()[0].onclick(); assert.equal(requestCount, 1, 'Sin acciones tras morir');
  run('estado.fase = "transicion"; estado.jugador.hp = 40; filtrarInventario("equipo", "casco")');
  assert.equal(items().length, 1); assert.equal(items()[0].attributes['aria-disabled'], 'true');
  run('filtrarInventario("arma")');
  assert.equal(items()[1].attributes['aria-disabled'], 'false', 'Equipo disponible entre combates');
  items()[1].onclick(); assert.equal(requestCount, 2);
  const equipped = structuredClone(next); equipped.fase = 'transicion'; equipped.jugador.equipamiento.mano_principal = hammer;
  equipped.jugador.inventario[0].equipado = false; equipped.jugador.inventario[1].equipado = true;
  resolveFetch(equipped); await new Promise(resolve => setImmediate(resolve));
  assert.equal(run('coleccionAbierta'), 'inventario', 'Equipar conserva la ventana');
  assert.equal(run('estado.jugador.equipamiento.mano_principal.id'), 'maza');
  run('filtrarInventario("equipo", "pecho")'); assert.equal(items().length, 0);
  keyListeners.forEach(fn => fn({key: 'Escape'})); assert.equal(run('coleccionAbierta'), null);
  run('abrirColeccion("clase")');
  assert(elements.get('characterSummaryPanel').className.includes('hidden'));
  assert(elements.get('inventoryPanel').className.includes('hidden'));
  assert(!elements.get('skillsPanel').className.includes('hidden'));
  run('estado.jugador.clase_pendiente = true; estado.fase = "combate"; renderizarFichaPersonaje(estado.jugador)');
  assert.equal(elements.get('characterClassChoices').children[0].disabled, true);
  run('estado.fase = "transicion"; renderizarFichaPersonaje(estado.jugador)');
  assert.equal(elements.get('characterClassChoices').children[0].disabled, false);
  run('seleccionarPestanaPersonaje("personaje"); filtrarInventario("arma", "mano_principal")');
  assert.equal(run('coleccionAbierta'), 'inventario');
  assert.equal(items().length, 2);
  console.log('PASS: botón único, cuatro pestañas/teclado, estadísticas del motor, clase/chispa, filtros, slots, requisitos, pociones, doble clic, muerte, actualización y Escape.');
})().catch(error => {console.error(error); process.exitCode = 1;});
