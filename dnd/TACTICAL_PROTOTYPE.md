# Vertical slice táctico de Dungeon

El menú web incluye **Desafío táctico · Party de 3**. Este modo permite preparar
el grupo, observar el combate automático, leer un diagnóstico de derrota y
reajustar el siguiente intento sin reiniciar el programa. El modo original sigue
disponible en **Nueva partida**.

## Especificación y alcance

Se leyeron completos los tres PDF proporcionados. En este checkout están en la
raíz de `dnd`, no en `docs/`:

- `Plan_Modificacion_Prototipo_Dungeon_DnD_RPG_Tactico.pdf`: especificación inmediata.
- `GDD_Arquitectura_RPG_Tactico.pdf`: diseño general futuro.
- `GDD_Prototipo_Formulas_Modulos.pdf`: referencia técnica subordinada al plan.

Se implementan el roster fijo de tres personajes, dos builds por personaje,
tres armas tácticas, dos presets de IA, un jefe con sangrado y escudo,
registro estructurado, diagnóstico, reintento y simulaciones de balance.
No se añaden energía idle, reclutamiento, talentos completos, expediciones,
economía, monetización, mapa, narrativa ni sistemas de intervención manual.
Los sistemas ya existentes del modo original se conservan.

## Ejecutar

Desde `dnd`, con Python 3.12 o el entorno virtual existente:

```powershell
$env:DUNGEON_ENV = "development"
.\.venv\Scripts\python.exe -B main.py
```

El procedimiento normal abre `http://127.0.0.1:8000`. Elegir **Desafío táctico**
o visitar `/tactical.html`. En producción se conserva el puerto 8765.
La configuración táctica vive en memoria durante la sesión del servidor;
recargar la página la conserva y reanuda el combate, reiniciar el servidor la
restablece. Los slots originales no reciben datos tácticos.

El servidor calcula una ronda por solicitud `/api/tactico/avanzar`; el navegador
las solicita automáticamente. No se pide una acción al jugador por turno.
Cerrar la página pausa ese avance; volver a abrirla lo reanuda. El selector de
ritmo cambia la cadencia de presentación, no las reglas de combate.

Python está instalado y `.venv` funciona. El primer fallo de ejecución se debía
a restricciones del sandbox sobre la instalación de Microsoft Store. Las
pruebas se ejecutaron con el intérprete local fuera del sandbox, con aprobación.

## Escenario reproducible de aceptación

Mantener la semilla **1235**, que aparece inicialmente en la interfaz.

1. Iniciar con los tres personajes en Ofensiva, Dagas de hierro y Agresiva.
   La party pierde y el diagnóstico identifica sangrado.
2. Pulsar **Reajustar y reintentar**.
3. Elegir esta preparación:

| Personaje | Build | Arma | Prioridad |
| --- | --- | --- | --- |
| Aria | Adaptación | Espada de hierro | Táctica |
| Bruno | Adaptación | Maza de hierro | Táctica |
| Cora | Adaptación | Espada de hierro | Táctica |

4. Iniciar con la misma semilla: la party rompe el escudo y gana con tres
   supervivientes. Todos mantienen nivel 1.

La misma preparación adaptada con semilla **1234** pierde por fallo de escudo:
las prioridades de limpieza pueden consumir la ventana de ruptura. Esto permite
comprobar un diagnóstico distinto sin introducir otro jefe.
Adaptación con dagas y prioridad Agresiva, semilla **1235**, produce una derrota
mixta sin ninguna fuente que alcance el 40%.

## Mapa y decisión de reutilización

