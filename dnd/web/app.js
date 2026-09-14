// Atajo para buscar un elemento del HTML por su id.
const elemento = (id) => document.getElementById(id);
const UI_VERSION = "25";

// Última copia del estado enviada por Python.
let estado = null;
let menuPausaAbierto = false;
let modoSlots = null;
let coleccionAbierta = null;
let focoAntesColeccion = null;
let solicitudEnCurso = false;
let botonConTooltip = null;
let botonTooltipProgramado = null;
let temporizadorTooltip = null;


function ocultarTooltip(boton = null) {
  if (
    boton
    && botonConTooltip !== boton
    && botonTooltipProgramado !== boton
  ) return;
  if (temporizadorTooltip !== null) {
    window.clearTimeout(temporizadorTooltip);
    temporizadorTooltip = null;
  }
  botonTooltipProgramado = null;
  if (!boton || botonConTooltip === boton) {
    botonConTooltip = null;
    elemento("buttonTooltip").hidden = true;
  }
}


function mostrarTooltip(boton, texto) {
  const tooltip = elemento("buttonTooltip");
  const margen = 8;
  temporizadorTooltip = null;
  botonTooltipProgramado = null;
  botonConTooltip = boton;
  tooltip.textContent = texto;
  tooltip.hidden = false;
  tooltip.style.left = "0px";
  tooltip.style.top = "0px";

  const botonRect = boton.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();
  const izquierda = Math.min(
    window.innerWidth - tooltipRect.width - margen,
    Math.max(margen, botonRect.right - tooltipRect.width),
  );
  const encima = botonRect.top - tooltipRect.height - margen;
  const arriba = encima >= margen
    ? encima
    : Math.min(
      window.innerHeight - tooltipRect.height - margen,
      botonRect.bottom + margen,
    );

  tooltip.style.left = `${izquierda}px`;
  tooltip.style.top = `${Math.max(margen, arriba)}px`;
}


function programarTooltip(boton, texto) {
  ocultarTooltip();
  botonTooltipProgramado = boton;
  temporizadorTooltip = window.setTimeout(() => {
    if (botonTooltipProgramado === boton && document.body.contains(boton)) {
      mostrarTooltip(boton, texto);
    }
  }, 300);
}


function validarVersion(nuevoEstado) {
  if (nuevoEstado?.ui_version && nuevoEstado.ui_version !== UI_VERSION) {
    const versionServidor = String(nuevoEstado.ui_version);
    const versionSolicitada = new URLSearchParams(window.location.search).get("ui");
    if (versionSolicitada !== versionServidor) {
      const destino = new URL(window.location.href);
      destino.searchParams.set("ui", versionServidor);
      window.location.replace(destino.toString());
      return false;
    }

    const mensaje = (
      `La interfaz es versión ${UI_VERSION}, pero el servidor sigue en la `
      + `versión ${versionServidor}. Detén y vuelve a ejecutar main.py.`
    );
    elemento("error").textContent = mensaje;
    elemento("menuMessage").textContent = mensaje;
    return false;
  }
  return true;
}


async function llamarApi(ruta, datos = {}) {
  if (solicitudEnCurso) return false;
  solicitudEnCurso = true;
  try { return await ejecutarSolicitudApi(ruta, datos); }
  finally { solicitudEnCurso = false; }
}


