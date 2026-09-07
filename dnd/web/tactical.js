"use strict";

const el = (id) => document.getElementById(id);
let state = null;
let timer = null;
let displayedEvents = 0;
let busy = false;

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}

async function api(action, body) {
  const response = await fetch(`/api/tactico/${action}`, body === undefined ? {} : {
    method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "No se pudo completar la acción.");
  return data;
}

function fail(error) {
  clearTimeout(timer);
  el("error").textContent = error.message;
  el("error").hidden = false;
  el("reconnect").hidden = false;
}

function field(card, label, catalog, selected, callback) {
  const wrapper = node("label", label);
  const select = node("select");
  for (const [id, data] of Object.entries(catalog)) {
    const option = node("option", data.nombre);
    option.value = id;
    option.selected = id === selected;
    select.append(option);
  }
  select.addEventListener("change", () => callback(select.value));
  wrapper.append(select);
  card.append(wrapper);
  return select;
}

async function changeSelection(index, key, value) {
  const next = state.selecciones.map((s) => ({...s}));
  if (key === "personaje_id") {
    const other = next.findIndex((s) => s.personaje_id === value);
    [next[index], next[other]] = [next[other], next[index]];
  } else next[index][key] = value;
  await mutate("preparar", {selecciones: next});
}

function renderPreparation() {
  const catalog = state.catalogo;
  el("party").replaceChildren();
  state.selecciones.forEach((selection, index) => {
    const hero = state.party[index];
    const data = catalog.personajes[selection.personaje_id];
    const card = node("article", undefined, "hero");
    card.append(node("p", `PLAZA ${index + 1} · ${hero.rol.toUpperCase()}`, "eyebrow"));
    field(card, "Personaje", catalog.personajes, selection.personaje_id, (value) => changeSelection(index, "personaje_id", value));
    card.append(node("p", data.descripcion, "unique"));
    const stats = node("div", undefined, "stats");
    for (const [label, value] of [["Vida", hero.hp_max], ["Ataque", hero.ataque], ["Defensa", hero.defensa], ["Velocidad", hero.velocidad]]) {
      const stat = node("span", `${label} `);
      stat.append(node("strong", value));
      stats.append(stat);
    }
    card.append(stats);
    for (const [key, label, choices] of [["build", "Build", catalog.builds], ["arma", "Arma", catalog.armas], ["prioridad", "Prioridad de IA", catalog.prioridades]]) {
      field(card, label, choices, selection[key], (value) => changeSelection(index, key, value));
      card.append(node("p", choices[selection[key]].descripcion, "description"));
    }
    card.append(node("p", `Resistencia final al sangrado: ${hero.resistencia_sangrado}%`, "muted"));
    el("party").append(card);
  });
}

function renderHealth() {
  const combat = state.combate;
  el("round").textContent = `Ronda ${combat.ronda} · Intento ${state.intentos}`;
  el("health").replaceChildren();
  for (const actor of [...combat.party, combat.jefe]) {
    const boss = actor.id === combat.jefe.id;
    const card = node("article", undefined, `health-card${boss ? " boss" : ""}${actor.hp <= 0 ? " dead" : ""}`);
    card.append(node("h3", actor.nombre));
    card.append(node("p", `${actor.hp.toFixed(1)} / ${actor.hp_max} HP${actor.hp <= 0 ? " · Caído" : ""}`));
    const hp = node("progress");
    hp.max = actor.hp_max;
    hp.value = actor.hp;
    hp.setAttribute("aria-label", `Vida de ${actor.nombre}`);
    card.append(hp);
    const effects = Object.entries(actor.estados).map(([tag, effect]) => tag === "sangrado" ? `Sangrado ×${effect.cargas}` : tag === "vulnerable" ? "Aturdido / vulnerable" : "Muralla");
    card.append(node("p", effects.join(" · ") || "Sin estados", "effects"));
    if (boss) {
      const shield = node("progress", undefined, "shield");
      shield.max = actor.escudo_max;
      shield.value = actor.escudo;
      shield.setAttribute("aria-label", "Escudo del jefe");
      card.append(node("p", `Escudo ${actor.escudo.toFixed(1)} / ${actor.escudo_max}`), shield);
      if (actor.escudo_vence !== null) card.append(node("p", `Romper antes del final de ronda ${actor.escudo_vence}.`, "muted"));
    }
    el("health").append(card);
  }
}

const abilities = {ataque: "Ataque básico", limpiar: "Limpiar sangrado", curar: "Curar", romper: "Romper escudo", golpe_preciso: "Golpe preciso", golpe_demoledor: "Golpe demoledor", muralla: "Muralla", corte_sangriento: "Corte sangriento"};
function eventText(event) {
  const names = {...Object.fromEntries(Object.entries(state.catalogo.personajes).map(([id, data]) => [id, data.nombre])), [state.encuentro.id]: "Guardián"};
  const actor = names[event.actor_id] || "";
  const target = names[event.objetivo_id] || "";
  const amount = event.cantidad === null ? "" : Number(event.cantidad).toFixed(1);
  const tag = {fisico: "daño directo", sangrado: "sangrado", escudo_no_roto: "castigo de escudo"}[event.fuente_tag] || event.fuente_tag;
  switch (event.tipo) {
    case "iniciativa": return `Orden: ${event.metadata.orden.map((id) => names[id]).join(" → ")}`;
    case "accion": return `${actor}: ${abilities[event.metadata.habilidad] || event.metadata.habilidad}${event.metadata.regla ? ` [${event.metadata.regla}]` : ""}`;
    case "dano_recibido": case "dano_infligido": return `${target} pierde ${amount} HP por ${tag}.`;
    case "estado_aplicado": return `${target}: ${event.fuente_tag}${event.metadata.cargas ? ` ×${event.metadata.cargas}` : ""}.`;
    case "tick_sangrado": return `${target}: tick de sangrado (${event.metadata.cargas} cargas).`;
    case "estado_limpiado": return `${actor} limpia el sangrado de ${target}.`;
    case "estado_expirado": return `${target}: termina ${event.fuente_tag}.`;
    case "curacion": return `${actor} cura ${amount} HP a ${target}.`;
    case "escudo_activado": return `El jefe activa ${amount} de escudo. Plazo: final de ronda ${event.metadata.vence_ronda}.`;
    case "dano_escudo": return `${actor} reduce el escudo en ${amount}. Quedan ${event.metadata.escudo_restante}.`;
    case "escudo_roto": return `${actor} rompe el escudo. El jefe queda aturdido y vulnerable.`;
    case "escudo_no_roto": return `Falló la ruptura. Quedaban ${event.metadata.escudo_restante} de escudo.`;
    case "castigo_escudo": return "¡Ataque de castigo contra toda la party!";
    case "turno_omitido": return "El jefe pierde su acción por la ruptura del escudo.";
    case "muerte": return `${target} cae por ${tag}.`;
    case "critico": return `${actor} consigue un golpe crítico.`;
    case "victoria": return "Victoria: el Guardián ha caído.";
    case "derrota": return event.metadata.motivo === "limite_seguridad" ? "Fin por límite de seguridad." : "Derrota: ha caído toda la party.";
    default: return event.tipo;
  }
}

function renderLog() {
  if (displayedEvents > state.eventos.length) {
    el("log").replaceChildren();
    displayedEvents = 0;
  }
  const log = el("log");
  const nearBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 70;
  for (const event of state.eventos.slice(displayedEvents)) {
    const important = ["escudo_roto", "escudo_no_roto", "castigo_escudo", "muerte", "victoria", "derrota"].includes(event.tipo);
    log.append(node("p", `R${event.turno} · ${eventText(event)}`, important ? "important" : ""));
  }
  displayedEvents = state.eventos.length;
  if (nearBottom) log.scrollTop = log.scrollHeight;
}

function renderResult() {
  const result = state.resultado;
  el("resultTitle").textContent = result.resultado === "victoria" ? "El Guardián ha caído." : "Una derrota que puedes explicar.";
  el("resultStats").textContent = `${result.rondas} rondas · ${result.supervivientes.length}/3 supervivientes · Semilla ${result.seed}`;
  const diagnosis = el("diagnostic");
  diagnosis.replaceChildren();
  if (result.diagnostico) {
    const d = result.diagnostico;
    const title = result.motivo === "limite_seguridad" ? "Límite de seguridad"
      : d.causa === "desgaste_general" ? `Desgaste general · mayor fuente: ${d.contribucion_pct}%`
      : `${d.causa.replaceAll("_", " ")} · ${d.contribucion_pct}% del daño`;
    diagnosis.append(node("p", title, "cause"), node("p", d.mensaje), node("p", d.sugerencia));
    const sources = node("ul");
    for (const [tag, amount] of Object.entries(d.contribuciones)) sources.append(node("li", `${tag.replaceAll("_", " ")}: ${amount} HP`));
    diagnosis.append(sources, node("p", d.metodo, "muted"));
  } else diagnosis.append(node("p", "Tu grupo completó el encuentro. Puedes probar otra preparación con la misma semilla y comparar el registro."));
}

function render() {
  el("preparation").hidden = state.fase !== "preparacion";
  el("battle").hidden = !state.combate;
  el("result").hidden = state.fase !== "resultado";
  el("logSection").hidden = !state.combate;
  el("attempts").textContent = `Intentos: ${state.intentos}`;
  el("bossStats").textContent = `${state.encuentro.hp} HP · ${state.encuentro.escudo} escudo · Velocidad ${state.encuentro.velocidad}`;
  for (const [id, phase] of [["stepPrep", "preparacion"], ["stepFight", "combate"], ["stepResult", "resultado"]]) el(id).classList.toggle("active", state.fase === phase);
  if (state.fase === "preparacion") renderPreparation();
  if (state.combate) { renderHealth(); renderLog(); }
  if (state.resultado) renderResult();
}

function schedule() {
  clearTimeout(timer);
  if (state.fase === "combate") timer = setTimeout(() => mutate("avanzar", {}), Number(el("speed").value));
}

async function mutate(action, body) {
  if (busy) return;
  busy = true;
  el("prepFields").disabled = true;
  el("start").disabled = true;
  el("adjust").disabled = true;
  el("error").hidden = true;
  el("reconnect").hidden = true;
  try {
    state = await api(action, body);
    if (["iniciar", "reajustar"].includes(action)) { displayedEvents = 0; el("log").replaceChildren(); }
    render();
    schedule();
    if (state.fase === "resultado") el("result").focus({preventScroll: true});
  } catch (error) { fail(error); }
  finally {
    busy = false;
    el("prepFields").disabled = false;
    el("start").disabled = false;
    el("adjust").disabled = false;
  }
}

el("start").addEventListener("click", () => {
  if (!el("seed").value || !el("seed").reportValidity()) return;
  mutate("iniciar", {seed: Number(el("seed").value)});
});
el("adjust").addEventListener("click", () => mutate("reajustar", {}));
el("speed").addEventListener("change", schedule);
el("download").addEventListener("click", () => {
  const blob = new Blob([JSON.stringify({selecciones: state.selecciones, resultado: state.resultado, eventos: state.eventos}, null, 2)], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const link = node("a");
  link.href = url;
  link.download = `dungeon-intento-${state.intentos}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
async function load() {
  try { state = await api("estado"); el("error").hidden = true; el("reconnect").hidden = true; displayedEvents = 0; el("log").replaceChildren(); render(); schedule(); }
  catch (error) { fail(error); }
}
el("reconnect").addEventListener("click", load);
load();