| Archivos existentes | Responsabilidad | Decisión |
| --- | --- | --- |
| `main.py`, `server.py` | Arranque y API HTTP | Conservar el arranque; ampliar rutas del servidor. |
| `character.py`, `inventario.py` | Personaje, vida, stats y equipo | Reutilizar por composición en cada intento. |
| `enemies.py` | Modelo de enemigo | Reutilizar `Enemigo` para el jefe. |
| `item.py`, `item_factory.py`, `items.json`, `items.py` | Armas y catálogo | Reutilizar identificadores, nombres, requisitos y daño. |
| `combat_formulas.py` | Fórmulas puras de mitigación y habilidades | Mantener y reutilizar la mitigación con constante 22. |
| `game_engine.py`, `initiative.py` | Combate y orden de acciones 1v1 | Conservar como referencia y modo original; su cola binaria no representa cuatro actores. |
| `state.py` | Contrato de estado del modo original | Conservar; el nuevo modo tiene su propio contrato. |
| `level_system.py`, `persistence.py` | Nivel y guardados | Conservar; el desafío tiene nivel fijo y no escribe slots. |
| `web/` | UI del procedimiento de arranque actual | Añadir entrada al menú y una página táctica. |
| `godot_client/` | Cliente alternativo | Conservar; el vertical slice se entrega en la UI web existente. |

El acoplamiento principal está en `MotorJuego`: administra encuentro, turnos,
recompensas, guardado y eventos para un jugador y un enemigo. Sus eventos se
recortan a 120 y no sirven como historial causal completo. No se modifica ese
contrato para evitar regresiones de los clientes existentes.

| Archivos nuevos | Responsabilidad |
| --- | --- |
| `tactical_models.py` | Roster, encuentro, adaptadores de modelos, armas tácticas y recomposición de builds. |
| `tactical_ai.py` | Primera coincidencia entre reglas, objetivos vivos y cooldowns. |
| `tactical_combat.py` | Iniciativa por ronda, acciones, estados, escudo, castigo y fin. |
| `tactical_diagnostics.py` | `CombatEvent`, historial completo y contribución por daño efectivo. |
| `tactical_controller.py` | Preparación, combate, resultado y reajuste; exclusión mutua HTTP. |
| `simulate_tactical.py` | Simulaciones sin render ni servidor, cinco perfiles comparables. |
| `web/tactical.html`, `.css`, `.js` | Selección, stats finales, observación, diagnóstico y descarga JSON. |
| `test_tactical.py`, `test_tactical_http.py` | Aceptación del motor, del controlador y del servidor real. |

## Decisiones de combate

- Las builds se recomponen creando un `Personaje` desde atributos base y equipo.
  Su vida, defensa, velocidad y daño base provienen del modelo actual. Cada nuevo
  intento recibe modelos, HP, estados, cooldowns, RNG y log nuevos.
- El ataque del slice usa `(daño_base + promedio_del_arma) * 2 * build`.
  El factor 2 calibra el encuentro 3v1; la mitigación sigue usando la fórmula
  original `22 / (22 + armadura)`. No se cambia el balance del modo original.
- El azar se limita a iniciativa (hasta +10% de velocidad por ronda) y críticos
  de dagas. Se usa `random.Random(seed)` independiente por intento.
- Dagas: velocidad, crítico y daño a vulnerables. Maza: ruptura. Espada:
  perforación de armadura y resistencia al sangrado. Los nombres e IDs son del
  catálogo original; sus propiedades tácticas se añaden solo en el nuevo modo.
- Adaptación resiste 65% del sangrado y la espada reduce 25% del remanente:
  combinadas dan 73,75%, no inmunidad. Limpiar consume una acción y cooldown.
- Cora puede curar o proteger. Bruno con prioridad Táctica reserva su habilidad
  hasta el escudo y vuelve a usar su ataque único cuando pasa esa fase.
- El jefe activa escudo al caer al 50% HP. La ventana incluye el resto de la ronda
  de activación y las siguientes dos rondas completas. El escudo absorbe el golpe
  que lo rompe, sin convertir el excedente de ruptura en daño a HP.
- La ruptura aturde al jefe y lo vuelve vulnerable durante el resto de la ronda
  y la siguiente. El castigo se aplica al final de la ventana si queda escudo.
- Los cooldowns bajan al final de ronda; un cooldown de 3 usado en R1 permite
  usar otra vez la habilidad en R4. Los estados registran su ronda de vencimiento.
- El log no se trunca. `dano_recibido` registra HP efectivo perdido (sin overkill).
  Ticks, muertes y marcadores de castigo no duplican esa cantidad. El diagnóstico
  expresa la mayor contribución al daño; no afirma causalidad contrafactual.
- Si ninguna fuente alcanza 40%, devuelve desgaste general. El límite de 80
  rondas produce una derrota explícita por seguridad, sin inventar un counter.