async function ejecutarSolicitudApi(ruta, datos = {}) {
  let respuesta;
  let resultado;
  try {
    respuesta = await fetch(`/api/${ruta}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Dungeon-UI-Version": UI_VERSION,
      },
      body: JSON.stringify(datos),
    });
    resultado = await respuesta.json();
  } catch {
    const mensaje = "Se perdió la conexión con Dungeon. Reinicia la aplicación.";
    elemento("error").textContent = mensaje;
    elemento("menuMessage").textContent = mensaje;
    if (menuPausaAbierto) elemento("pauseMessage").textContent = mensaje;
    return false;
  }

  if (!respuesta.ok) {
    elemento("error").textContent = resultado.error;
    elemento("menuMessage").textContent = resultado.error;
    if (menuPausaAbierto) elemento("pauseMessage").textContent = resultado.error;
    estado = resultado.estado;
    renderizar();
    return false;
  }

  if (!validarVersion(resultado)) return false;

  estado = resultado;
  elemento("error").textContent = "";
  elemento("menuMessage").textContent = "";
  renderizar();
  return true;
}


function mostrarAccionesPausa() {
  modoSlots = null;
  elemento("pauseTitle").textContent = "Menú de pausa";
  elemento("pauseActions").classList.remove("hidden");
  elemento("slotPanel").classList.add("hidden");
  elemento("pauseMessage").textContent = "El progreso se guarda al avanzar de habitación o al morir.";
}


function crearBotonSlot(datosSlot) {
  const boton = document.createElement("button");
  const titulo = document.createElement("strong");
  const resumen = document.createElement("span");
  const fecha = document.createElement("small");
  boton.className = "slot-button";
  if (datosSlot.slot === estado.slot_activo) boton.classList.add("active");
  titulo.textContent = `Personaje ${datosSlot.slot}`;

  if (datosSlot.ocupado) {
    const datos = datosSlot.resumen;
    resumen.textContent = (
      `${datos.personaje} · Nivel ${datos.nivel} · Habitación ${datos.habitacion}`
    );
    fecha.textContent = "Progreso guardado · Empieza una nueva expedición";
  } else {
    resumen.textContent = datosSlot.error || "Slot vacío";
    fecha.textContent = "";
  }

  boton.append(titulo, resumen, fecha);
  boton.disabled = !datosSlot.ocupado;
  boton.onclick = async () => {
    const correcto = await llamarApi("cargar", {id: datosSlot.id});
    if (correcto) cerrarPausa();
  };
  const fila = document.createElement("div");
  const descartar = document.createElement("button");
  descartar.textContent = "Descartar personaje";
  descartar.disabled = !datosSlot.ocupado;
  descartar.onclick = async () => {
    const nombre = datosSlot.resumen.personaje;
    if (!window.confirm(`¿Descartar a ${nombre}? Se eliminará del roster con toda su experiencia, oro y equipo. Esta acción no se puede deshacer desde el juego.`)) return;
    descartar.disabled = true;
    const correcto = await llamarApi("descartar", {id: datosSlot.id, confirmado: true});
    if (correcto) mostrarSlots("cargar", true);
    else descartar.disabled = false;
  };
  fila.append(boton, descartar);
  return fila;
}


function mostrarSlots(modo, desdeMenu = false) {
  modoSlots = modo;
  menuPausaAbierto = true;
  elemento("pauseOverlay").classList.remove("hidden");
  elemento("pauseActions").classList.add("hidden");
  elemento("slotPanel").classList.remove("hidden");
  elemento("pauseTitle").textContent = "Elegir personaje";
  elemento("backPauseButton").onclick = () => {
    if (desdeMenu) cerrarPausa();
    else mostrarAccionesPausa();
  };
  elemento("pauseMessage").textContent = "";
  elemento("slotList").replaceChildren();
  if (!Array.isArray(estado?.slots)) {
    elemento("slotHelp").textContent = "No se pudo cargar la lista de personajes. Vuelve al menú y recarga la página.";
    return;
  }
  elemento("slotHelp").textContent = "Elige un personaje del roster. Comenzarás en la habitación 1.";
  elemento("slotList").replaceChildren(...estado.slots.map(crearBotonSlot));
  if (!estado.slots.length) elemento("slotHelp").textContent = "No quedan personajes. Vuelve al menú para crear uno.";
}


function abrirPausa() {
  menuPausaAbierto = true;
  elemento("pauseOverlay").classList.remove("hidden");
  mostrarAccionesPausa();
}


function cerrarPausa() {
  menuPausaAbierto = false;
  modoSlots = null;
  elemento("pauseOverlay").classList.add("hidden");
}


function abrirColeccion(tipo = "personaje") {
  focoAntesColeccion = document.activeElement;
  abrirGestionPersonaje("inventario");
  renderizarFichaPersonaje(estado.jugador);
  seleccionarPestanaPersonaje(tipo);
  elemento("collectionOverlay").classList.remove("hidden");
  elemento("characterTabs").querySelector('[aria-selected="true"]').focus();
}


function cerrarColeccion() {
  const estabaAbierta = Boolean(coleccionAbierta);
  coleccionAbierta = null;
  elemento("collectionOverlay").classList.add("hidden");
  ocultarTooltip();
  if (estabaAbierta && focoAntesColeccion?.isConnected) focoAntesColeccion.focus();
}


function crearBoton(texto, manejador, opciones = {}) {
  const boton = document.createElement("button");
  boton.textContent = texto;
  boton.onclick = manejador;
  boton.disabled = opciones.deshabilitado || false;

  if (opciones.tooltip) {
    boton.setAttribute("aria-describedby", "buttonTooltip");
    boton.setAttribute("aria-label", `${texto}. ${opciones.tooltip}`);
    boton.addEventListener("pointerenter", () => {
      programarTooltip(boton, opciones.tooltip);
    });
    boton.addEventListener("pointerleave", () => ocultarTooltip(boton));
    boton.addEventListener("focus", () => mostrarTooltip(boton, opciones.tooltip));
    boton.addEventListener("blur", () => ocultarTooltip(boton));
  }

  if (opciones.primario) {
    boton.classList.add("primary");
  }
  if (opciones.activo) {
    boton.classList.add("skill-active");
  }
  if (opciones.completo) {
    boton.classList.add("full");
  }

  elemento("actions").appendChild(boton);
}


async function salirAlMenuPrincipal() {
  if (estado.jugador && !window.confirm("¿Seguro que quieres salir? Los avances obtenidos desde el último guardado se perderán y regresarás a la habitación 1")) return;
  const correcto = await llamarApi("reiniciar");
  if (correcto) cerrarPausa();
}


function porcentaje(valor, maximo) {
  const calculado = (valor / maximo) * 100;
  const limitado = Math.max(0, Math.min(100, calculado));
  return `${limitado}%`;
}


function renderizarInicio() {
  if (estado.fase !== "inicio") {
    return;
  }

  elemento("start").classList.remove("hidden");
  elemento("game").classList.add("hidden");


}


function renderizarMenu() {
  elemento("menu").classList.remove("hidden");
  elemento("start").classList.add("hidden");
  elemento("game").classList.add("hidden");
  elemento("roomBadge").classList.add("hidden");
  elemento("pauseButton").classList.add("hidden");
  elemento("characterButton").classList.add("hidden");
  cerrarColeccion();
  elemento("loadButton").disabled = !estado.guardado_disponible;
  elemento("tacticalButton").disabled = !estado.tactico_disponible;
  elemento("tacticalMessage").textContent = estado.mensaje_bloqueo_tactico || "";
  elemento("menuMessage").textContent = [...(estado.registro || []), ...(estado.avisos_roster || [])].join(" ");
}


function renderizarPanel(jugador) {
  elemento("playerName").textContent = jugador.nombre;
  elemento("weaponName").textContent = jugador.arma;
  elemento("className").textContent = `${jugador.clase_nombre} · ${jugador.chispa ? "Chispa latente" : "Sin chispa"}`;
  elemento("hpText").textContent = `${jugador.hp}/${jugador.salud_maxima}`;
  elemento("hpBar").style.width = porcentaje(
    jugador.hp,
    jugador.salud_maxima,
  );
  elemento("energyText").textContent = (
    `${jugador.energia}/${jugador.energia_maxima}`
  );

  const puntosDeEnergia = Array.from(
    { length: jugador.energia_maxima },
    (_, indice) => {
      const encendido = indice < jugador.energia ? "on" : "";
      return `<i class="pip ${encendido}"></i>`;
    },
  );

  elemento("energyPips").innerHTML = puntosDeEnergia.join("");
  elemento("level").textContent = jugador.nivel;
  elemento("exp").textContent = jugador.exp_siguiente_nivel === null
    ? "MÁX"
    : `${jugador.exp}/${jugador.exp_siguiente_nivel}`;
  elemento("gold").textContent = jugador.oro;
  elemento("strength").textContent = jugador.fuerza;
  elemento("dexterity").textContent = jugador.destreza;
  elemento("constitution").textContent = jugador.constitucion;
  elemento("statPoints").textContent = jugador.puntos_estadistica;
  elemento("defense").textContent = jugador.armadura;
  elemento("attack").textContent = (
    `${jugador.ataque_minimo}–${jugador.ataque_maximo}`
  );
  elemento("speed").textContent = jugador.iniciativa;
  elemento("evasion").textContent = `${Math.round(jugador.evasion * 100)}%`;
  const penalizacionesPeso = [];
  if (jugador.penalizacion_evasion_peso > 0) {
    penalizacionesPeso.push(
      `EVA -${Math.round(jugador.penalizacion_evasion_peso * 100)}%`,
    );
  }
  if (jugador.modificador_movimiento_carga < 0) {
    penalizacionesPeso.push(`MOV ${jugador.modificador_movimiento_carga}`);
  }
  elemento("weight").textContent = (
    `${jugador.peso_equipado}/${jugador.capacidad_peso}`
  );
  const penalizacionPeso = elemento("weightPenalty");
  penalizacionPeso.textContent = penalizacionesPeso.join(" · ");
  penalizacionPeso.classList.toggle("hidden", penalizacionesPeso.length === 0);
  elemento("room").textContent = (
    `${estado.habitacion}/${estado.habitaciones_totales}`
  );
  renderizarEstadosActivos(jugador, estado.enemigo);
  renderizarHabilidades(jugador);
  renderizarInventario(jugador);
  renderizarEquipo(jugador);
  renderizarFichaPersonaje(jugador);
}


function renderizarEstadosActivos(jugador, enemigo) {
  const estados = [
    ...(jugador.estados_activos || []).map((efecto) => ({
      ...efecto,
      objetivo: "Tú",
    })),
    ...((enemigo?.estados_activos) || []).map((efecto) => ({
      ...efecto,
      objetivo: "Enemigo",
    })),
  ];
  const panel = elemento("statusPanel");
  panel.classList.remove("hidden");
  const tarjetas = estados.map((efecto) => {
    const tarjeta = document.createElement("article");
    const encabezado = document.createElement("div");
    const nombre = document.createElement("strong");
    const duracion = document.createElement("span");
    const descripcion = document.createElement("small");
    tarjeta.classList.add("status-effect", `status-${efecto.tipo}`);
    nombre.textContent = `${efecto.objetivo} · ${efecto.nombre}`;
    duracion.textContent = efecto.duracion;
    descripcion.textContent = efecto.descripcion;
    encabezado.append(nombre, duracion);
    tarjeta.append(encabezado, descripcion);
    return tarjeta;
  });
  if (tarjetas.length === 0) {
    const vacio = document.createElement("p");
    vacio.classList.add("status-empty");
    vacio.textContent = "Sin efectos activos.";
    tarjetas.push(vacio);
  }
  elemento("activeStatuses").replaceChildren(...tarjetas);
}


function renderizarHabilidades(jugador) {
  elemento("skillPoints").textContent = jugador.puntos_habilidad;
  const puedeMejorarAhora = !["menu", "inicio", "combate", "muerte", "fin"].includes(
    estado.fase,
  );
  const tarjetas = jugador.habilidades.map((habilidad) => {
    const tarjeta = document.createElement("article");
    const encabezado = document.createElement("div");
    const nombre = document.createElement("strong");
    const nivel = document.createElement("span");
    const detalle = document.createElement("small");
    const boton = document.createElement("button");
    nombre.textContent = habilidad.nombre;
    nivel.textContent = `${habilidad.nivel}/${habilidad.nivel_maximo}`;
    detalle.textContent = habilidad.activa
      ? `ACTIVA · ${habilidad.turnos_activos} turno(s) restante(s)`
      : `${habilidad.descripcion} Clase: ${jugador.clase_nombre}. `
        + `Coste: ${habilidad.costo_energia} de energía. `
        + `Cooldown: ${habilidad.cooldown_turnos} turnos.`;
    tarjeta.classList.toggle("skill-active-card", habilidad.activa);
    boton.textContent = habilidad.desbloqueada ? "Mejorar" : "Desbloquear";
    boton.disabled = (
      jugador.puntos_habilidad < 1
      || habilidad.nivel >= habilidad.nivel_maximo
      || !puedeMejorarAhora
    );
    boton.onclick = () => llamarApi("mejorar-habilidad", {
      habilidad: habilidad.id,
    });
    encabezado.append(nombre, nivel);
    tarjeta.append(encabezado, detalle, boton);
    return tarjeta;
  });
  if (!tarjetas.length) {
    const mensaje = document.createElement("p");
    mensaje.textContent = jugador.clase ? "El árbol de habilidades de esta clase aún no está disponible." : "Elige una clase al alcanzar el nivel 10 para acceder a sus habilidades cuando estén disponibles.";
    tarjetas.push(mensaje);
  }
  elemento("skillList").replaceChildren(...tarjetas);
}


function requisitosObjeto(requisitos = {}) {
  const nombres = {
    fuerza: "Fuerza",
    destreza: "Destreza",
    constitucion: "Constitución",
  };
  const valores = Object.entries(requisitos).map(
    ([atributo, valor]) => `${nombres[atributo] || atributo} ${valor}`,
  );
  return valores.length ? `Requiere ${valores.join(", ")}` : "Sin requisitos";
}



function descripcionObjeto(item) {
  const detalles = [];
  if (item.clase === "arma") {
    detalles.push(`Tier ${item.tier}`);
    detalles.push(`Daño ${item.ataque[0]}–${item.ataque[1]}`);
    detalles.push(item.dos_manos ? "Dos manos" : "Una mano");
    detalles.push(`Escala con Fuerza · coeficiente ${item.escalado_fuerza}`);
  } else if (item.clase === "secundario") {
    detalles.push(`Tier ${item.tier}`);
    detalles.push(`${Math.round(item.absorcion_pasiva * 100)}% de absorción pasiva`);
    detalles.push(
      `Bloquea ${Math.round(item.bloqueo_activo * 100)}% del daño`,
    );
    detalles.push(`Peso ${item.peso} kg`);
    detalles.push(`Durabilidad ${item.durabilidad}`);
  } else if (item.clase === "armadura") {
    detalles.push(`${item.defensa} de armadura`);
    detalles.push(`Slot ${item.slot}`);
    detalles.push(`Peso ${item.peso} kg`);
    detalles.push(`Durabilidad ${item.durabilidad}`);
  } else if (item.clase === "consumible") {
    detalles.push(`Recupera ${item.valor || item.salud} de vida`);
  } else if (item.descripcion) {
    detalles.push(item.descripcion);
  }
  if (item.requisitos) detalles.push(requisitosObjeto(item.requisitos));
  return detalles.join(" · ");
}


function obtenerTituloDelEncuentro(enemigo) {
  if (estado.jugador?.hp <= 0) return "Has muerto";
  const titulos = {
    combate: enemigo?.nombre,
    nivel: "Una decisión importante",
    transicion: enemigo ? "Victoria" : "El camino continúa",
    muerte: "Has muerto",
    fin: estado.resultado === "victoria"
      ? "Has escapado"
      : "Tu expedición termina",
  };
  return titulos[estado.fase] || "Explorando…";
}


function obtenerDescripcionDelEncuentro(enemigo) {
  if (estado.jugador?.hp <= 0) {
    return "La expedición termina aquí, pero tu aventurero conserva su progreso.";
  }
  if (estado.fase === "combate") {
    const intencion = enemigo.intencion || "normal";
    if (intencion.startsWith("habilidad:")) {
      return `El ${enemigo.nombre} prepara ${intencion.split(":")[1]}.`;
    }
    if (intencion === "poderoso") {
      return `El ${enemigo.nombre} prepara un ataque poderoso: daño ×1.5, presión ×1.25. Actúas primero y no podrá repetirlo en su siguiente ataque.`;
    }
    return `El ${enemigo.nombre} prepara un ataque ${intencion}.`;
  }
  if (estado.fase === "nivel") {
    return "Elige cómo quieres desarrollar tu personaje.";
  }
  if (estado.fase === "muerte") {
    return "La expedición termina aquí, pero tu aventurero conserva su progreso.";
  }
  if (estado.fase === "fin") {
    return estado.resultado === "victoria"
      ? "Encontraste la salida del calabozo."
      : "Has caído en el calabozo.";
  }
  return "La habitación está despejada.";
}


function renderizarEncuentro() {
  const enemigo = estado.enemigo;
  for (const [id, modelo] of [["playerShield", estado.jugador], ["enemyShield", enemigo]]) {
    let indicador = document.getElementById(id);
    if (!indicador) {
      indicador = document.createElement("label"); indicador.id = id;
      elemento("intent").parentElement.append(indicador);
    }
    indicador.hidden = !modelo?.durabilidad_maxima_escudo;
    if (!indicador.hidden) {
      const valor = Number(modelo.durabilidad_escudo.toFixed(1));
      indicador.textContent = `Escudo de ${modelo.nombre}: ${valor} / ${modelo.durabilidad_maxima_escudo}${valor === 0 ? " · Roto" : ""} `;
      const barra = document.createElement("progress"); barra.max = modelo.durabilidad_maxima_escudo; barra.value = valor;
      barra.setAttribute("aria-label", `Durabilidad del escudo de ${modelo.nombre}`); indicador.append(barra);
    }
  }
  elemento("enemyHealth").classList.toggle("hidden", !enemigo);

  if (enemigo) {
    elemento("enemyHpText").textContent = (
      `${enemigo.hp}/${enemigo.hp_maxima}`
    );
    elemento("enemyHpBar").style.width = porcentaje(
      enemigo.hp,
      enemigo.hp_maxima,
    );
  }

  elemento("encounterTitle").textContent = obtenerTituloDelEncuentro(enemigo);
  elemento("phaseLabel").textContent = estado.fase === "combate"
    ? "ENCUENTRO"
    : estado.fase.toUpperCase();
  elemento("intent").textContent = obtenerDescripcionDelEncuentro(enemigo);
}


function agregarAccionesDeCombate(jugador) {
  const [danoMinimo, danoMaximo] = jugador.ataque_arma;
  crearBoton(
    "Atacar · +1 energía",
    () => llamarApi("accion", { accion: "atacar" }),
    {
      tooltip: `Ataque normal: daño base ${jugador.dano_base} + arma `
        + `${danoMinimo}–${danoMaximo}. Recupera 1 de energía. `
        + "El enemigo puede evadir.",
    },
  );
  crearBoton(
    "Defender · +1 energía",
    () => llamarApi("accion", { accion: "defender" }),
    {
      tooltip: "Parada con arma: reduce 50%, 25% o 10% según su poder frente al ataque. Una parada completa hace perder la siguiente acción al rival. Con escudo usa bloqueo activo. Recupera 1 energía; los rápidos evitan la defensa activa.",
    },
  );
  for (const habilidad of jugador.habilidades) {
    const bloqueada = !habilidad.desbloqueada;
    const requisitoIncumplido = !habilidad.cumple_requisito;
    const sinEnergia = jugador.energia < habilidad.costo_energia;
    const enCooldown = habilidad.cooldown > 0;
    const activa = habilidad.activa;
    const motivos = [];
    if (bloqueada) motivos.push("habilidad bloqueada");
    if (requisitoIncumplido) motivos.push("requiere una habilidad aprendida de tu clase");
    if (sinEnergia) motivos.push("energía insuficiente");
    if (enCooldown) motivos.push(`cooldown: ${habilidad.cooldown} turno(s)`);
    if (activa) {
      motivos.push(`activa durante ${habilidad.turnos_activos} turno(s)`);
    }
    crearBoton(
      `${habilidad.nombre} · Nv ${habilidad.nivel}/${habilidad.nivel_maximo}`
        + (activa ? ` · ACTIVA ${habilidad.turnos_activos}` : ""),
      () => llamarApi("accion", {
        accion: "habilidad",
        habilidad: habilidad.id,
      }),
      {
        primario: habilidad.cumple_requisito && habilidad.desbloqueada,
        activo: activa,
        deshabilitado: bloqueada
          || requisitoIncumplido
          || sinEnergia
          || enCooldown
          || activa,
        tooltip: motivos.length
          ? motivos.join(" · ")
          : `${habilidad.descripcion} Coste: ${habilidad.costo_energia} de `
            + `energía. Cooldown: ${habilidad.cooldown_turnos} turnos.`,
      },
    );
  }
}


function agregarAccionesDeNivel() {
  if (estado.jugador.puntos_estadistica < 1) return;
  crearBoton(
    "+1 Fuerza",
    () => llamarApi("nivel", { estadistica: "fuerza" }),
    { tooltip: "Aumenta el daño de Espadas, Mazas y Morning Star." },
  );
  crearBoton(
    "+1 Destreza",
    () => llamarApi("nivel", { estadistica: "destreza" }),
    {
      primario: true,
      tooltip: "Aumenta el daño de Dagas y Estoques, además de Velocidad y Evasión.",
    },
  );
  crearBoton(
    "+1 Constitución · resistencia y regeneración",
    () => llamarApi("nivel", { estadistica: "constitucion" }),
    {
      tooltip: "Mejora Estabilidad, Resistencia Física y Regeneración.",
    },
  );
}


function renderizarAcciones() {
  elemento("actions").replaceChildren();
  const jugador = estado.jugador;
  if (jugador?.clase_pendiente && ["nivel", "transicion"].includes(estado.fase)) {
    for (const [id, clase] of Object.entries(estado.clases)) {
      crearBoton(`Elegir ${clase.nombre}`, () => llamarApi("clase", {clase: id}), {primario: true});
    }
  }

  if (estado.fase === "combate") {
    agregarAccionesDeCombate(jugador);
  } else if (estado.fase === "nivel") {
    agregarAccionesDeNivel();
  } else if (estado.fase === "transicion") {
    crearBoton(
      "Siguiente habitación",
      () => llamarApi("continuar"),
      { primario: true, completo: true },
    );

  } else if (estado.fase === "muerte" || jugador?.hp <= 0) {
    crearBoton(
      "Renacer en la habitación 1",
      () => llamarApi("respawn"),
      { primario: true, completo: true },
    );
    crearBoton(
      "Salir al menú principal",
      salirAlMenuPrincipal,
      { completo: true },
    );
  } else if (estado.fase === "fin") {
    crearBoton(
      "Volver al menú",
      salirAlMenuPrincipal,
      { primario: true, completo: true },
    );
  }
}


function renderizarRegistro() {
  const registro = elemento("log");
  const mensajes = estado.registro.slice(-14).map((mensaje) => {
    const parrafo = document.createElement("p");
    const evento = mensaje.match(/^\[\[([a-z_]+)\]\]\s*/);
    if (evento) {
      parrafo.classList.add(`log-event-${evento[1]}`);
      parrafo.textContent = mensaje.slice(evento[0].length);
    } else {
      parrafo.textContent = mensaje;
    }
    return parrafo;
  });

  registro.replaceChildren(...mensajes);
  registro.scrollTop = registro.scrollHeight;
}


function renderizar() {
  if (!estado) {
    return;
  }
  ocultarTooltip();
  if (estado.fase === "menu") {
    renderizarMenu();
    return;
  }
  elemento("menu").classList.add("hidden");
  if (estado.fase === "inicio") {
    elemento("pauseButton").classList.add("hidden");
    elemento("characterButton").classList.add("hidden");
    cerrarColeccion();
    renderizarInicio();
    return;
  }

  elemento("start").classList.add("hidden");
  elemento("game").classList.remove("hidden");
  elemento("game").classList.toggle("death-transition", estado.fase === "muerte");
  elemento("roomBadge").classList.remove("hidden");
  elemento("pauseButton").classList.remove("hidden");
  elemento("characterButton").classList.remove("hidden");
  renderizarPanel(estado.jugador);
  renderizarEncuentro();
  renderizarAcciones();
  renderizarRegistro();
}


elemento("startButton").onclick = () => {
  llamarApi("iniciar", {nombre: elemento("name").value});
};

elemento("cancelCreationButton").onclick = salirAlMenuPrincipal;


elemento("tacticalButton").onclick = () => { window.location.href = "/tactical.html"; };
elemento("newButton").onclick = () => llamarApi("nueva");
elemento("loadButton").onclick = () => mostrarSlots("cargar", true);
elemento("pauseButton").onclick = abrirPausa;
elemento("characterButton").onclick = () => abrirColeccion();
elemento("closeCollectionButton").onclick = cerrarColeccion;
elemento("resumeButton").onclick = cerrarPausa;
elemento("mainMenuButton").onclick = salirAlMenuPrincipal;
elemento("exitButton").onclick = async () => {
  try {
    await fetch("/api/salir", { method: "POST", body: "{}" });
    elemento("menuMessage").textContent = "Dungeon se ha cerrado. Ya puedes cerrar esta ventana.";
  } catch {
    elemento("menuMessage").textContent = "Dungeon ya no está en ejecución.";
  }
};


elemento("name").addEventListener("keydown", (evento) => {
  if (evento.key === "Enter") {
    elemento("startButton").click();
  }
});

document.addEventListener("keydown", (evento) => {
  if (coleccionAbierta && evento.key === "Tab") {
    const botones = [...elemento("collectionPanel").querySelectorAll('button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex="0"]')].filter(n => n.tabIndex !== -1 && n.getClientRects().length);
    const primero = botones[0], ultimo = botones[botones.length - 1];
    if (!primero) { evento.preventDefault(); elemento("collectionPanel").focus(); }
    else if (evento.shiftKey && (document.activeElement === primero || !elemento("collectionPanel").contains(document.activeElement))) { evento.preventDefault(); ultimo.focus(); }
    else if (!evento.shiftKey && (document.activeElement === ultimo || !elemento("collectionPanel").contains(document.activeElement))) { evento.preventDefault(); primero.focus(); }
    return;
  }
  if (evento.key !== "Escape") return;
  if (estado?.fase === "inicio") salirAlMenuPrincipal();
  else if (coleccionAbierta) cerrarColeccion();
  else if (menuPausaAbierto) cerrarPausa();
  else if (estado?.jugador && !["menu", "inicio"].includes(estado.fase)) abrirPausa();
});


fetch("/api/estado")
  .then((respuesta) => respuesta.json())
  .then((nuevoEstado) => {
    if (!validarVersion(nuevoEstado)) return;
    estado = nuevoEstado;
    renderizar();
  })
  .catch(() => {
    elemento("error").textContent = "No se pudo conectar con el servidor.";
  });
