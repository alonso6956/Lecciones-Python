// Atajo para buscar un elemento del HTML por su id.
const elemento = (id) => document.getElementById(id);
const UI_VERSION = "20";

// Última copia del estado enviada por Python.
let estado = null;
let menuPausaAbierto = false;
let modoSlots = null;
let coleccionAbierta = null;
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


function formatearFecha(fecha) {
  if (!fecha) return "Fecha desconocida";
  return new Date(fecha).toLocaleString("es-PE", {
    dateStyle: "short",
    timeStyle: "short",
  });
}


function mostrarAccionesPausa() {
  modoSlots = null;
  elemento("pauseTitle").textContent = "Menú de pausa";
  elemento("pauseActions").classList.remove("hidden");
  elemento("slotPanel").classList.add("hidden");
  elemento("pauseMessage").textContent = estado.slot_activo
    ? `Guardado automático activo en el slot ${estado.slot_activo}.`
    : "Selecciona Guardar partida para activar un slot.";
}


function crearBotonSlot(datosSlot) {
  const boton = document.createElement("button");
  const titulo = document.createElement("strong");
  const resumen = document.createElement("span");
  const fecha = document.createElement("small");
  boton.className = "slot-button";
  if (datosSlot.slot === estado.slot_activo) boton.classList.add("active");
  titulo.textContent = `S${datosSlot.slot}`;

  if (datosSlot.ocupado) {
    const datos = datosSlot.resumen;
    resumen.textContent = (
      `${datos.personaje} · Nivel ${datos.nivel} · Habitación ${datos.habitacion}`
    );
    fecha.textContent = formatearFecha(datos.fecha);
  } else {
    resumen.textContent = datosSlot.error || "Slot vacío";
    fecha.textContent = modoSlots === "guardar" ? "Disponible para guardar" : "";
  }

  boton.append(titulo, resumen, fecha);
  boton.disabled = modoSlots === "cargar" && !datosSlot.ocupado;
  boton.onclick = async () => {
    if (
      modoSlots === "guardar"
      && datosSlot.ocupado
      && !window.confirm(`¿Sobrescribir el slot ${datosSlot.slot}?`)
    ) return;

    const operacion = modoSlots;
    const correcto = await llamarApi(operacion, { slot: datosSlot.slot });
    if (!correcto) return;
    if (operacion === "guardar") {
      menuPausaAbierto = true;
      mostrarAccionesPausa();
    } else {
      cerrarPausa();
    }
  };
  return boton;
}


