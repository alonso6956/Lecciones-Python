# Dungeon: roster compartido y combate táctico

## Flujo jugable

1. **Crear personaje** solo pide un nombre. Asigna un ID único, nivel 1,
   estadísticas base a 1, espada básica equipada y ningún poder de arma.
2. **Elegir personaje** carga su último checkpoint y empieza la expedición
   en la habitación 1, con vida completa y sin estados temporales.
3. La creación guarda el checkpoint inicial. **Avanzar de habitación** y **morir**
   guardan nivel, EXP, oro, estadísticas, inventario y equipamiento.
   La tienda solo está en el menú: seleccionar personaje y comprar confirma el inventario inmediatamente.
   Ganar combates o subir de nivel se confirma al avanzar, o al morir.
4. Morir conserva la progresión permanente y devuelve al menú. Confirmar
   **Pausa → Salir al menú** descarta los cambios desde el último checkpoint.
   El personaje permanece en el roster y la siguiente expedición empieza en 1.
5. Al nivel **10**, elegir Guerrero, Pícaro o Guardián añade una etiqueta al
   perfil. Al nivel **30**, se manifiesta `chispa_latente`. El nivel máximo
   es 30. Ambas decisiones siguen las mismas reglas de checkpoint.
6. **Desafío táctico · Hasta 6 personajes** se habilita al tener tres personajes.
   La condición es el tamaño del roster; no se impone otro nivel mínimo.

La web y Godot consumen el mismo motor HTTP. Desde el menú de Godot, el botón
Desafío táctico abre el cliente web del mismo servidor de desarrollo.

## Preparación y combate táctico

Se seleccionan de tres a seis personajes distintos del roster. Cada uno aporta nombre, nivel, estadísticas y equipo desde
su último checkpoint. Solo se pueden elegir armas que ese personaje posee y
cuyos requisitos cumple. El inventario de otro personaje no concede acceso.

Se conservan las builds Ofensiva (+20% ataque y +1 velocidad) y Adaptación
(65% resistencia al sangrado y +25% ruptura), las prioridades de IA, el combate
automático, el jefe con sangrado/escudo y los diagnósticos de derrota.

Las armas tienen daño, escalado y propiedades físicas; no conceden técnicas,
habilidades ni pasivas. Los árboles de clase/chispa aún están vacíos: elegir
clase no altera estadísticas ni habilita poderes. La IA del roster usa ataques
básicos y las maniobras de campo seleccionadas hasta que se conecten esos árboles. Las reglas futuras de prioridad
solo podrán ejecutar habilidades disponibles para el personaje.

Cada intento trabaja con copias. El daño, los estados y los cambios de
preparación táctica no modifican el roster ni guardan progresión del calabozo.
Recargar la página conserva el combate en memoria; reiniciar el servidor
restablece la preparación. El servidor calcula una ronda por solicitud
`/api/tactico/avanzar`; el navegador las solicita automáticamente.

### Despliegue y campo de batalla

El tablero tiene **10 columnas (A–J) y 8 filas (1–8)**. Admite hasta seis aliados y al guardián. Este encuentro conserva un solo rival y sus estadísticas; añadir aliados reduce la dificultad, sin escalar automáticamente la vida del jefe.

1. Usa **Añadir personaje** o **Quitar último personaje** para ajustar el grupo entre 3 y 6. Selecciona sus armas y una maniobra de campo por personaje.
2. En el tablero, elige una ficha o un personaje en el selector y pulsa una casilla libre. Los aliados se despliegan en A–C y el guardián en H–J. Las flechas permiten recorrer el tablero con teclado.
3. Selecciona una herramienta para pintar el terreno. **Suelo / borrar** elimina el terreno de una casilla; **Limpiar terreno** conserva el despliegue y elimina todas las modificaciones. Se rechazan posiciones duplicadas, casillas fuera del tablero y campos que corten todas las rutas al guardián.
4. Inicia el combate. Las fichas muestran número de personaje, nombre y vida, y resaltan cada actor durante su acción. Puedes inspeccionar las casillas, pausar entre rondas o avanzar una ronda. El ritmo controla la reproducción y el intervalo entre rondas.
5. **Reajustar** recupera el despliegue y terreno originales, la vida completa y las maniobras disponibles. El terreno se conserva entre reintentos y recargas de página mientras el servidor siga abierto; no se guarda en disco.

