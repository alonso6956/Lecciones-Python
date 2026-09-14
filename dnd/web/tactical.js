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
    if (other >= 0) [next[index], next[other]] = [next[other], next[index]];
    else next[index] = {...next[index], personaje_id: value, arma: state.catalogo.personajes[value].arma_equipada};
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
    for (const [label, value] of statValues(hero)) {
      const stat = node("span", `${label} `);
      stat.append(node("strong", value));
      stats.append(stat);
    }
    const details = node("details"); details.append(node("summary", "Estadísticas del personaje"), stats); card.append(details);
    for (const [key, label, choices] of [["build", "Build", catalog.builds], ["arma", "Arma", catalog.armas], ["prioridad", "Prioridad de IA", catalog.prioridades]]) {
      const available = key === "arma" && data.armas ? Object.fromEntries(Object.entries(choices).filter(([id]) => data.armas.includes(id))) : choices;
      field(card, label, available, selection[key], (value) => changeSelection(index, key, value));
      card.append(node("p", choices[selection[key]].descripcion, "description"));
    }
    card.append(node("p", `Resistencia final al sangrado: ${hero.resistencia_sangrado}%`, "muted"));
    el("party").append(card);
  });
}

function statValues(actor) {
  const percent = (value) => `${Math.round(value * 100)}%`;
  const values = [["Vida máxima", actor.hp_max],
    ["Fuerza", actor.fuerza], ["Destreza", actor.destreza], ["Constitución", actor.constitucion],
    ["Daño", `${actor.ataque_minimo}–${actor.ataque_maximo}`],
    ["Armadura", actor.armadura], ["Mitigación", percent(actor.mitigacion_armadura)],
    ["Iniciativa", actor.iniciativa], ["Evasión", percent(actor.evasion)],
    ["Arma", actor.arma], ["Secundario", actor.secundario || "Ninguno"],
    ["Bloqueo", percent(actor.probabilidad_bloqueo)],
    ["Daño bloqueado", percent(actor.porcentaje_dano_bloqueado)]];
  if (actor.critico_arma !== undefined) values.push(
    ["Movimiento", actor.movimiento], ["Regeneración por turno", actor.regeneracion],
    ["Impacto", actor.impacto], ["Estabilidad", actor.estabilidad],
    ["Resistencia Física", actor.resistencia_fisica], ["Penetración total", Number(actor.penetracion.toFixed(1))],
    ["Crítico del arma", percent(actor.critico_arma)], ["Penetración", actor.penetracion_arma],
    ["Alcance", actor.alcance_arma], ["Durabilidad", actor.durabilidad_arma]);
  if (actor.energia_maxima !== undefined) values.push(
    ["Energía máxima", actor.energia_maxima],
    ["Peso / capacidad", `${actor.peso_equipado} / ${actor.capacidad_peso}`],
    ["Carga", actor.carga_categoria], ["Movimiento por carga", actor.modificador_movimiento_carga],
    ["Penalización de evasión", percent(actor.penalizacion_evasion_peso)]);
  return values;
}

