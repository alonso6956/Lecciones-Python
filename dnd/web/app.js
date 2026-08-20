// Atajo para buscar un elemento del HTML por su id.
const elemento = (id) => document.getElementById(id);

// Última copia del estado enviada por Python.
let estado = null;


async function llamarApi(ruta, datos = {}) {
  let respuesta;
  let resultado;
  try {
    respuesta = await fetch(`/api/${ruta}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });
    resultado = await respuesta.json();
  } catch {
    const mensaje = "Se perdió la conexión con Dungeon. Reinicia la aplicación.";
    elemento("error").textContent = mensaje;
    elemento("menuMessage").textContent = mensaje;
    return;
  }

  if (!respuesta.ok) {
    elemento("error").textContent = resultado.error;
    elemento("menuMessage").textContent = resultado.error;
    estado = resultado.estado;
    renderizar();
    return;
  }

  estado = resultado;
  elemento("error").textContent = "";
  elemento("menuMessage").textContent = "";
  renderizar();
}


function crearBoton(texto, manejador, opciones = {}) {
  const boton = document.createElement("button");
  boton.textContent = texto;
  boton.onclick = manejador;
  boton.disabled = opciones.deshabilitado || false;

  if (opciones.tooltip) {
    boton.title = opciones.tooltip;
    boton.dataset.tooltip = opciones.tooltip;
    boton.setAttribute("aria-label", `${texto}. ${opciones.tooltip}`);
  }

  if (opciones.primario) {
    boton.classList.add("primary");
  }
  if (opciones.completo) {
    boton.classList.add("full");
  }

  elemento("actions").appendChild(boton);
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
            · Defensa fija <b>${arma.defensa}</b>
          </p>
          <p>${arma.tecnica}: ${arma.descripcion_tecnica}</p>
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
  elemento("level").textContent = jugador.nivel;
  elemento("exp").textContent = jugador.exp;
  elemento("gold").textContent = jugador.oro;
  elemento("strength").textContent = jugador.fuerza;
  elemento("dexterity").textContent = jugador.destreza;
  elemento("constitution").textContent = jugador.constitucion;
  elemento("defense").textContent = jugador.defensa;
  elemento("attack").textContent = (
    `${jugador.ataque_minimo}–${jugador.ataque_maximo}`
  );
  elemento("speed").textContent = jugador.velocidad;
  elemento("evasion").textContent = `${Math.round(jugador.evasion * 100)}%`;
  elemento("room").textContent = (
    `${estado.habitacion}/${estado.habitaciones_totales}`
  );
}


function obtenerTituloDelEncuentro(enemigo) {
  const titulos = {
    combate: enemigo?.nombre,
    nivel: "Una decisión importante",
    transicion: enemigo ? "Victoria" : "El camino continúa",
    tienda: "El mercader",
    fin: estado.resultado === "victoria"
      ? "Has escapado"
      : "Tu expedición termina",
  };
  return titulos[estado.fase] || "Explorando…";
}


function obtenerDescripcionDelEncuentro(enemigo) {
  if (estado.fase === "combate") {
    const intencion = enemigo.intencion || "normal";
    return `El ${enemigo.nombre} prepara un ataque ${intencion}.`;
  }
  if (estado.fase === "nivel") {
    return "Elige cómo quieres desarrollar tu personaje.";
  }
  if (estado.fase === "tienda") {
    return "Gasta tu oro con cuidado; el camino aún es largo.";
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
    "Atacar",
    () => llamarApi("accion", { accion: "atacar" }),
    {
      tooltip: `Ataque normal: daño base ${jugador.dano_base} + arma `
        + `${danoMinimo}–${danoMaximo}. El enemigo puede evadir.`,
    },
  );
  crearBoton(
    "Defender · +1 energía",
    () => llamarApi("accion", { accion: "defender" }),
    {
      tooltip: "Duplica la defensa durante este turno y recupera 1 de energía.",
    },
  );
  crearBoton(
    `${jugador.tecnica} · −2 energía`,
    () => llamarApi("accion", { accion: "tecnica" }),
    {
      primario: true,
      deshabilitado: jugador.energia < 2,
      tooltip: `${jugador.descripcion_tecnica}. Daño de habilidad ×1.5, `
        + "amortiguado por Defensa y Constitución enemigas. Coste: 2 energía.",
    },
  );
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
    "+1 Constitución · vida y defensa",
    () => llamarApi("nivel", { estadistica: "constitucion" }),
    {
      tooltip: "Otorga +10 de vida máxima; cada 2 puntos de CON aportan +1 Defensa.",
    },
  );
}


function agregarAccionesDeTienda(jugador) {
  const categorias = [
    ["pociones", "POCIONES"],
    ["armas", "ARMAS"],
  ];

  for (const [categoria, etiqueta] of categorias) {
    const titulo = document.createElement("p");
    titulo.classList.add("shop-title");
    titulo.textContent = etiqueta;
    elemento("actions").appendChild(titulo);

    const productos = Object.entries(estado.tienda[categoria]);
    for (const [nombre, producto] of productos) {
      crearBoton(
        `${nombre} · ${producto.precio} oro`,
        () => llamarApi("comprar", { categoria, nombre }),
        {
          deshabilitado: jugador.oro < producto.precio,
          tooltip: categoria === "pociones"
            ? `Recupera exactamente ${producto.salud} de vida.`
            : `Daño ${producto.ataque[0]}–${producto.ataque[1]}; defensa ${producto.defensa}.`,
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
    parrafo.textContent = mensaje;
    return parrafo;
  });

  registro.replaceChildren(...mensajes);
  registro.scrollTop = registro.scrollHeight;
}


function renderizar() {
  if (!estado) {
    return;
  }
  if (estado.fase === "menu") {
    renderizarMenu();
    return;
  }
  elemento("menu").classList.add("hidden");
  if (estado.fase === "inicio") {
    renderizarInicio();
    return;
  }

  elemento("start").classList.add("hidden");
  elemento("game").classList.remove("hidden");
  elemento("roomBadge").classList.remove("hidden");
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
elemento("loadButton").onclick = () => llamarApi("cargar");
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


fetch("/api/estado")
  .then((respuesta) => respuesta.json())
  .then((nuevoEstado) => {
    estado = nuevoEstado;
    renderizar();
  })
  .catch(() => {
    elemento("error").textContent = "No se pudo conectar con el servidor.";
  });
