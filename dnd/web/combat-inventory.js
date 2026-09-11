// Gestión de personaje: usa exclusivamente las acciones y datos del motor.
let filtroInventario = "consumible", filtroSlot = null, gestionPendiente = false;
let detalleInventarioId = null;
const nombresEquipo = {casco: "Casco", mano_principal: "Principal", pecho: "Pecho", mano_secundaria: "Secundaria", brazos: "Brazos", piernas: "Piernas"};
const iconosEquipo = {casco: "🪖", mano_principal: "⚔️", mano_secundaria: "🛡️", pecho: "🥋", brazos: "🧤", piernas: "👖"};
const nodoGestion = (tag, texto, clase = "") => {
  const n = document.createElement(tag); if (texto !== undefined) n.textContent = texto;
  if (clase) n.className = clase; return n;
};
function puedeCambiarEquipo() { return estado?.jugador?.hp > 0 && !["menu", "inicio", "combate", "muerte", "fin"].includes(estado.fase); }
function iconoInventario(item) {
  const armas = {espada: "⚔️", daga: "🗡️", maza: "🔨", lanza: "🔱"};
  return item.clase === "arma" ? armas[item.tipo_arma] || "⚔️" : iconosEquipo[item.slot] || (item.clase === "consumible" ? "🧪" : "💎");
}
function accionInventario(item) {
  if (gestionPendiente) return {texto: "Espera…", motivo: "Resolviendo la acción."};
  if (item.clase === "consumible") {
    if (["menu", "inicio", "muerte", "fin"].includes(estado.fase) || estado.jugador.hp <= 0) return {texto: "No disponible", motivo: "No puedes usar objetos en este momento."};
    if (item.efecto !== "curacion") return {texto: "No disponible", motivo: "Este objeto no se puede usar aquí."};
    if (estado.jugador.hp >= estado.jugador.salud_maxima) return {texto: "Vida completa", motivo: "Ya tienes toda la vida. La poción no se consumirá."};
    return {texto: estado.fase === "combate" ? "Usar · 1 acción" : "Usar", ruta: "usar-item"};
  }
  if (!["arma", "armadura", "secundario"].includes(item.clase)) return {texto: "Material", motivo: "Se utiliza en el taller del menú principal."};
  if (item.equipado) return {texto: "Equipado", motivo: "Este objeto ya está equipado."};
  if (!puedeCambiarEquipo()) return {texto: "Bloqueado", motivo: "Puedes cambiar equipo entre combates."};
  if (!item.puede_equipar) return {texto: "Sin requisitos", motivo: requisitosObjeto(item.requisitos)};
  return {texto: "Equipar", ruta: "equipar"};
}
function abrirGestionPersonaje(tipo) {
  filtroInventario = tipo === "equipo" ? "equipo" : "consumible"; filtroSlot = null; detalleInventarioId = null;
  elemento("managementMessage").textContent = "";
  renderizarInventario(estado.jugador); renderizarEquipo(estado.jugador);
}
function filtrarInventario(categoria, slot = null) {
  if (coleccionAbierta) seleccionarPestanaPersonaje("inventario");
  filtroInventario = categoria; filtroSlot = slot; detalleInventarioId = null;
  renderizarInventario(estado.jugador); renderizarEquipo(estado.jugador);
}
function resumenInventario(item) {
  if (item.clase === "consumible") return `Recupera ${item.valor} de vida`;
  if (item.clase === "arma") return `Daño ${item.ataque.join("–")} · Tier ${item.tier}${item.dos_manos ? " · 2 manos" : ""}`;
  if (item.clase === "armadura") return `Armadura +${item.defensa}`;
  if (item.clase === "secundario") return `Bloqueo ${Math.round(item.probabilidad_bloqueo * 100)}%`;
  return "Componente de crafteo";
}
function mostrarDetalleInventario(item) {
  detalleInventarioId = item.id;
  const panel = elemento("combatItemDetails"), accion = accionInventario(item);
  panel.replaceChildren(nodoGestion("strong", item.nombre), nodoGestion("p", descripcionObjeto(item)));
  if (item.clase === "arma") {
    panel.append(nodoGestion("p", `Velocidad ×${item.velocidad} · Crítico ${Math.round(item.critico * 100)}% · Penetración ${Number(item.penetracion.toFixed(1))} · Durabilidad ${item.durabilidad}`));
    if (item.afijo?.id) panel.append(nodoGestion("p", `${item.afijo.id}: ${Math.round(item.afijo.probabilidad * 100)}% · ${item.afijo.dano} daño durante ${item.afijo.turnos} turno(s).`));
    if (item.dos_manos) panel.append(nodoGestion("p", "Ocupa ambas manos; al equiparla se retira el objeto secundario."));
  }
  panel.append(nodoGestion("p", accion.motivo || (accion.ruta === "usar-item" ? (estado.fase === "combate" ? "Clic para usar. Consume tu acción y se resuelve el turno." : "Clic para recuperar vida.") : "Clic para equipar."), "item-action-hint"));
}
async function ejecutarGestion(ruta, datos, etiqueta) {
  if (gestionPendiente || solicitudEnCurso) return;
  const turno = estado.fase === "combate" && ruta === "usar-item";
  gestionPendiente = true;
  const mensaje = elemento("managementMessage"); mensaje.textContent = "Resolviendo la acción…";
  elemento("characterManagement").setAttribute("aria-busy", "true");
  renderizarInventario(estado.jugador); renderizarEquipo(estado.jugador);
  try {
    const ok = await llamarApi(ruta, datos);
    mensaje.textContent = ok ? (turno ? "Turno resuelto." : `${etiqueta}.`) : elemento("error").textContent || "No se pudo completar la acción.";
    if (ok && turno) cerrarColeccion();
  } finally {
    gestionPendiente = false; elemento("characterManagement").setAttribute("aria-busy", "false");
    if (estado?.jugador) { renderizarInventario(estado.jugador); renderizarEquipo(estado.jugador); }
    if (coleccionAbierta && !elemento("collectionPanel").contains(document.activeElement)) elemento("closeCollectionButton").focus();
  }
}
function renderizarInventario(jugador) {
  elemento("managementHealth").textContent = `Vida ${jugador.hp} / ${jugador.salud_maxima}`;
  elemento("managementRule").textContent = estado.fase === "combate" ? "Las pociones consumen una acción. El equipo se cambia entre combates." : puedeCambiarEquipo() ? "Puedes usar pociones y cambiar equipo antes del próximo combate." : "Consulta de inventario · Acciones no disponibles.";
  for (const tab of elemento("inventoryTabs").querySelectorAll("button")) {
    tab.setAttribute("aria-pressed", String(tab.dataset.category === filtroInventario));
    tab.onclick = () => filtrarInventario(tab.dataset.category);
  }
  elemento("clearEquipmentFilter").classList.toggle("hidden", !filtroSlot);
  elemento("clearEquipmentFilter").onclick = () => filtrarInventario(filtroInventario);
  const items = jugador.inventario.filter(item => (!filtroSlot || item.slot === filtroSlot) &&
    (filtroInventario === "todos" || (filtroInventario === "equipo" ? ["armadura", "secundario"].includes(item.clase) : item.clase === filtroInventario)));
  elemento("inventoryFilterLabel").textContent = `${filtroSlot ? nombresEquipo[filtroSlot] + " · " : ""}${items.length} objetos`;
  const grid = elemento("inventoryList"), scroll = grid.scrollTop;
  const focoId = document.activeElement?.dataset?.inventoryId;
  const botones = items.map(item => {
    const accion = accionInventario(item), boton = nodoGestion("button", undefined, `battle-item ${item.equipado ? "is-equipped" : ""}`);
    boton.type = "button"; boton.dataset.inventoryId = item.id;
    boton.setAttribute("aria-disabled", String(!accion.ruta));
    boton.setAttribute("aria-label", `${item.nombre}, cantidad ${item.cantidad}. ${resumenInventario(item)}. ${accion.motivo || accion.texto}`);
    const icono = nodoGestion("span", iconoInventario(item), "battle-item-icon"); icono.setAttribute("aria-hidden", "true");
    const texto = nodoGestion("span", undefined, "battle-item-info");
    texto.append(nodoGestion("strong", item.nombre), nodoGestion("small", resumenInventario(item)), nodoGestion("span", accion.texto, `battle-item-action ${item.clase === "consumible" ? "use" : "equip"}`));
    boton.append(icono, texto, nodoGestion("span", `×${item.cantidad}`, "battle-item-quantity"));
    boton.onpointerenter = () => mostrarDetalleInventario(item); boton.onfocus = () => mostrarDetalleInventario(item);
    boton.onclick = () => {
      mostrarDetalleInventario(item);
      const actual = accionInventario(item);
      if (actual.ruta) ejecutarGestion(actual.ruta, {item: item.id}, actual.ruta === "equipar" ? `${item.nombre} equipado` : `${item.nombre} utilizada`);
    };
    return boton;
  });
  grid.replaceChildren(...botones);
  if (!items.length) grid.append(nodoGestion("p", filtroSlot ? "No llevas objetos compatibles con este slot." : "No llevas objetos de esta categoría.", "battle-empty"));
  grid.scrollTop = scroll;
  if (focoId) botones.find(b => b.dataset.inventoryId === focoId)?.focus();
  const detalle = jugador.inventario.find(i => i.id === detalleInventarioId && items.includes(i));
  if (detalle) mostrarDetalleInventario(detalle);
  else elemento("combatItemDetails").replaceChildren(nodoGestion("p", "Enfoca o pasa el cursor sobre un objeto para ver sus detalles."));
}
function renderizarEquipo(jugador) {
  elemento("equipmentTotalDefense").textContent = jugador.armadura;
  elemento("equipmentDefense").textContent = jugador.armadura_equipo;
  const focoSlot = document.activeElement?.dataset?.bodySlot;
  const slots = Object.entries(nombresEquipo).map(([slot, nombre]) => {
    const actual = jugador.equipamiento[slot], item = jugador.inventario.find(i => i.id === actual?.id);
    const bloqueada = slot === "mano_secundaria" && jugador.equipamiento.mano_principal?.dos_manos;
    const caja = nodoGestion("div", undefined, `body-slot slot-${slot}${actual ? " filled" : ""}${filtroSlot === slot ? " selected" : ""}`);
    const boton = nodoGestion("button", undefined, "body-slot-select"); boton.dataset.bodySlot = slot;
    const icono = nodoGestion("span", item ? iconoInventario(item) : iconosEquipo[slot], "body-slot-icon"); icono.setAttribute("aria-hidden", "true");
    boton.append(nodoGestion("small", nombre), icono, nodoGestion("span", actual?.nombre || (bloqueada ? "Arma a 2 manos" : "Vacío"), "body-slot-name"));
    boton.setAttribute("aria-label", `${nombre}: ${actual?.nombre || (bloqueada ? "Ocupada por arma de dos manos" : "vacío")}. Ver objetos compatibles.`);
    boton.setAttribute("aria-pressed", String(filtroSlot === slot));
    boton.onclick = () => { filtrarInventario(slot === "mano_principal" ? "arma" : "equipo", slot); elemento("inventoryList").querySelector("button")?.focus(); };
    if (item) { boton.onpointerenter = () => mostrarDetalleInventario(item); boton.onfocus = () => mostrarDetalleInventario(item); }
    caja.append(boton);
    if (actual && slot !== "mano_principal") {
      const quitar = nodoGestion("button", "Quitar", "body-slot-remove");
      quitar.disabled = gestionPendiente || !puedeCambiarEquipo();
      quitar.setAttribute("aria-label", `Desequipar ${actual.nombre}`);
      quitar.onclick = () => ejecutarGestion("desequipar", {slot}, `${actual.nombre} retirado`); caja.append(quitar);
    }
    return caja;
  });
  elemento("equipmentList").replaceChildren(...slots);
  if (focoSlot) elemento("equipmentList").querySelector(`[data-body-slot="${focoSlot}"]`)?.focus();
}