| Terreno | Efecto | Límite inicial |
| --- | --- | --- |
| Obstáculo | Bloquea paso y línea de visión. Solo columnas D–G. | 10 |
| Cobertura | Reduce un 20 % el daño directo recibido en esa casilla. | 8 |
| Elevación | Cuesta 2 puntos entrar; +15 % de daño hacia suelo bajo y −15 % al atacar hacia arriba. | 6 |
| Barro | Cuesta 2 puntos entrar. | 8 |
| Trampa aliada | Al pisarla el rival: 12 de daño, detención del movimiento y consumo. Solo D–G. | 3 |
| Trampa rival | Al pisarla un aliado: mismo efecto. Solo D–G. | 3 |

El movimiento es ortogonal, con **2–4 puntos por acción** según `velocidad / 4`, truncada y acotada. El motor busca una ruta de menor coste evitando unidades vivas y obstáculos. Los caídos dejan de bloquear el paso. Tras moverse se puede atacar si el objetivo queda al alcance del arma y con línea de visión; de lo contrario, la acción se dedica a aproximarse. Una trampa impide seguir moviéndose hasta terminar la siguiente ronda, pero no impide atacar a un objetivo que ya esté al alcance.

La lanza fabricada puede atacar desde dos casillas; el resto conserva el alcance definido en su objeto. El guardián busca al aliado accesible más cercano por coste de ruta. El sangrado de su ataque afecta solo a aliados a distancia 2 y con visión. El castigo por fallar la ruptura de escudo sigue siendo global. Las futuras curaciones/limpiezas tienen alcance 3 y Muralla afecta a aliados a distancia 2.

Dos aliados adyacentes en lados opuestos del guardián obtienen **+15 % de daño por flanqueo**. Altura, cobertura, humo y flanqueo se aplican multiplicativamente al daño directo antes de la mitigación normal. No alteran los ticks de sangrado ni el daño fijo de trampas.

### Maniobras de campo

Cada personaje puede elegir una maniobra independiente de los árboles de clase. La IA la usa **una vez por combate**, cuando el guardián está a cuatro casillas o menos; consume su acción de ese turno. Si no hay una casilla válida, continúa con su acción normal y podrá intentarlo después.

- **Cortina de humo:** genera humo en la casilla del actor y sus vecinas transitables. Reduce el daño directo recibido un 25 %, para ambos bandos, hasta el final de la ronda actual + 2.
- **Fortificar posición:** convierte el suelo de su casilla en cobertura durante el resto del combate. No reemplaza otros terrenos.
- **Tender trampa:** crea una trampa aliada en suelo libre y visible a distancia máxima 3 del actor, priorizando la cercanía al guardián. Las trampas no desaparecen al morir quien las colocó.
- **Sin maniobra:** no reserva acciones para modificar el campo.

Las maniobras no gastan consumibles ni oro del personaje y no entregan recompensas. Son recursos limitados del intento táctico. Sus cambios de terreno pueden superar los límites del editor inicial.

## Ejecutar

```powershell
$env:DUNGEON_ENV = "development"
.\.venv\Scripts\python.exe -B main.py
```

Desarrollo: `http://127.0.0.1:8000`. Producción: puerto 8765.
El cliente táctico está en `/tactical.html`. Visitarlo directamente tampoco
permite iniciar con menos de tres personajes: la API valida el bloqueo.

## Arquitectura y persistencia

| Archivo | Responsabilidad |
| --- | --- |
| `character_roster.py` | Lista de personajes persistentes, copias, validación y migración de slots. |
| `progression.py` | Catálogo de etiquetas y ganchos para hitos y árboles futuros. |
| `character.py` | Estadísticas, nivel, clase, chispa y habilidades de clase. |
| `persistence.py` | Envoltorio JSON con checksum, respaldo y reemplazo atómico. |
| `game_engine.py` | Estado volátil de expedición; guarda al avanzar de habitación o morir y descarta cambios al abandonar. |
| `state.py` | Contrato público compartido por la web y Godot. |
| `tactical_models.py` | Validación de selecciones y adaptación del personaje al combate táctico. |
| `tactical_ai.py`, `tactical_combat.py` | Prioridades disponibles, rondas, estados y resolución. |
| `tactical_controller.py` | Bloqueo del roster, preparación y reintentos. |
| `tactical_board.py` | Validación del despliegue/terreno, rutas, visión, altura, cobertura y catálogo de maniobras. |
| `web/tactical-board.js`, `web/tactical-board.css` | Editor del campo, inspección de casillas y reproducción visual de acciones. |
| `tactical_diagnostics.py` | Diagnóstico según daño efectivo recibido. |
| `server.py` | Instancia compartida del roster y serialización de solicitudes. |

