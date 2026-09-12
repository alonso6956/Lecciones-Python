"use strict";
let boardUnit = "", boardTool = "posicionar", inspectedCell = null;
let playback = null, playing = false, autoCombat = true;
const terrainMarks = {suelo: "", muro: "▦", cobertura: "▰", altura: "▲", barro: "≈", trampa_aliada: "✦", trampa_rival: "✕"};
const coordinate = p => `${String.fromCharCode(65 + p[0])}${p[1] + 1}`;

function renderBoard() {
  if (!state?.tablero) return;
  const board = playback?.tablero || state.tablero;
  const combat = playback || state.combate;
  const actors = combat ? [...combat.party, combat.jefe] : [...state.party, state.encuentro];
  const visibleActors = [...actors].sort((a, b) => Number(b.hp > 0) - Number(a.hp > 0));
  const editable = state.fase === "preparacion" && state.tactico_disponible !== false && !busy;
  el("boardFields").disabled = !editable;
  el("boardRound").textContent = combat ? `Ronda ${combat.ronda} · ${playing ? "Reproduciendo acciones" : state.fase === "resultado" ? "Combate terminado" : "Combate en curso"}` : `${state.selecciones.length}/6 personajes · Despliegue`;
  const units = el("boardUnit"); units.replaceChildren();
  for (const actor of actors) {
    const option = node("option", actor.nombre); option.value = actor.id; units.append(option);
  }
  if (!actors.some(a => a.id === boardUnit)) boardUnit = actors[0]?.id || "";
  units.value = boardUnit;
  const tools = el("boardTool"); tools.replaceChildren();
  const move = node("option", "Posicionar personaje"); move.value = "posicionar"; tools.append(move);
  for (const [id, terrain] of Object.entries(state.catalogo.terrenos)) {
    const option = node("option", `${terrain.nombre}${id === "suelo" ? " / borrar" : ""}`); option.value = id; tools.append(option);
  }
  tools.value = boardTool;
  el("toolHelp").textContent = boardTool === "posicionar" ? "Selecciona una ficha o elige un personaje y después una casilla. Aliados: A–C. Guardián: H–J." : state.catalogo.terrenos[boardTool].descripcion;
  const focused = document.activeElement?.dataset?.cell;
  const grid = el("battleGrid"); grid.replaceChildren();
  grid.style.setProperty("--columns", board.ancho);
  const cells = new Map(board.celdas.map(c => [`${c.x},${c.y}`, c.tipo]));
  const effects = new Map(board.efectos.map(c => [`${c.x},${c.y}`, c]));
  for (let y = 0; y < board.alto; y++) {
    for (let x = 0; x < board.ancho; x++) {
      const point = [x, y], key = `${x},${y}`, terrain = cells.get(key) || "suelo";
      const actor = visibleActors.find(a => board.posiciones[a.id]?.[0] === x && board.posiciones[a.id]?.[1] === y);
      const label = coordinate(point), tile = node("button"); tile.type = "button";
      tile.dataset.cell = key;
      const effect = effects.get(key);
      tile.className = `battle-cell terrain-${terrain}${x < 3 ? " deploy-ally" : x > 6 ? " deploy-enemy" : ""}${effect ? " smoke" : ""}${actor?.id === playback?.actor_id ? " acting" : ""}${actor?.id === boardUnit && editable ? " selected-unit" : ""}`;
      tile.setAttribute("aria-label", `${label}: ${state.catalogo.terrenos[terrain].nombre}${actor ? ` · ${actor.nombre} · ${actor.hp}/${actor.hp_max} vida` : ""}${effect ? " · Humo" : ""}`);
      tile.title = tile.getAttribute("aria-label");
      tile.append(node("span", label, "cell-coordinate"), node("span", terrainMarks[terrain], "terrain-mark"));
      if (actor) {
        const boss = actor.id === state.encuentro.id;
        const index = state.selecciones.findIndex(s => s.personaje_id === actor.id);
        const token = node("span", actor.hp <= 0 ? "†" : boss ? "G" : String(index + 1), `unit-token ${boss ? "enemy-token" : "ally-token"}${actor.hp <= 0 ? " fallen" : ""}`);
        tile.append(token, node("span", actor.nombre, "unit-name"));
        const bar = node("span", undefined, "unit-hp"), fill = node("i");
        fill.style.width = `${Math.max(0, actor.hp / actor.hp_max * 100)}%`; bar.append(fill); tile.append(bar);
      }
      tile.onclick = () => selectCell(point, actor);
      tile.onkeydown = event => {
        const delta = {ArrowLeft: -1, ArrowRight: 1, ArrowUp: -board.ancho, ArrowDown: board.ancho}[event.key];
        if (delta !== undefined) {event.preventDefault(); grid.children[Math.max(0, Math.min(board.ancho * board.alto - 1, y * board.ancho + x + delta))].focus();}
      };
      grid.append(tile);
    }
  }
  if (focused) [...grid.children].find(tile => tile.dataset.cell === focused)?.focus();
  const counts = Object.entries(state.catalogo.terrenos).filter(([id]) => id !== "suelo").map(([id, t]) => `${t.nombre}: ${board.celdas.filter(c => c.tipo === id).length}/${t.limite}`);
  el("terrainBudget").textContent = state.fase === "preparacion" ? counts.join(" · ") : "Las maniobras pueden añadir terreno durante el combate.";
  if (inspectedCell) describeCell(board, visibleActors, inspectedCell);
  if (playback?.evento) el("boardEvent").textContent = eventText(playback.evento);
  else if (!playing) el("boardEvent").textContent = state.fase === "preparacion" ? "Configura el campo; los cambios se aplican al próximo intento." : "Pulsa una casilla para inspeccionar el terreno y la unidad.";
  el("pauseCombat").textContent = autoCombat ? "Pausar" : "Continuar";
  el("pauseCombat").disabled = state.fase !== "combate" && !playing;
  el("nextRound").disabled = busy || playing || state.fase !== "combate";
}

