// Executes the page scripts against their real HTML IDs and backend fixtures.
// This checks DOM wiring and request/render behavior, not browser layout.
"use strict";
const fs = require("node:fs"), vm = require("node:vm"), assert = require("node:assert/strict");
const fixture = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
class Element {
  constructor(tag) {
    this.tag = tag; this.children = []; this.dataset = {}; this.attributes = {};
    this._value = ""; this._text = ""; this.hidden = false;
    const classes = new Set();
    this.classList = {add: c => classes.add(c), remove: c => classes.delete(c), contains: c => classes.has(c),
      toggle: (c, active) => active ? classes.add(c) : classes.delete(c)};
    this.style = {setProperty() {}};
  }
  set textContent(text) {this._text = String(text); this.children = [];}
  get textContent() {return this._text + this.children.map(c => c.textContent).join(" ");}
  set value(value) {this._value = String(value);}
  get value() {return this._value || (this.tag === "select" ? this.children[0]?.value || "" : "");}
  get options() {return this.children;}
  append(...nodes) {this.children.push(...nodes);}
  replaceChildren(...nodes) {this.children = nodes; this._text = ""; if (this.tag === "select") this._value = "";}
  setAttribute(key, value) {this.attributes[key] = value;}
  getAttribute(key) {return this.attributes[key];}
  contains(node) {return this.children.includes(node);}
  querySelector(tag) {for (const node of this.children) {if (node.tag === tag) return node; const child = node.querySelector(tag); if (child) return child;} return null;}
  focus() {}
  addEventListener(event, callback) {this[`on${event}`] = callback;}
  reportValidity() {return true;}
  getBoundingClientRect() {return {left: 20, top: 20, bottom: 40};}
}
async function page(name, data, script) {
  const html = fs.readFileSync(`web/${name}.html`, "utf8"), elements = new Map();
  for (const match of html.matchAll(/<(\w+)\b[^>]*\bid="([^"]+)"[^>]*>/g)) {
    assert(!elements.has(match[2]), `Duplicate ID: ${match[2]}`);
    const element = new Element(match[1]); element.hidden = /\bhidden\b/.test(match[0]); elements.set(match[2], element);
  }
  if (elements.has("sort")) elements.get("sort").value = "nombre";
  const document = {body: {dataset: {page: name}}, getElementById: id => elements.get(id) || null,
    createElement: tag => new Element(tag), addEventListener() {}};
  const requests = [];
  const context = vm.createContext({document, window: {addEventListener() {}, innerWidth: 1280, innerHeight: 800,
      location: {search: `?ui=${fixture.main.ui_version}`, href: `http://localhost/?ui=${fixture.main.ui_version}`,
        replace() {throw Error("Unexpected version redirect");}}},
    AbortController, URL, URLSearchParams, console, setTimeout, clearTimeout, structuredClone,
    fetch: async (url, options = {}) => {
      requests.push({url, body: options.body ? JSON.parse(options.body) : null});
      const query = new URL(url, "http://localhost").searchParams;
      const result = url.includes("previsualizar") ? fixture.previews[query.get("tipo")] : data;
      assert(result, `Missing response for ${url}`);
      return {ok: true, json: async () => structuredClone(result)};
    }});
  if (script === "tactical") {
    vm.runInContext(fs.readFileSync("web/tactical-board.js", "utf8"), context);
    vm.runInContext("autoCombat = false", context);
  }
  vm.runInContext(fs.readFileSync(`web/${script}.js`, "utf8"), context);
  await new Promise(setImmediate);
  const run = code => vm.runInContext(code, context);
  if (script !== "app") assert.equal(run("busy"), false);
  assert.equal(elements.get("error").textContent, "");
  return {elements, requests, run};
}
(async () => {
  const main = await page("index", fixture.main, "app");
  const index = fs.readFileSync("web/index.html", "utf8");
  assert(index.includes(`/app.js?v=${fixture.main.ui_version}`));
  assert.equal(main.run("estado.slots.length"), 3);
  assert.equal(main.elements.get("loadButton").disabled, false);
  assert.equal(main.elements.get("tacticalButton").disabled, false);
  main.elements.get("loadButton").onclick();
  assert.equal(main.elements.get("slotList").children.length, 3);
  assert.equal(main.elements.get("pauseOverlay").classList.contains("hidden"), false);
  main.elements.get("backPauseButton").onclick();
  assert.equal(main.elements.get("pauseOverlay").classList.contains("hidden"), true);
  main.run("estado = null");
  main.elements.get("loadButton").onclick();
  assert(main.elements.get("slotHelp").textContent.includes("No se pudo cargar"));
  main.elements.get("backPauseButton").onclick();
  assert.equal(main.elements.get("pauseOverlay").classList.contains("hidden"), true);
  const tactical = await page("tactical", fixture.tactical, "tactical");
  assert.equal(tactical.elements.get("party").children.length, 3);
  assert.equal(tactical.elements.get("start").disabled, false);
  assert.equal(tactical.elements.get("battleGrid").children.length, 80);
  assert.equal(tactical.elements.get("boardFields").disabled, false);
  assert(!tactical.elements.has("boardTool"));
  assert(!tactical.elements.has("clearTerrain"));
  await tactical.run('selectCell([0, 7], null)');
  const edit = tactical.requests.find(r => r.url === "/api/tactico/campo");
  assert.deepEqual(edit.body.tablero.posiciones[fixture.tactical.party[0].id], [0, 7]);
  assert.deepEqual(edit.body.tablero.celdas, fixture.tactical.tablero.celdas);
  const six = await page("tactical", fixture.tacticalSix, "tactical");
  assert.equal(six.elements.get("party").children.length, 6);
  assert.equal(six.elements.get("addHero").disabled, true);
  assert.equal(six.elements.get("boardUnit").options.length, 6);
  const fight = await page("tactical", fixture.tacticalFrame, "tactical");
  assert.equal(fight.elements.get("boardFields").disabled, true);
  assert.equal(fight.elements.get("nextRound").disabled, false);
  fight.elements.get("speed").value = "1";
  await fight.run("state.reproduccion = state.reproduccion.slice(0, 2); animateBoard()");
  assert.equal(fight.run("playing"), false);
  assert.equal(fight.run("playback"), null);
  fight.run('state.combate.party[0].hp = 0; state.tablero.posiciones[state.combate.party[0].id] = state.tablero.posiciones[state.combate.party[1].id]; renderBoard()');
  const living = fixture.tacticalFrame.combate.party[1];
  const pos = fixture.tacticalFrame.tablero.posiciones[living.id];
  assert(fight.elements.get("battleGrid").children[pos[1] * 10 + pos[0]].getAttribute("aria-label").includes(living.nombre));

  const forge = await page("workshop", fixture.workshop, "workshop");
  assert(!forge.elements.has("vaultPanel"));
  assert(forge.elements.get("preview").textContent.includes("Vault: 3"));
  assert(forge.elements.get("preview").textContent.includes("75 oro"));
  forge.elements.get("component").value = "glandula_venenosa";
  forge.elements.get("type").value = "casco";
  forge.elements.get("type").onchange();
  await new Promise(setImmediate);
  assert.equal(forge.elements.get("component").value, "");
  assert.equal(forge.elements.get("component").disabled, true);
  assert(forge.elements.get("preview").textContent.includes("Defensa"));
  assert(!forge.elements.get("preview").textContent.includes("Daño mínimo posible"));
  await forge.run('act("fabricar", {tipo: "casco", material: "hierro", componente: null})');
  assert.equal(forge.requests.find(r => r.body)?.body.personaje_id, fixture.workshop.personaje_id);
  assert(!forge.requests.some(r => r.body && "precio" in r.body));
  forge.run('state.disponible = false; updateControls()');
  assert.equal(forge.elements.get("craft").disabled, true);

  const vault = await page("vault", fixture.workshop, "workshop");
  assert(!vault.elements.has("craftFields"));
  assert.equal(vault.requests.some(r => r.url.includes("previsualizar")), false);
  assert(vault.elements.get("vault").children.length);
  await vault.run('act("depositar_materiales")');
  assert(vault.requests.some(r => r.url === "/api/taller/depositar_materiales"));

  const shop = await page("shop", fixture.shop, "shop");
  assert.equal(shop.elements.get("sellPanel").hidden, true);
  shop.elements.get("sellMode").onclick();
  assert.equal(shop.elements.get("buyPanel").hidden, true);
  assert.equal(shop.elements.get("sellPanel").hidden, false);
  assert(shop.elements.get("inventory").textContent.includes("Recibirás:"));
  await shop.run('sell(state.ventas.find(i => i.vendible), 1)');
  assert(shop.requests.some(r => r.url === "/api/tienda/vender" && r.body.instance_id));
  assert(!shop.requests.some(r => r.body && "precio" in r.body));

  for (const name of ["workshop", "vault"]) {
    const empty = await page(name, fixture.empty, "workshop");
    assert(empty.elements.get("message").textContent.includes("Crea un personaje"));
  }
  console.log("Page scripts OK: menus, forge, vault, shop, six-unit deployment, fixed maps and combat playback.");
})().catch(error => {console.error(error); process.exitCode = 1;});
