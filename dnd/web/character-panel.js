// Pestañas de la ficha: presentación de los valores públicos del motor.
const panelesPersonaje = {personaje: "characterSummaryPanel", clase: "skillsPanel", inventario: "inventoryPanel", chispa: "sparkPanel"};
function seleccionarPestanaPersonaje(tipo) {
  if (!panelesPersonaje[tipo]) return;
  coleccionAbierta = tipo;
  for (const [nombre, panel] of Object.entries(panelesPersonaje)) elemento(panel).classList.toggle("hidden", nombre !== tipo);
  for (const tab of elemento("characterTabs").querySelectorAll("button")) {
    const activa = tab.dataset.characterTab === tipo;
    tab.setAttribute("aria-selected", String(activa)); tab.tabIndex = activa ? 0 : -1;
    tab.onclick = () => seleccionarPestanaPersonaje(tab.dataset.characterTab);
    tab.onkeydown = evento => {
      const teclas = ["ArrowLeft", "ArrowRight", "Home", "End"];
      if (!teclas.includes(evento.key)) return;
      evento.preventDefault();
      const tabs = [...elemento("characterTabs").querySelectorAll("button")], indice = tabs.indexOf(tab);
      const destino = evento.key === "Home" ? 0 : evento.key === "End" ? tabs.length - 1 : (indice + (evento.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      seleccionarPestanaPersonaje(tabs[destino].dataset.characterTab); tabs[destino].focus();
    };
  }
  elemento("combatItemDetails").classList.toggle("hidden", !["personaje", "inventario"].includes(tipo));
  elemento("managementRule").classList.toggle("hidden", !["personaje", "inventario"].includes(tipo));
  ocultarTooltip();
}
function renderizarFichaPersonaje(jugador) {
  const numero = valor => Number.isFinite(valor) ? Number(valor.toFixed(2)).toLocaleString("es") : "—";
  const porcentajeFicha = valor => Number.isFinite(valor) ? `${numero(valor * 100)}%` : "—";
  elemento("collectionTitle").textContent = jugador.nombre || "Personaje";
  elemento("characterIdentity").textContent = `Nivel ${jugador.nivel} · ${jugador.clase_nombre} · ${numero(jugador.oro)} de oro`;
  elemento("primaryStats").replaceChildren(...Object.entries({fuerza: "Fuerza", destreza: "Destreza", constitucion: "Constitución"}).map(([clave, nombre]) => {
    const ficha = nodoGestion("div", undefined, "primary-stat");
    ficha.append(nodoGestion("span", nombre), nodoGestion("strong", numero(jugador[clave])),
      nodoGestion("small", `Base ${numero(jugador.stats_base?.[clave])} · Equipo +${numero(jugador.bonus_equipo?.[clave] ?? 0)}`));
    return ficha;
  }));
  const secundarias = [
    ["Vida", `${numero(jugador.hp)} / ${numero(jugador.salud_maxima)}`],
    ["Energía", `${numero(jugador.energia)} / ${numero(jugador.energia_maxima)}`],
    ["Daño del personaje", `${numero(jugador.ataque_minimo)}–${numero(jugador.ataque_maximo)}`],
    ["Armadura", numero(jugador.armadura)], ["Mitigación por armadura", porcentajeFicha(jugador.mitigacion_armadura)],
    ["Iniciativa", numero(jugador.iniciativa)], ["Evasión actual", porcentajeFicha(jugador.evasion)],
    ["Movimiento", jugador.movimiento], ["Regeneración por turno", jugador.regeneracion],
    ["Impacto", jugador.impacto], ["Estabilidad", jugador.estabilidad],
    ["Resistencia Física", jugador.resistencia_fisica], ["Penetración total", Number(jugador.penetracion.toFixed(1))],
    ["Crítico del arma", porcentajeFicha(jugador.critico_arma)], ["Penetración del arma", numero(jugador.penetracion_arma)],
    ["Absorción pasiva", porcentajeFicha(jugador.absorcion_pasiva)], ["Bloqueo activo", porcentajeFicha(jugador.bloqueo_activo)],
    ["Peso equipado / capacidad", `${numero(jugador.peso_equipado)} / ${numero(jugador.capacidad_peso)}`],
    ["Alcance del arma", numero(jugador.alcance_arma)],
    ["Durabilidad del arma", numero(jugador.durabilidad_arma)], ["Durabilidad del escudo", `${numero(jugador.durabilidad_escudo)} / ${numero(jugador.durabilidad_maxima_escudo)}`], ["Puntos de estadística", numero(jugador.puntos_estadistica)],
  ];
  elemento("secondaryStats").replaceChildren(...secundarias.map(([nombre, valor]) => {
    const fila = nodoGestion("div"); fila.append(nodoGestion("dt", nombre), nodoGestion("dd", valor)); return fila;
  }));
  const penalizaciones = [];
  if (jugador.penalizacion_evasion_peso > 0) penalizaciones.push(`evasión −${porcentajeFicha(jugador.penalizacion_evasion_peso)}`);
  if (jugador.modificador_movimiento_carga < 0) penalizaciones.push(`movimiento ${jugador.modificador_movimiento_carga}`);
  elemento("characterWeightStatus").textContent = penalizaciones.length ? `Penalización por peso: ${penalizaciones.join(" · ")}.` : "Sin penalizaciones por peso. Las estadísticas incluyen las bonificaciones aplicadas por el motor.";
  elemento("characterClassName").textContent = jugador.clase_nombre || "Sin clase";
  elemento("characterClassHelp").textContent = jugador.clase ? "Consulta las habilidades de tu clase y utiliza tus puntos para aprenderlas o mejorarlas entre combates." : jugador.clase_pendiente ? "Puedes elegir tu clase entre combates. La elección es permanente." : "La elección de clase se desbloquea al nivel 10.";
  const elecciones = elemento("characterClassChoices"); elecciones.replaceChildren();
  if (jugador.clase_pendiente) {
    for (const [id, clase] of Object.entries(estado.clases || {})) {
      const boton = nodoGestion("button", `Elegir ${clase.nombre}`);
      boton.disabled = !["nivel", "transicion"].includes(estado.fase) || solicitudEnCurso;
      boton.onclick = async () => {
        const ok = await llamarApi("clase", {clase: id});
        elemento("managementMessage").textContent = ok ? `Clase elegida: ${estado.jugador.clase_nombre}.` : elemento("error").textContent;
      };
      elecciones.append(boton);
    }
  }
  elemento("sparkTitle").textContent = jugador.chispa ? "Chispa latente" : "Chispa sin despertar";
  elemento("sparkStatus").textContent = jugador.chispa ? "Tu personaje ya posee una chispa." : `Se despierta al alcanzar el nivel ${jugador.chispa_nivel_desbloqueo ?? "—"}.`;
  elemento("sparkHelp").textContent = "La administración de la chispa aún no está habilitada. Aquí aparecerán sus opciones cuando estén disponibles.";
  elemento("sparkPanel").classList.toggle("awakened", Boolean(jugador.chispa));
}