function renderHealth() {
  const combat = state.combate;
  el("round").textContent = `Ronda ${combat.ronda} · Intento ${state.intentos}`;
  el("health").replaceChildren();
  for (const actor of [...combat.party, ...combat.enemigos.map(a => a.id === combat.jefe?.id ? combat.jefe : a)]) {
    const boss = actor.id === combat.jefe?.id;
    const enemy = combat.enemigos.some(a => a.id === actor.id);
    const card = node("article", undefined, `health-card${enemy ? " boss" : ""}${actor.hp <= 0 ? " dead" : ""}`);
    card.append(node("h3", actor.nombre));
    card.append(node("p", `${actor.hp.toFixed(1)} / ${actor.hp_max} HP${actor.hp <= 0 ? " · Caído" : ""}`));
    const hp = node("progress");
    hp.max = actor.hp_max;
    hp.value = actor.hp;
    hp.setAttribute("aria-label", `Vida de ${actor.nombre}`);
    card.append(hp);
    const stats = node("div", undefined, "stats");
    for (const [label, value] of statValues(actor)) stats.append(node("span", `${label}: ${value}`));
    card.append(stats);
    const effects = Object.entries(actor.estados).map(([tag, effect]) => tag === "sangrado" ? `Sangrado ×${effect.cargas}` : ({vulnerable: "Aturdido / vulnerable", inmovilizado: "Inmovilizado", muralla: "Muralla"}[tag] || tag));
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
  const names = {...Object.fromEntries(Object.entries(state.catalogo.personajes).map(([id, data]) => [id, data.nombre])), ...Object.fromEntries(state.encuentro.enemigos.map(a => [a.id, a.nombre]))};
  const actor = names[event.actor_id] || "";
  const target = names[event.objetivo_id] || "";
  const amount = event.cantidad === null ? "" : Number(event.cantidad).toFixed(1);
  const tag = {fisico: "daño directo", sangrado: "sangrado", escudo_no_roto: "castigo de escudo"}[event.fuente_tag] || event.fuente_tag;
  switch (event.tipo) {
    case "decision_ia": return `${actor}: ${event.metadata.motivo}${target ? ` → ${target}` : ""}.`;
    case "movimiento": return `${actor}: ${coordinate(event.metadata.origen)} → ${coordinate(event.metadata.destino)}.`;
    case "sin_alcance": return `${actor} no alcanza a ${target}${event.fuente_tag === "inmovilizado" ? " porque está inmovilizado" : " en esta acción"}.`;
    case "trampa_activada": return `${actor} pisa una trampa en ${coordinate(event.metadata.casilla)} y queda inmovilizado.`;
    case "campo_modificado": return `${actor}: ${state.catalogo.maniobras[event.fuente_tag]?.nombre || event.fuente_tag} en ${coordinate(event.metadata.casilla)}.`;
    case "ventaja_posicional": return `${actor} → ${target}: ${event.metadata.factores.join(", ")} (daño ×${event.metadata.multiplicador}).`;
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
    case "esquiva": return `${actor} esquiva el ataque de ${target}.`;
    case "bloqueo": return `${actor} bloquea parte del ataque de ${target}.`;
    case "victoria": return "Victoria: todos los enemigos han caído.";
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
  el("resultTitle").textContent = result.resultado === "victoria" ? "Todos los enemigos han caído." : "Una derrota que puedes explicar.";
  el("resultStats").textContent = `${result.rondas} rondas · ${result.supervivientes.length}/${state.selecciones.length} supervivientes · Semilla ${result.seed}`;
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
  el("addHero").disabled = busy || state.fase !== "preparacion" || !state.tactico_disponible || state.selecciones.length >= Math.min(6, Object.keys(state.catalogo.personajes).length);
  el("removeHero").disabled = busy || state.fase !== "preparacion" || state.selecciones.length <= 3;
  el("partyCount").textContent = `${state.selecciones.length} / 6 personajes`;
  renderBoard();
  el("start").disabled = state.tactico_disponible === false;
  el("prepFields").disabled = state.tactico_disponible === false;
  el("lockMessage").textContent = state.mensaje_bloqueo || "";
  el("preparation").hidden = state.fase !== "preparacion";
  el("battle").hidden = !state.combate;
  el("result").hidden = state.fase !== "resultado";
  el("logSection").hidden = !state.combate;
  el("attempts").textContent = `Intentos: ${state.intentos}`;
  el("bossTitle").textContent = state.encuentro.nombre;
  el("bossStats").textContent = state.encuentro.enemigos.map(a => `${a.nombre} · ${a.hp_max} vida · ${a.ataque} ataque`).join(" / ");
  el("encounterRules").textContent = state.catalogo.escenarios[state.escenario_id].descripcion;
  for (const [id, phase] of [["stepPrep", "preparacion"], ["stepFight", "combate"], ["stepResult", "resultado"]]) el(id).classList.toggle("active", state.fase === phase);
  if (state.fase === "preparacion") renderPreparation();
  if (state.combate) { renderHealth(); renderLog(); }
  if (state.resultado) renderResult();
}

function schedule() {
  clearTimeout(timer);
  if (state.fase === "combate" && autoCombat && !playing) timer = setTimeout(() => mutate("avanzar", {}), Number(el("speed").value));
}

async function mutate(action, body) {
  if (busy) return;
  busy = true;
  clearTimeout(timer);
  renderBoard();
  el("prepFields").disabled = true;
  el("start").disabled = true;
  el("adjust").disabled = true;
  el("error").hidden = true;
  el("reconnect").hidden = true;
  try {
    state = await api(action, body);
    if (action === "iniciar") autoCombat = true;
    if (["iniciar", "reajustar"].includes(action)) { displayedEvents = 0; el("log").replaceChildren(); }
    if (action === "avanzar") await animateBoard();
    render();
    schedule();
    if (state.fase === "resultado") el("result").focus({preventScroll: true});
  } catch (error) { fail(error); }
  finally {
    busy = false;
    el("prepFields").disabled = state?.tactico_disponible === false;
    el("start").disabled = state?.tactico_disponible === false;
    el("adjust").disabled = false;
    render();
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
  if (busy || playing) return;
  try { state = await api("estado"); el("error").hidden = true; el("reconnect").hidden = true; displayedEvents = 0; el("log").replaceChildren(); render(); schedule(); }
  catch (error) { fail(error); }
}
el("reconnect").addEventListener("click", load);
setupBoard();
load();