El archivo `roster.json` contiene `state.roster`, una lista de diccionarios con
`id`, `nombre`, `nivel`, `arma_equipada`, `estadisticas`, `clase`, `chispa`,
`inventario`, `equipamiento`, `exp`, `oro`, puntos y habilidades aprendidas.
No contiene habitación, HP, enemigos, cooldowns ni buffs. Existe un respaldo
`roster.backup.json`. Ver [PRODUCTION.md](PRODUCTION.md) para las ubicaciones.

Si no existe el roster, se importan los slots antiguos conservando los
originales. Se descarta el estado de combate y se reembolsan como puntos los
niveles de habilidades de arma. Los errores de importación se muestran en el
menú. El primer guardado nuevo confirma todos los personajes importados.

## API

| Ruta | Uso |
| --- | --- |
| `GET /api/estado` | Estado del calabozo, roster, clases y disponibilidad táctica. |
| `POST /api/nueva` | Abre la creación desde el menú. |
| `POST /api/iniciar` | Crea con `{nombre}` y entra en habitación 1. |
| `POST /api/cargar` | Selecciona `{id}`; `{slot}` se conserva como adaptador para Godot. |
| `POST /api/clase` | Elige `{clase}` cuando se alcanza nivel 10. |
| `POST /api/continuar` | Avanza desde una habitación superada y confirma primero el checkpoint. |
| `GET /api/tienda/estado?personaje_id=...` | Catálogo, oro e inventario del personaje seleccionado. |
| `POST /api/tienda/comprar` | Compra `{personaje_id, categoria, nombre, cantidad}` solo desde el menú. |
| `POST /api/reiniciar` | Abandona sin escribir en disco. |
| `POST /api/guardar` | Rechazado: el guardado es automático al avanzar de habitación o morir. |
| `GET /api/tactico/estado` | Preparación, catálogo del roster y bloqueo. |
| `POST /api/tactico/preparar` | De 3 a 6 selecciones: personaje, build, arma, prioridad y `maniobra` opcional. |
| `POST /api/tactico/campo` | `{tablero: {posiciones: {id: [x, y]}, celdas: [{x, y, tipo}]}}`; coordenadas desde cero, solo durante preparación. No envía casillas de suelo. |
| `POST /api/tactico/iniciar` | Inicia con `{seed}`; valida party y propiedad del equipo. |
| `POST /api/tactico/avanzar` | Resuelve una ronda; `reproduccion` contiene instantáneas de movimiento y acciones de esa ronda. |
| `POST /api/tactico/reajustar` | Vuelve a preparación tras el resultado. |

## Validación y simulador aislado

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -v
node --check web/app.js
node --check web/tactical.js
node --check web/tactical-board.js
```

Las pruebas incluyen creación, migración, checksum/respaldo, fallo de escritura,
checkpoint de habitación, muerte/abandono, hitos 10/30, habilidades independientes
del equipo, party del roster y ciclos completos por HTTP con archivos temporales.

`test_tactical_board.py` cubre grupos de seis, validación de posiciones, límites de terreno, rutas, alcance/visión, trampas, flanqueo, maniobras, determinismo, reintentos y API. `test_workshop_pages.cjs` también comprueba el editor y la reproducción con datos reales del motor, sin navegador; no verifica visualmente el diseño.

`simulate_tactical.py` conserva personajes de laboratorio (Aria, Bruno y Cora)
para comparar las fórmulas y diagnósticos sin partidas locales. Estos fixtures
solo se usan al construir el simulador **sin** un roster inyectado; el servidor
siempre inyecta el roster real. Sus poderes de prueba están ligados a sus roles,
nunca al arma. Los resultados de balance anteriores al cambio de habilidades
no describen el balance actual del juego con personajes persistentes.

El simulador que construye `CombatResolver` sin `tablero` mantiene la resolución anterior sin posiciones para conservar comparaciones históricas. El controlador HTTP siempre crea un tablero; las pruebas nuevas cubren este recorrido jugable.

El diagnóstico suma únicamente HP efectivamente perdido: ticks informativos y
muertes no duplican daño. Una fuente que alcanza el 40% determina la causa;
si ninguna lo alcanza se informa desgaste general. El límite de 80 rondas
previene combates infinitos.