function mostrarSlots(modo, desdeMenu = false) {
  modoSlots = modo;
  menuPausaAbierto = true;
  elemento("pauseOverlay").classList.remove("hidden");
  elemento("pauseActions").classList.add("hidden");
  elemento("slotPanel").classList.remove("hidden");
  elemento("pauseTitle").textContent = modo === "guardar"
    ? "Guardar partida"
    : "Cargar partida";
  elemento("slotHelp").textContent = modo === "guardar"
    ? "Elige dónde guardar. Un slot ocupado pedirá confirmación."
    : "Elige una partida para continuar.";
  elemento("slotList").replaceChildren(...estado.slots.map(crearBotonSlot));
  elemento("backPauseButton").onclick = () => {
    if (desdeMenu) cerrarPausa();
    else mostrarAccionesPausa();
  };
  elemento("pauseMessage").textContent = "";
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


function abrirColeccion(tipo) {
  coleccionAbierta = tipo;
  const titulos = {
    habilidades: "Habilidades",
    inventario: "Inventario",
    equipo: "Equipamiento activo",
  };
  elemento("collectionTitle").textContent = titulos[tipo];
  elemento("skillsPanel").classList.toggle("hidden", tipo !== "habilidades");
  elemento("inventoryPanel").classList.toggle("hidden", tipo !== "inventario");
  elemento("equipmentPanel").classList.toggle("hidden", tipo !== "equipo");
  elemento("collectionOverlay").classList.remove("hidden");
}


function cerrarColeccion() {
  coleccionAbierta = null;
  elemento("collectionOverlay").classList.add("hidden");
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

  const tarjetas = estado.armas_iniciales.map((arma, indice) => {
    const seleccionada = indice === 0 ? "checked" : "";
    return `
      <label class="weapon">
        <input
          type="radio"
          name="weapon"
          value="${arma.nombre}"
          ${seleccionada}
        >
        <article>
          <h3>${arma.nombre}</h3>
          <p>
            Daño <b>${arma.ataque[0]}–${arma.ataque[1]}</b>
          </p>
          <p>
            Escala con ${arma.tipo === "daga" ? "Destreza" : "Fuerza"}
            · ${arma.dos_manos ? "Dos manos" : "Una mano"}.
          </p>
        </article>
      </label>
    `;
  });

  elemento("weapons").innerHTML = tarjetas.join("");
}


function renderizarMenu() {
  elemento("menu").classList.remove("hidden");
  elemento("start").classList.add("hidden");
  elemento("game").classList.add("hidden");
  elemento("roomBadge").classList.add("hidden");
  elemento("pauseButton").classList.add("hidden");
  elemento("skillsButton").classList.add("hidden");
  elemento("inventoryButton").classList.add("hidden");
  elemento("equipmentButton").classList.add("hidden");
  cerrarColeccion();
  elemento("loadButton").disabled = !estado.guardado_disponible;
}


function renderizarPanel(jugador) {
  elemento("playerName").textContent = jugador.nombre;
  elemento("weaponName").textContent = jugador.arma;
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
  elemento("level").textContent = `${jugador.nivel}/${jugador.nivel_maximo}`;
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
  elemento("speed").textContent = jugador.velocidad;
  elemento("evasion").textContent = `${Math.round(jugador.evasion * 100)}%`;
  const penalizacionesPeso = [];
  if (jugador.penalizacion_evasion_peso > 0) {
    penalizacionesPeso.push(
      `EVA -${Math.round(jugador.penalizacion_evasion_peso * 100)}%`,
    );
  }
  if (jugador.penalizacion_velocidad_peso > 0) {
    penalizacionesPeso.push(`VEL -${jugador.penalizacion_velocidad_peso}`);
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
  const puedeMejorarAhora = !["menu", "inicio", "combate", "fin"].includes(
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
      : `${habilidad.descripcion} Requiere ${habilidad.arma_requerida}. `
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


function descripcionPasiva(pasiva) {
  if (!pasiva) return "Sin pasiva";
  if (pasiva.efecto === "critico") {
    return `Pasiva ${pasiva.nombre}: ${Math.round(pasiva.probabilidad * 100)}% `
      + "de probabilidad de golpe crítico";
  }
  if (pasiva.efecto === "ignorar_defensa") {
    return `Pasiva ${pasiva.nombre}: ${Math.round(pasiva.probabilidad * 100)}% `
      + "de ignorar armadura y escudo";
  }
  if (pasiva.efecto === "doble_ataque_sangrado") {
    return `Pasiva ${pasiva.nombre}: ${pasiva.numero_ataques} ataques; `
      + `${pasiva.dano_sangrado} de sangrado por impacto`;
  }
  return `Pasiva ${pasiva.nombre}: ${pasiva.descripcion}`;
}


function descripcionObjeto(item) {
  const detalles = [];
  if (item.clase === "arma") {
    detalles.push(`Tier ${item.tier}`);
    detalles.push(`Daño ${item.ataque[0]}–${item.ataque[1]}`);
    detalles.push(item.dos_manos ? "Dos manos" : "Una mano");
    const atributo = item.estadistica_escalado === "destreza"
      ? "Destreza"
      : "Fuerza";
    detalles.push(
      `Escala con ${atributo}: +${Math.round(item.crecimiento_por_punto * 100)}% por punto`,
    );
    detalles.push(descripcionPasiva(item.pasiva));
  } else if (item.clase === "secundario") {
    detalles.push(`Tier ${item.tier}`);
    detalles.push(`${Math.round(item.probabilidad_bloqueo * 100)}% de bloqueo`);
    detalles.push(
      `Bloquea ${Math.round(item.porcentaje_dano_bloqueado * 100)}% del daño`,
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


function renderizarInventario(jugador) {
  const puedeGestionar = !["menu", "inicio", "combate", "fin"].includes(
    estado.fase,
  );
  const puedeUsarConsumible = !["menu", "inicio", "fin"].includes(estado.fase);
  const filas = jugador.inventario.map((item) => {
    const fila = document.createElement("article");
    const informacion = document.createElement("div");
    const nombre = document.createElement("strong");
    const detalle = document.createElement("small");
    const boton = document.createElement("button");
    nombre.textContent = `${item.nombre} ×${item.cantidad}`;
    detalle.textContent = descripcionObjeto(item);
    informacion.append(nombre, detalle);
    if (["arma", "secundario", "armadura"].includes(item.clase)) {
      boton.textContent = item.equipado ? "Equipado" : "Equipar";
      boton.disabled = item.equipado || !puedeGestionar || !item.puede_equipar;
      if (!item.puede_equipar) boton.title = "No cumples los requisitos";
      boton.onclick = () => llamarApi("equipar", { item: item.id });
    } else if (item.clase === "consumible") {
      boton.textContent = estado.fase === "combate" ? "Usar (acción)" : "Usar";
      boton.disabled = !puedeUsarConsumible || jugador.hp >= jugador.salud_maxima;
      boton.onclick = () => llamarApi("usar-item", { item: item.id });
    } else {
      boton.textContent = "Material";
      boton.disabled = true;
    }
    fila.append(informacion, boton);
    return fila;
  });
  elemento("inventoryList").replaceChildren(...filas);
}


function renderizarEquipo(jugador) {
  const nombresSlot = {
    mano_principal: "Mano principal",
    mano_secundaria: "Mano secundaria",
    casco: "Casco",
    pecho: "Pecho",
    brazos: "Brazos",
    piernas: "Piernas",
  };
  const puedeGestionar = !["menu", "inicio", "combate", "fin"].includes(
    estado.fase,
  );
  elemento("equipmentDefense").textContent = (
    jugador.armadura_equipo
  );

  const filas = Object.entries(nombresSlot).map(([slot, etiqueta]) => {
    const actual = jugador.equipamiento[slot];
    const fila = document.createElement("article");
    const texto = document.createElement("div");
    const titulo = document.createElement("strong");
    const detalle = document.createElement("small");
    const selector = document.createElement("select");
    const desequipar = document.createElement("button");
    titulo.textContent = etiqueta;
    if (!actual) {
      detalle.textContent = "Vacío";
    } else if (actual.clase === "armadura") {
      detalle.textContent = (
        `${actual.nombre} · ${actual.defensa} de armadura`
      );
    } else {
      detalle.textContent = actual.nombre;
    }
    texto.append(titulo, detalle);

    const candidatos = jugador.inventario.filter((item) => item.slot === slot);
    if (!actual && candidatos.length) {
      const opcionVacia = document.createElement("option");
      opcionVacia.value = "";
      opcionVacia.textContent = "Elegir objeto…";
      opcionVacia.selected = true;
      selector.appendChild(opcionVacia);
    }
    for (const item of candidatos) {
      const opcion = document.createElement("option");
      opcion.value = item.id;
      opcion.textContent = item.nombre;
      opcion.selected = actual?.id === item.id;
      opcion.disabled = !item.puede_equipar;
      selector.appendChild(opcion);
    }
    if (!candidatos.length) {
      const opcion = document.createElement("option");
      opcion.textContent = "Sin objetos disponibles";
      selector.appendChild(opcion);
    }
    selector.disabled = !puedeGestionar || candidatos.length < 1;
    selector.onchange = () => {
      if (selector.value) llamarApi("equipar", { item: selector.value });
    };

    desequipar.textContent = "Desequipar";
    desequipar.disabled = !puedeGestionar || !actual || slot === "mano_principal";
    desequipar.title = slot === "mano_principal"
      ? "La mano principal debe conservar un arma"
      : "";
    desequipar.onclick = () => llamarApi("desequipar", { slot });
    fila.append(texto, selector, desequipar);
    return fila;
  });
  elemento("equipmentList").replaceChildren(...filas);
}


function obtenerTituloDelEncuentro(enemigo) {
  if (estado.jugador?.hp <= 0) return "Has muerto";
  const titulos = {
    combate: enemigo?.nombre,
    nivel: "Una decisión importante",
    transicion: enemigo ? "Victoria" : "El camino continúa",
    tienda: "El mercader",
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
    return `El ${enemigo.nombre} prepara un ataque ${intencion}.`;
  }
  if (estado.fase === "nivel") {
    return "Elige cómo quieres desarrollar tu personaje.";
  }
  if (estado.fase === "tienda") {
    return "Gasta tu oro con cuidado; el camino aún es largo.";
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
      tooltip: "Duplica la armadura durante este turno y recupera 1 de energía.",
    },
  );
  for (const habilidad of jugador.habilidades) {
    const bloqueada = !habilidad.desbloqueada;
    const requisitoIncumplido = !habilidad.cumple_requisito;
    const armaIncorrecta = !habilidad.cumple_tipo_equipo;
    const manoSecundariaOcupada = (
      habilidad.requiere_mano_secundaria_libre
      && !habilidad.mano_secundaria_libre
    );
    const sinEnergia = jugador.energia < habilidad.costo_energia;
    const enCooldown = habilidad.cooldown > 0;
    const activa = habilidad.activa;
    const motivos = [];
    if (bloqueada) motivos.push("habilidad bloqueada");
    if (armaIncorrecta) motivos.push(`requiere ${habilidad.arma_requerida}`);
    if (manoSecundariaOcupada) motivos.push("requiere la mano secundaria libre");
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
    "+1 Constitución · vida y armadura",
    () => llamarApi("nivel", { estadistica: "constitucion" }),
    {
      tooltip: "Otorga +10 de vida máxima; cada 2 puntos de CON aportan armadura.",
    },
  );
}


function agregarAccionesDeTienda(jugador) {
  const categorias = [
    ["pociones", "POCIONES"],
    ["armas", "ARMAS"],
    ["secundarios", "MANO SECUNDARIA"],
    ["armaduras", "ARMADURAS"],
  ];

  for (const [categoria, etiqueta] of categorias) {
    const titulo = document.createElement("p");
    titulo.classList.add("shop-title");
    titulo.textContent = etiqueta;
    elemento("actions").appendChild(titulo);

    const productos = Object.entries(estado.tienda[categoria]);
    for (const [nombre, producto] of productos) {
      const clases = {
        armas: "arma",
        secundarios: "secundario",
        armaduras: "armadura",
        pociones: "consumible",
      };
      crearBoton(
        `${nombre} · ${producto.precio} oro`,
        () => llamarApi("comprar", { categoria, nombre }),
        {
          deshabilitado: jugador.oro < producto.precio,
          tooltip: descripcionObjeto({
            ...producto,
            clase: clases[categoria],
          }),
        },
      );
    }
  }

  crearBoton(
    "Salir de la tienda",
    () => llamarApi("continuar"),
    { primario: true, completo: true },
  );
}


function renderizarAcciones() {
  elemento("actions").replaceChildren();
  const jugador = estado.jugador;

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
  } else if (estado.fase === "tienda") {
    agregarAccionesDeTienda(jugador);
  } else if (estado.fase === "muerte" || jugador?.hp <= 0) {
    crearBoton(
      "Renacer en la habitación 1",
      () => llamarApi("respawn"),
      { primario: true, completo: true },
    );
    crearBoton(
      "Guardar antes de renacer",
      () => mostrarSlots("guardar"),
      { completo: true },
    );
    crearBoton(
      "Salir al menú principal",
      salirAlMenuPrincipal,
      { completo: true },
    );
  } else if (estado.fase === "fin") {
    crearBoton(
      "Nueva partida",
      () => llamarApi("nueva"),
      { primario: true, completo: true },
    );
    crearBoton(
      "Menú principal",
      () => llamarApi("reiniciar"),
      { completo: true },
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
    elemento("skillsButton").classList.add("hidden");
    elemento("inventoryButton").classList.add("hidden");
    elemento("equipmentButton").classList.add("hidden");
    cerrarColeccion();
    renderizarInicio();
    return;
  }

  elemento("start").classList.add("hidden");
  elemento("game").classList.remove("hidden");
  elemento("game").classList.toggle("death-transition", estado.fase === "muerte");
  elemento("roomBadge").classList.remove("hidden");
  elemento("pauseButton").classList.remove("hidden");
  elemento("skillsButton").classList.remove("hidden");
  elemento("inventoryButton").classList.remove("hidden");
  elemento("equipmentButton").classList.remove("hidden");
  renderizarPanel(estado.jugador);
  renderizarEncuentro();
  renderizarAcciones();
  renderizarRegistro();
}


elemento("startButton").onclick = () => {
  const armaSeleccionada = document.querySelector(
    'input[name="weapon"]:checked',
  );
  llamarApi("iniciar", {
    nombre: elemento("name").value,
    arma: armaSeleccionada?.value || "",
  });
};


elemento("newButton").onclick = () => llamarApi("nueva");
elemento("loadButton").onclick = () => mostrarSlots("cargar", true);
elemento("pauseButton").onclick = abrirPausa;
elemento("skillsButton").onclick = () => abrirColeccion("habilidades");
elemento("inventoryButton").onclick = () => abrirColeccion("inventario");
elemento("equipmentButton").onclick = () => abrirColeccion("equipo");
elemento("closeCollectionButton").onclick = cerrarColeccion;
elemento("resumeButton").onclick = cerrarPausa;
elemento("saveButton").onclick = () => mostrarSlots("guardar");
elemento("pauseLoadButton").onclick = () => mostrarSlots("cargar");
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
  if (evento.key !== "Escape") return;
  if (coleccionAbierta) cerrarColeccion();
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