## Verificación y balance

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -v
node --check web/tactical.js
.\.venv\Scripts\python.exe -B simulate_tactical.py --n 1000 --seed-base 1234 --output .local/balance-tactico-1000.json
```

Las pruebas incluyen los casos obligatorios:

| Caso | Evidencia |
| --- | --- |
| T01 | 3v1 termina automáticamente, con iniciativa y evento final. |
| T02 | Build ofensiva con armas variadas falla el escudo y registra castigo y daño. |
| T03 | Comparación de 30 semillas: aumenta claramente ruptura y victoria. |
| T04 | Derrota real por sangrado, contribución >=40%. |
| T05 | Log mixto y derrota real mixta; devuelve desgaste general. |
| T06 | Cambios repetidos de build no acumulan stats. |
| T07 | Reintento limpio, mismas selecciones y vida inicial. |
| T08 | Derrota → reajuste → victoria con la misma semilla y nivel, también por HTTP. |
| T09 | Igual preparación y semilla producen idéntico resumen y log. |

También se verifican prioridad y cooldowns, reserva de ruptura, actores muertos,
overkill, validación atómica, bloqueo de preparación en combate, límite de rondas,
umbral exacto y ausencia de doble conteo. Las tres pruebas originales pasan;
el combate original por HTTP sigue terminando en seis acciones con semilla 1234.

La instrumentación reporta tasa de victoria, rondas por resultado, distribución
de causas de derrota, activación/ruptura/castigo del escudo, daño medio por tag y
supervivencia final por personaje. Los perfiles `solo_build`, `solo_arma` y
`solo_ia` aíslan cada cambio respecto a la ofensiva; no son búsquedas exhaustivas
de todas las combinaciones posibles.

Resultado final: **26 pruebas pasan**, incluida la regresión del modo original.
La comprobación de sintaxis JavaScript y `git diff --check` también pasan.
Balance observado con 1.000 semillas consecutivas por perfil (1234–2233),
5.000 combates en total:

| Preparación | Victoria | Ruptura exitosa | Castigo de escudo | Rondas medias |
| --- | ---: | ---: | ---: | ---: |
| Ofensiva | 0% | 0% | 0% | 8,00 |
| Adaptada | 52,3% | 52,3% | 47,7% | 16,01 |
| Solo build | 0% | 0% | 100% | 14,11 |
| Solo arma | 0% | 0% | 100% | 7,00 |
| Solo IA | 0% | 0% | 0% | 8,00 |

La ofensiva de tres dagas muere por sangrado antes del castigo. La variante
ofensiva con armas distintas sí llega al castigo y cubre T02. La preparación
adaptada mejora el resultado en 52,3 puntos porcentuales; ninguno de los cambios
aislados ensayados basta para ganar. Este balance valida el bucle contra este
jefe, no el equilibrio de las builds en encuentros futuros. El reporte completo
está en `.local/balance-tactico-1000.json` y se reproduce con el comando anterior.

La revisión visual en navegador queda pendiente: el proveedor de control de
interfaz devolvió `apps: []` y `browsers: []`. Sí se verifican respuestas HTTP,
recursos de la página, ciclo completo por API y sintaxis JavaScript. No se ha
generado ni validado un nuevo ejecutable empaquetado. Los archivos web ya se
incluyen en los `.spec` existentes y los módulos Python se importan normalmente.

## Estado inicial y punto de retorno

Base Git: `6808bbae5e68f691a53c3007affdf2df8390fc58`, rama `main`.
Antes de modificar código se creó este checkpoint de fuentes, catálogos,
scripts de build y UI web:

`.local/checkpoints/pre-tactico-20260906-230007.zip`

SHA256: `571E7A178B0E8EC60609C558249A82F6AC65E4A0C292C63DD3A4FBBB98C850DB`.

El checkpoint complementa Git; no contiene el entorno virtual ni los PDF.
Los PDF, `.venv`, el `.gitignore` del directorio padre y cuatro `.pyc` modificados
ya estaban presentes al comenzar esta implementación y no se incluyen como
cambios funcionales del slice. Se usa `-B` para no seguir modificando bytecode.
