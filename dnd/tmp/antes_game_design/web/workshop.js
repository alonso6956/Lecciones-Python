"use strict";
const el = id => document.getElementById(id);
const node = (tag, text) => { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; return n; };
const roman = tier => ["", "I", "II", "III", "IV", "V"][tier] || tier;
const range = (values, scale = 1, digits = 1) => [...new Set(values.map(v => Number((v * scale).toFixed(digits))))].join("–");
let state = null, busy = false, crafted = null, preview = null, previewVersion = 0, previewRequest = null;
let popupAnchor = null, popupTimer = null, dragged = null, restoringFocus = false;
const canAct = () => !busy && Boolean(state?.disponible && state.personaje_id);
const isVault = document.body.dataset.page === "vault";
function options(id, entries, empty) {
  const select = el(id), previous = select.value;
  select.replaceChildren();
  if (empty) { const option = node("option", empty); option.value = ""; select.append(option); }
  for (const [key, data] of Object.entries(entries)) { const option = node("option", data.nombre); option.value = key; select.append(option); }
  if ([...select.options].some(o => o.value === previous)) select.value = previous;
}
function errorMessage(error) { el("error").textContent = error.message; el("error").hidden = false; }
function updateControls() {
  el("character").disabled = busy; el("refresh").disabled = busy;
  if (!isVault) {
    el("craftFields").disabled = !canAct();
    el("craft").disabled = !canAct() || !preview?.puede_fabricar;
    el("component").disabled = state?.catalogo.tipos[el("type").value]?.categoria !== "arma";
  }
  const transferable = (state?.inventario || []).filter(i => i.transferible);
  if (isVault) {
    el("depositAll").disabled = !canAct() || !transferable.length;
    el("depositMaterials").disabled = !canAct() || !transferable.some(i => i.categoria === "material");
  }
}
async function load() {
  if (busy) return;
  busy = true; closePopup(); cancelPreview(); updateControls();
  try {
    const get = async selected => {
      const response = await fetch(`/api/taller/estado${selected ? `?personaje_id=${encodeURIComponent(selected)}` : ""}`);
      const data = await response.json(); if (!response.ok) throw Error(data.error); return data;
    };
    let data = await get(el("character").value);
    if (!data.personaje_id && data.personajes.length) data = await get(data.personajes[0].id);
    state = data;
    options("character", Object.fromEntries(data.personajes.map(p => [p.id, p])));
    el("character").value = data.personaje_id || ""; el("error").hidden = true;
  } catch (error) { if (state) state.disponible = false; errorMessage(error); }
  finally { busy = false; render(); updateControls(); }
}
async function act(action, data = {}) {
  if (!canAct()) return;
  busy = true; closePopup(); cancelPreview(); updateControls();
  try {
    const response = await fetch(`/api/taller/${action}`, {method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({personaje_id: state.personaje_id, ...data})});
    const result = await response.json();
    if (!response.ok) throw Error(result.error || "No se pudo completar la operación.");
    state = {...result, disponible: true};
    if (result.objeto_creado) crafted = result.objeto_creado;
    if (action === "nombrar" || (crafted && !state.inventario.some(i => i.item_id === crafted.id))) crafted = null;
    el("error").hidden = true;
    el("message").textContent = result.transferidos ? `${result.transferidos} unidades depositadas y guardadas.` : "Operación completada y guardada.";
  } catch (error) { errorMessage(error); }
  finally { busy = false; render(); }
}
function icon(item) {
  const data = item.detalles || item.custom_data || item, id = item.item_id || "";
  const icons = {espada: "⚔️", maza: "🔨", daga: "🗡️", dagas: "🗡️", lanza: "🔱", arma: "⚔️", armadura: "🛡️", secundario: "🛡️", consumible: "🧪", material: "💠", casco: "🪖", pecho: "🥋", brazos: "🧤", piernas: "👖",
    glandula_venenosa: "🧪", colmillo_bestia: "🦷", corazon_salamandra: "🔥", fragmento_runico: "🔮", nucleo_cristalino: "💎"};
  const metal = id.startsWith("material_");
  const n = node("span", metal ? "⬟" : icons[id] || icons[data.tipo_arma] || icons[data.slot] || icons[item.categoria] || "📦");
  n.className = `item-icon${metal ? " metal" : ""}`; n.setAttribute("aria-hidden", "true"); return n;
}
function stats(data) {
  const list = node("dl"); list.className = "stat-list";
  const add = (title, value) => list.append(node("dt", title), node("dd", value));
  if (data.tier) add("Calidad", `Tier ${roman(data.tier)}`);
  if (data.precio !== undefined) { add("Valor de mercado", `${data.precio} oro`); add("Venta", `${Math.floor(data.precio / 2)} oro`); }
  if (data.ataque) add("Daño del arma", data.ataque.join("–"));
  if (data.defensa !== undefined) add("Defensa", data.defensa);
  if (data.velocidad !== undefined) add("Velocidad", `×${data.velocidad}`);
  if (data.critico !== undefined) add("Crítico", `${(data.critico * 100).toFixed(1)}%`);
  if (data.penetracion !== undefined) add("Penetración", Number(data.penetracion.toFixed(1)));
  for (const [key, label] of [["durabilidad", "Durabilidad"], ["peso", "Peso"], ["alcance", "Alcance"]]) if (data[key] !== undefined) add(label, data[key]);
  if (data.probabilidad_bloqueo !== undefined) add("Bloqueo", `${Math.round(data.probabilidad_bloqueo * 100)}%`);
  if (data.porcentaje_dano_bloqueado !== undefined) add("Daño bloqueado", `${Math.round(data.porcentaje_dano_bloqueado * 100)}%`);
  if (data.efecto) add(data.efecto, data.valor);
  if (data.bonus_sobrenatural) add("Daño a sobrenaturales", `+${Math.round(data.bonus_sobrenatural * 100)}%`);
  if (data.requisitos) add("Requisitos", Object.entries(data.requisitos).map(([k, v]) => `${k} ${v}`).join(", ") || "Ninguno");
  for (const [k, v] of Object.entries(data.bonificaciones || {})) add(k, v);
  return list;
}
function effectText(afijo) {
  return afijo?.id ? `${afijo.id}: ${Math.round(afijo.probabilidad * 100)}% de activar ${afijo.dano} de daño durante ${afijo.turnos} turno(s).` : "Sin afijo.";
}
function cancelPreview() { previewVersion++; previewRequest?.abort(); preview = null; }
async function updatePreview() {
  cancelPreview(); updateControls();
  const target = el("preview");
  target.replaceChildren(node("p", state?.personaje_id ? "Calculando resultado…" : "Elige el personaje que recibirá el objeto."));
  if (!state?.personaje_id) return;
  const version = previewVersion; previewRequest = new AbortController();
  const params = new URLSearchParams({personaje_id: state.personaje_id, tipo: el("type").value, material: el("material").value});
  if (el("component").value) params.set("componente", el("component").value);
  try {
    const response = await fetch(`/api/taller/previsualizar?${params}`, {signal: previewRequest.signal});
    const data = await response.json();
    if (version !== previewVersion) return;
    if (!response.ok) throw Error(data.error);
    preview = data; renderPreview(); updateControls();
  } catch (error) {
    if (version !== previewVersion || error.name === "AbortError") return;
    target.replaceChildren(node("p", `No se pudo calcular: ${error.message}`));
  }
}
function renderPreview() {
  const p = preview, target = el("preview"); target.replaceChildren();
  const heading = node("div"); heading.className = "preview-heading";
  heading.append(icon(p), node("h3", `${p.nombre}${p.afijo.id ? ` · ${p.afijo.id}` : ""}`));
  const list = stats({tier: p.tier, alcance: p.alcance, requisitos: p.requisitos});
  const add = (k, v) => list.append(node("dt", k), node("dd", v));
  if (p.ataque) { add("Daño mínimo posible", range(p.ataque.minimo)); add("Daño máximo posible", range(p.ataque.maximo)); }
  for (const [key, label, scale, suffix] of [["velocidad", "Velocidad", 1, "×"], ["critico", "Crítico", 100, "%"], ["penetracion", "Penetración", 1, ""], ["defensa", "Defensa", 1, ""], ["probabilidad_bloqueo", "Bloqueo", 100, "%"], ["porcentaje_dano_bloqueado", "Daño bloqueado", 100, "%"], ["peso", "Peso", 1, ""], ["durabilidad", "Durabilidad", 1, ""]]) {
    if (p.rangos[key]) add(label, `${range(p.rangos[key], scale)}${suffix}`);
  }
  add("Fabricación", `${p.coste_oro} oro + materiales`);
  add("Valor de mercado", `${p.valor_mercado} oro`); add("Venta", `${p.precio_venta} oro`);
  const hint = node("p", "El perfil aleatorio determina los valores finales. El coste en oro de fabricación siempre supera el valor de mercado y lo que recuperas al vender."); hint.className = "hint";
  const resources = node("ul"); resources.className = "resource-list";
  for (const r of p.recursos) {
    const enough = r.disponible >= r.necesario;
    const row = node("li", `${enough ? "✓" : "✕"} ${r.nombre}: ${r.disponible}/${r.necesario} · Inventario: ${r.inventario} · Vault: ${r.vault}${enough ? "" : " · insuficiente"}`);
    row.className = enough ? "enough" : "missing"; resources.append(row);
  }
  target.append(heading, list, node("p", effectText(p.afijo)), hint, resources);
  if (!p.espacio_disponible) target.append(node("p", "No hay espacio para el objeto en este inventario."));
  if (p.oro_disponible < p.coste_oro) target.append(node("p", `Oro insuficiente: tienes ${p.oro_disponible} y necesitas ${p.coste_oro}.`));
}
function closePopup(returnFocus = false) {
  clearTimeout(popupTimer);
  const anchor = popupAnchor; popupAnchor = null;
  el("itemPopup").hidden = true; anchor?.setAttribute("aria-expanded", "false");
  if (returnFocus && anchor?.isConnected) {
    restoringFocus = true; anchor.focus(); restoringFocus = false;
  }
}
function scheduleClose() {
  clearTimeout(popupTimer);
  popupTimer = setTimeout(() => {
    if (!el("itemPopup").contains(document.activeElement) && document.activeElement !== popupAnchor) closePopup();
  }, 180);
}
function transfer(item, deposit, cantidad) {
  if (!isVault || !canAct() || !item.transferible) return;
  return act(deposit ? "depositar" : "retirar", {instance_id: item.instance_id, cantidad});
}
function showPopup(item, deposit, anchor) {
  if (busy || dragged || restoringFocus) return;
  clearTimeout(popupTimer);
  if (popupAnchor === anchor && !el("itemPopup").hidden) return;
  closePopup(); popupAnchor = anchor;
  const popup = el("itemPopup"); popup.replaceChildren(); popup.hidden = false;
  anchor.setAttribute("aria-expanded", "true");
  const title = node("h3", item.nombre); title.id = "popupTitle";
  const close = node("button", "×"); close.className = "popup-close secondary"; close.setAttribute("aria-label", "Cerrar detalles"); close.onclick = () => closePopup(true);
  const data = item.detalles || item.custom_data || {};
  popup.append(title, close, node("small", `${item.categoria} · Cantidad: ${item.cantidad}${item.equipado ? " · Equipado" : ""}`), stats(data));
  if (data.descripcion) popup.append(node("p", data.descripcion));
  if (data.afijo?.id) popup.append(node("p", effectText(data.afijo)));
  const actions = node("div"); actions.className = "popup-actions";
  const label = node("label", "Cantidad"), quantity = node("input"); quantity.type = "number"; quantity.min = "1"; quantity.max = String(item.cantidad); quantity.step = "1"; quantity.value = "1"; quantity.required = true;
  label.append(quantity);
  const move = node("button", deposit ? "Depositar" : "Retirar"); move.disabled = !canAct() || !item.transferible;
  move.onclick = () => { if (quantity.reportValidity()) transfer(item, deposit, Number(quantity.value)); };
  if (isVault) actions.append(label, move);
  if (deposit && ["arma", "armadura", "secundario"].includes(item.categoria)) {
    const equip = node("button", item.equipado ? "Desequipar" : "Equipar"); equip.className = "secondary";
    equip.disabled = !canAct() || (item.equipado && item.categoria === "arma");
    equip.onclick = () => act(item.equipado ? "desequipar" : "equipar", item.equipado ? {slot: item.slot} : {item_id: item.item_id});
    actions.append(equip);
  }
  if (deposit && item.custom_data) {
    const rename = node("button", "Nombrar"); rename.className = "secondary"; rename.disabled = !canAct();
    rename.onclick = () => { crafted = item.custom_data; closePopup(); renderResult(); el("weaponName").focus(); }; actions.append(rename);
  }
  popup.append(actions);
  if (isVault && !item.transferible) popup.append(node("p", item.equipado ? (item.categoria === "arma" ? "Equipa otra arma antes de depositar esta." : "Desequipa este objeto para depositarlo.") : "Este objeto está vinculado o no admite transferencias."));
  const rect = anchor.getBoundingClientRect();
  popup.style.left = `${Math.max(10, Math.min(rect.left, window.innerWidth - popup.offsetWidth - 10))}px`;
  const below = rect.bottom + 6;
  popup.style.top = `${Math.max(10, Math.min(below + popup.offsetHeight <= window.innerHeight ? below : rect.top - popup.offsetHeight - 6, window.innerHeight - popup.offsetHeight - 10))}px`;
}
function renderItems(id, items, deposit) {
  const target = el(id); target.replaceChildren();
  const query = el("search").value.toLocaleLowerCase(), category = el("category").value, sort = el("sort").value;
  const filtered = items.filter(i => i.nombre.toLocaleLowerCase().includes(query) && (!category || category === i.categoria));
  filtered.sort((a, b) => sort === "cantidad" ? b.cantidad - a.cantidad : String(a[sort]).localeCompare(String(b[sort]), "es"));
  for (const item of filtered) {
    const slot = node("button"); slot.type = "button";
    slot.className = `item-slot${item.custom_data ? " crafted" : ""}${item.equipado ? " equipped" : ""}`;
    slot.setAttribute("aria-label", `${item.nombre}, cantidad ${item.cantidad}${item.equipado ? ", equipado" : ""}`);
    slot.setAttribute("aria-haspopup", "dialog"); slot.setAttribute("aria-controls", "itemPopup"); slot.setAttribute("aria-expanded", "false");
    slot.append(icon(item));
    const count = node("span", item.cantidad); count.className = "item-count"; count.setAttribute("aria-hidden", "true"); slot.append(count);
    const metals = {hierro: ["Fe", "#aeb8c9"], acero: ["Ac", "#d0e4e8"], bronce: ["Br", "#d49753"], plata: ["Ag", "#f1f2ff"], obsidiana: ["Ob", "#b895db"]};
    const metal = metals[item.item_id.replace("material_", "")];
    if (metal) { slot.style.setProperty("--item-tint", metal[1]); const mark = node("span", metal[0]); mark.className = "material-mark"; mark.setAttribute("aria-hidden", "true"); slot.append(mark); }
    if (item.equipado) { const badge = node("span", "E"); badge.className = "equipped-badge"; badge.setAttribute("aria-hidden", "true"); slot.append(badge); }
    slot.onmouseenter = () => showPopup(item, deposit, slot); slot.onmouseleave = scheduleClose;
    slot.onfocus = () => showPopup(item, deposit, slot); slot.onblur = scheduleClose;
    slot.onclick = event => {
      if (event.shiftKey) { transfer(item, deposit, item.cantidad); return; }
      showPopup(item, deposit, slot);
      if (!el("itemPopup").hidden) el("itemPopup").querySelector(isVault ? "input" : "button")?.focus();
    };
    slot.oncontextmenu = event => { event.preventDefault(); transfer(item, deposit, 1); };
    slot.draggable = isVault && canAct() && item.transferible;
    slot.ondragstart = event => {
      if (!canAct() || !item.transferible) { event.preventDefault(); return; }
      closePopup(); dragged = {item, deposit, personaje: state.personaje_id};
      event.dataTransfer.effectAllowed = "move"; event.dataTransfer.setData("text/plain", item.instance_id); slot.classList.add("dragging");
    };
    slot.ondragend = () => { dragged = null; slot.classList.remove("dragging"); clearDropTargets(); };
    target.append(slot);
  }
  if (!filtered.length) { const empty = node("p", items.length ? "Ningún objeto coincide con los filtros." : "No hay objetos aquí."); empty.className = "empty-message"; target.append(empty); }
  // Relleno visual: la capacidad real se indica en la cabecera.
  for (let i = filtered.length; i < 12; i++) { const empty = node("div"); empty.className = "item-slot empty"; empty.setAttribute("aria-hidden", "true"); target.append(empty); }
}
function clearDropTargets() { for (const id of ["inventoryPanel", "vaultPanel"]) el(id)?.classList.remove("drop-target"); }
function renderStorage() {
  closePopup(); if (!state) return;
  renderItems("inventory", state.inventario, true);
  if (isVault) renderItems("vault", state.vault.items, false);
}
function renderResult() {
  const target = el("result"); target.replaceChildren(); if (!crafted) return;
  target.append(node("h3", crafted.nombre), stats(crafted), node("p", effectText(crafted.afijo)));
  const label = node("label", "Nombre del objeto"), name = node("input"); name.id = "weaponName"; name.maxLength = 60; name.required = true; name.value = crafted.nombre; label.append(name);
  const save = node("button", "Guardar nombre"); save.disabled = !canAct();
  save.onclick = () => { if (name.reportValidity()) act("nombrar", {item_id: crafted.id, nombre: name.value}); }; target.append(label, save);
}
function render() {
  if (!state) return;
  if (!isVault) {
  options("type", state.catalogo.tipos); options("material", state.catalogo.materiales); options("component", state.catalogo.afijos, "Sin componente");
  const p = state.progreso;
  el("tierBadge").textContent = `Tier ${roman(p.tier)}`;
  el("progress").textContent = p.objetivo ? `${p.actual} / ${p.objetivo} fabricaciones para avanzar` : `${state.crafting_exp} fabricaciones · Maestría alcanzada`;
  el("progressPercent").textContent = `${p.porcentaje}%`; el("skillXP").value = p.porcentaje;
  el("nextTier").textContent = p.siguiente_tier ? `Siguiente: Tier ${roman(p.siguiente_tier)} · Equipo de mayor poder · Coste: ${p.siguiente_coste} materiales y oro según la pieza.` : "Tier V · Puedes fabricar el equipo de mayor poder del taller.";
  el("cost").textContent = `Coste: ${state.coste_material} materiales${el("component").value ? " y 1 componente" : ""}.`;
  el("gold").textContent = state.oro;
  }
  if (isVault) el("capacity").textContent = `${state.vault.ocupados} / ${state.vault.capacidad} espacios`;
  el("inventoryCount").textContent = `${state.inventario.length} espacios ocupados`;
  if (!state.disponible) el("message").textContent = "Vuelve al menú y termina los combates tácticos para usar el taller y vault.";
  else if (!state.personaje_id) el("message").textContent = "Crea un personaje en Dungeon para comenzar.";
  updateControls(); renderStorage(); renderResult(); if (!isVault) updatePreview();
}
el("character").onchange = () => { crafted = null; el("message").textContent = ""; load(); };
el("refresh").onclick = load;
for (const id of ["search", "category", "sort"]) el(id).oninput = renderStorage;
if (!isVault) {
for (const id of ["type", "material", "component"]) el(id).onchange = () => {
  if (state.catalogo.tipos[el("type").value]?.categoria !== "arma") el("component").value = "";
  el("cost").textContent = `Coste: ${state.coste_material} materiales${el("component").value ? " y 1 componente" : ""}.`; updatePreview();
};
el("craft").onclick = () => { if (preview?.puede_fabricar) act("fabricar", {tipo: el("type").value, material: el("material").value, componente: el("component").value || null}); };
}
if (isVault) {
el("depositMaterials").onclick = () => act("depositar_materiales");
el("depositAll").onclick = () => act("depositar_todo");
}
el("itemPopup").onmouseenter = () => clearTimeout(popupTimer); el("itemPopup").onmouseleave = scheduleClose; el("itemPopup").onfocusout = scheduleClose;
document.addEventListener("keydown", event => { if (event.key === "Escape") closePopup(true); });
document.addEventListener("pointerdown", event => { if (!el("itemPopup").contains(event.target) && !popupAnchor?.contains(event.target)) closePopup(); });
window.addEventListener("resize", () => closePopup());
window.addEventListener("scroll", event => { if (!el("itemPopup").contains(event.target)) closePopup(); }, true);
for (const [id, deposit] of (isVault ? [["vaultPanel", true], ["inventoryPanel", false]] : [])) {
  const panel = el(id), accepts = () => canAct() && dragged && dragged.deposit === deposit && dragged.personaje === state.personaje_id;
  panel.ondragover = event => { if (accepts()) { event.preventDefault(); event.dataTransfer.dropEffect = "move"; panel.classList.add("drop-target"); } };
  panel.ondragleave = event => { if (!panel.contains(event.relatedTarget)) panel.classList.remove("drop-target"); };
  panel.ondrop = event => { event.preventDefault(); clearDropTargets(); if (accepts()) transfer(dragged.item, deposit, dragged.item.cantidad); dragged = null; };
}
load();
