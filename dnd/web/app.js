// Atajo para buscar un elemento del HTML por su id.
const elemento = (id) => document.getElementById(id);

// Última copia del estado enviada por Python.
let estado = null;


async function llamarApi(ruta, datos = {}) {
  const respuesta = await fetch(`/api/${ruta}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  });
  const resultado = await respuesta.json();

  if (!respuesta.ok) {
    elemento("error").textContent = resultado.error;
    estado = resultado.estado;
    renderizar();
    return;
  }

  estado = resultado;
  elemento("error").textContent = "";
  renderizar();
}


function crearBoton(texto, manejador, opciones = {}) {
  const boton = document.createElement("button");
  boton.textContent = texto;
  boton.onclick = manejador;
  boton.disabled = opciones.deshabilitado || false;

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
            · Defensa <b>${arma.descripcion_defensa}</b>
          </p>
          <p>${arma.tecnica}: ${arma.descripcion_tecnica}</p>
        </article>
      </label>
    `;
  });

  elemento("weapons").innerHTML = tarjetas.join("");
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
    return `El ${enemigo.nombre} prepara un ataque ${enemigo.intencion}.`;
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
  crearBoton(
    "Atacar",
    () => llamarApi("accion", { accion: "atacar" }),
  );
  crearBoton(
    "Defender · +1 energía",
    () => llamarApi("accion", { accion: "defender" }),
  );
  crearBoton(
    `${jugador.tecnica} · −2 energía`,
    () => llamarApi("accion", { accion: "tecnica" }),
    { primario: true, deshabilitado: jugador.energia < 2 },
  );
}


function agregarAccionesDeNivel() {
  crearBoton(
    "+1 Fuerza",
    () => llamarApi("nivel", { estadistica: "fuerza" }),
  );
  crearBoton(
    "+1 Destreza",
    () => llamarApi("nivel", { estadistica: "destreza" }),
    { primario: true },
  );
  crearBoton(
    "+1 Constitución · +10 vida",
    () => llamarApi("nivel", { estadistica: "constitucion" }),
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
        { deshabilitado: jugador.oro < producto.precio },
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
      "Nueva expedición",
      () => llamarApi("reiniciar"),
      { primario: true, completo: true },
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