function describeCell(board, actors, point) {
  const terrain = board.celdas.find(c => c.x === point[0] && c.y === point[1])?.tipo || "suelo";
  const actor = actors.find(a => board.posiciones[a.id]?.[0] === point[0] && board.posiciones[a.id]?.[1] === point[1]);
  const details = el("cellDetails"); details.replaceChildren(node("h3", `${coordinate(point)} · ${state.catalogo.terrenos[terrain].nombre}`), node("p", state.catalogo.terrenos[terrain].descripcion));
  if (actor) {
    details.append(node("h3", actor.nombre), node("p", `${actor.hp}/${actor.hp_max} vida · Alcance ${actor.alcance_arma || 1} · Velocidad ${actor.velocidad}`));
    details.append(node("p", `Estados: ${Object.keys(actor.estados || {}).join(", ") || "ninguno"}`));
  }
}

async function selectCell(point, actor) {
  inspectedCell = point;
  if (busy || playing || state.fase !== "preparacion" || !state.tactico_disponible) {renderBoard(); return;}
  if (boardTool === "posicionar" && actor) {boardUnit = actor.id; renderBoard(); return;}
  const plan = {posiciones: structuredClone(state.tablero.posiciones), celdas: structuredClone(state.tablero.celdas)};
  if (boardTool === "posicionar") plan.posiciones[boardUnit] = point;
  else {
    plan.celdas = plan.celdas.filter(c => c.x !== point[0] || c.y !== point[1]);
    if (boardTool !== "suelo") plan.celdas.push({x: point[0], y: point[1], tipo: boardTool});
  }
  await mutate("campo", {tablero: plan});
}

async function changePartySize(amount) {
  if (busy || state.fase !== "preparacion") return;
  const next = state.selecciones.map(s => ({...s}));
  if (amount < 0) next.pop();
  else {
    const free = Object.entries(state.catalogo.personajes).find(([id]) => !next.some(s => s.personaje_id === id));
    if (!free) return;
    next.push({personaje_id: free[0], arma: free[1].arma_equipada, build: "ofensiva", prioridad: "agresiva", maniobra: "ninguna"});
  }
  await mutate("preparar", {selecciones: next});
}

async function animateBoard() {
  const frames = state.reproduccion || [];
  if (!frames.length || Number(el("speed").value) === 0) return;
  playing = true;
  try {
    for (const frame of frames) {
      playback = frame; renderBoard();
      await new Promise(resolve => setTimeout(resolve, Math.max(50, Number(el("speed").value) / 2)));
    }
  } finally {playback = null; playing = false;}
}

function setupBoard() {
  el("boardUnit").onchange = () => {boardUnit = el("boardUnit").value; renderBoard();};
  el("boardTool").onchange = () => {boardTool = el("boardTool").value; renderBoard();};
  el("clearTerrain").onclick = () => mutate("campo", {tablero: {posiciones: state.tablero.posiciones, celdas: []}});
  el("addHero").onclick = () => changePartySize(1);
  el("removeHero").onclick = () => changePartySize(-1);
  el("pauseCombat").onclick = () => {autoCombat = !autoCombat; clearTimeout(timer); renderBoard(); if (autoCombat && !busy) schedule();};
  el("nextRound").onclick = () => {autoCombat = false; clearTimeout(timer); mutate("avanzar", {});};
}
