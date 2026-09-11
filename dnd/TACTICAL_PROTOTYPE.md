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
6. **Desafío táctico · Party de 3** se habilita al tener tres personajes.
   La condición es el tamaño del roster; no se impone otro nivel mínimo.

La web y Godot consumen el mismo motor HTTP. Desde el menú de Godot, el botón
Desafío táctico abre el cliente web del mismo servidor de desarrollo.

## Preparación y combate táctico

Se seleccionan tres personajes distintos del roster, incluso cuando hay más de
tres disponibles. Cada uno aporta nombre, nivel, estadísticas y equipo desde
su último checkpoint. Solo se pueden elegir armas que ese personaje posee y
cuyos requisitos cumple. El inventario de otro personaje no concede acceso.

Se conservan las builds Ofensiva (+20% ataque y +1 velocidad) y Adaptación
(65% resistencia al sangrado y +25% ruptura), las prioridades de IA, el combate
automático, el jefe con sangrado/escudo y los diagnósticos de derrota.

Las armas tienen daño, escalado y propiedades físicas; no conceden técnicas,
habilidades ni pasivas. Los árboles de clase/chispa aún están vacíos: elegir
clase no altera estadísticas ni habilita poderes. La IA del roster usa ataques
básicos hasta que se conecten esos árboles. Las reglas futuras de prioridad
solo podrán ejecutar habilidades disponibles para el personaje.

Cada intento trabaja con copias. El daño, los estados y los cambios de
preparación táctica no modifican el roster ni guardan progresión del calabozo.
Recargar la página conserva el combate en memoria; reiniciar el servidor
restablece la preparación. El servidor calcula una ronda por solicitud
`/api/tactico/avanzar`; el navegador las solicita automáticamente.

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
| `POST /api/tactico/preparar` | Tres selecciones: personaje, build, arma y prioridad. |
| `POST /api/tactico/iniciar` | Inicia con `{seed}`; valida party y propiedad del equipo. |
| `POST /api/tactico/avanzar` | Resuelve una ronda. |
| `POST /api/tactico/reajustar` | Vuelve a preparación tras el resultado. |

## Validación y simulador aislado

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -v
node --check web/app.js
node --check web/tactical.js
```

Las pruebas incluyen creación, migración, checksum/respaldo, fallo de escritura,
checkpoint de habitación, muerte/abandono, hitos 10/30, habilidades independientes
del equipo, party del roster y ciclos completos por HTTP con archivos temporales.

`simulate_tactical.py` conserva personajes de laboratorio (Aria, Bruno y Cora)
para comparar las fórmulas y diagnósticos sin partidas locales. Estos fixtures
solo se usan al construir el simulador **sin** un roster inyectado; el servidor
siempre inyecta el roster real. Sus poderes de prueba están ligados a sus roles,
nunca al arma. Los resultados de balance anteriores al cambio de habilidades
no describen el balance actual del juego con personajes persistentes.

El diagnóstico suma únicamente HP efectivamente perdido: ticks informativos y
muertes no duplican daño. Una fuente que alcanza el 40% determina la causa;
si ninguna lo alcanza se informa desgaste general. El límite de 80 rondas
previene combates infinitos.
