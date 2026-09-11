# Crafteo y Vault compartido

Acceso: menú principal → **Taller y Vault compartido**, tanto desde la web como desde Godot (abre la misma interfaz web).
Se necesita un personaje creado. El taller trabaja con sus checkpoints guardados y se bloquea durante una expedición o un combate táctico para evitar que una copia antigua sobrescriba una transferencia.

La **Tienda · Preparar personaje** también está en el menú principal. Se elige el personaje, el producto y la cantidad; se descuenta su oro y se guarda la compra inmediatamente. El equipo compatible se equipa automáticamente; el resto se queda en su inventario. No aparecen tiendas dentro del dungeon ni se aceptan compras durante una expedición o combate táctico. Dentro del dungeon se utilizan los objetos que el personaje llevó al entrar.

## Crafteo

- Los enemigos pueden dejar materiales y componentes al morir. El progreso se guarda al avanzar de una habitación superada a la siguiente o al morir. Abandonar vuelve al último checkpoint.
- El personaje elige espada, maza, daga o lanza; hierro, acero, bronce, plata u obsidiana; y un componente opcional.
- Se fabrica al Tier de su habilidad: I inicialmente; II/III/IV/V después de 5/15/30/50 fabricaciones. El coste es 3 unidades de material por Tier y un componente si se eligió.
- Los recursos se consumen exclusivamente del inventario del personaje. Primero hay que retirar los que estén en el vault.
- El generador conserva el presupuesto del Tier: los perfiles transfieren puntos entre estadísticas con una variación relativa máxima del 10%. Los afijos reservan el 10% del presupuesto; la eficacia sobrenatural de la plata reserva un 3%.
- La creación produce una instancia con UUID. Nombrarla después no cambia sus estadísticas. Se puede equipar desde el taller.
- La previsualización se calcula con las mismas fórmulas que la fabricación: muestra los rangos posibles de cada perfil, durabilidad, requisitos y materiales disponibles/necesarios. No consume recursos ni genera instancias. Fabricar se habilita cuando hay materiales y espacio suficientes.
- La barra de habilidad indica el progreso dentro del Tier actual y el siguiente desbloqueo; al llegar al Tier V permanece al 100%.
- Daño, velocidad, crítico, penetración y efectos periódicos de afijo alimentan ambos modos. Alcance y durabilidad se conservan como datos; esta versión no añade posicionamiento ni desgaste al combate existente.

Las tablas de balance, progresión, costes, botín, perfiles, materiales y afijos están en `crafting.json`. No hay rareza o calidad aleatoria adicional.

## Vault

El vault pertenece al perfil completo, con 200 espacios iniciales configurables. Las armas, armaduras y secundarios tienen identidad individual y ocupan un espacio por copia. Los materiales y consumibles idénticos se apilan. El inventario conserva su capacidad ilimitada anterior; los contenedores también admiten un límite configurable.

La pantalla permite elegir personaje, depositar/retirar una cantidad, buscar, filtrar y ordenar. No se puede depositar equipo equipado: para un arma principal hay que equipar otra primero. Las reglas `vault_allowed`, `bound` y `quest_locked` del catálogo y la lista `vault.bloqueados` permiten excluir objetos.

El inventario y el vault usan slots compactos con iconos, cantidades y una marca de equipo. Pasa el cursor, enfoca con Tab o toca un slot para ver los detalles; Enter abre sus acciones con teclado. Escape cierra el panel.

- **Clic derecho:** transfiere una unidad.
- **Shift + clic:** transfiere la pila completa.
- **Arrastrar al panel opuesto:** transfiere la pila completa.
- **Depositar materiales / Depositar todo:** mueve los objetos admitidos en una sola operación, omitiendo equipo equipado y objetos restringidos. Si falta capacidad o falla el guardado, no se mueve ninguno. Los filtros de búsqueda no limitan estos depósitos.
- Para otra cantidad, usa el selector del panel emergente. En pantallas táctiles se conservan todas las acciones sin necesitar arrastrar.

## Persistencia y compatibilidad

### Inventario y equipo durante la expedición (web)

El botón **Personaje** reúne los accesos en cuatro pestañas:

- **Personaje:** estadísticas primarias y secundarias del motor, bonificaciones y equipamiento actual. Seleccionar un slot abre Inventario con sus objetos compatibles.
- **Clase:** clase elegida, elección de clase desde nivel 10 y habilidades disponibles. La elección y las mejoras respetan los bloqueos del combate.
- **Inventario:** categorías rápidas y acciones para usar, equipar o consultar objetos. El daño mostrado en cada arma es el del objeto; el daño total del personaje aparece en su ficha.
- **Chispa:** estado del desbloqueo al nivel 30 y de la chispa latente. La administración permanece pendiente hasta que ese sistema se habilite.

Las flechas izquierda/derecha, Inicio y Fin permiten cambiar de pestaña con teclado. Cambiar de pestaña no consume turnos.

Un clic usa una poción o equipa un objeto permitido. Las pociones consumen la acción de combate y el panel se cierra al resolverse el turno. Cambiar o quitar equipo sólo está permitido entre combates; los requisitos, la vida completa y la muerte bloquean las acciones correspondientes. Los detalles explican cada bloqueo. Escape cierra la ventana y Tab conserva el foco dentro de ella. Las peticiones pendientes bloquean acciones repetidas.

### Guardados

`roster.json` contiene los personajes y `shared_vault`, como secciones hermanas del estado global. Una transferencia prepara copias del origen y destino y confirma ambos con un único reemplazo atómico y checksum. La memoria se publica solo después del guardado. Un fallo conserva ambos contenedores anteriores; el respaldo también contiene un par coherente de inventarios y vault.

Los inventarios antiguos sin instancias ni vault se migran en memoria y se escriben en el siguiente guardado normal. No se sobrescriben los slots legacy. Los UUID y datos completos de las armas procedurales viajan con su contenedor; el catálogo estático no se llena con definiciones de armas generadas. El descarte de un personaje conserva el vault.

## Verificación

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -q
node --check web/workshop.js
node test_combat_inventory_ui.cjs
```

`test_workshop.py` comprueba presupuesto, consumo, nombres, identidad entre personajes, capacidades, bloqueos, concurrencia, rollback, recarga y uso en ambos combates. `test_tactical_http.py` incluye los recorridos HTTP del taller y el bloqueo durante combate. Las dos especificaciones PyInstaller incluyen `crafting.json`.
