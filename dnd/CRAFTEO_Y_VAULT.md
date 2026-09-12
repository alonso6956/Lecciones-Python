# Crafteo y Vault compartido

Acceso: menú principal → **Taller de crafteo** o **Vault compartido**, como dos opciones independientes, tanto desde la web como desde Godot (abre las mismas interfaces web). El taller muestra el diseño y el inventario del receptor; el vault muestra únicamente el inventario y la bóveda para organizar transferencias.
Se necesita un personaje creado. El taller trabaja con sus checkpoints guardados y se bloquea durante una expedición o un combate táctico para evitar que una copia antigua sobrescriba una transferencia.

La **Tienda · Preparar personaje** también está en el menú principal, con opciones **Comprar** y **Vender**. Se elige el personaje, el producto y la cantidad; se actualiza su oro y se guarda la operación inmediatamente. El equipo comprado compatible se equipa automáticamente; el resto se queda en su inventario. No aparecen tiendas dentro del dungeon ni se aceptan operaciones durante una expedición o combate táctico. Dentro del dungeon se utilizan los objetos que el personaje llevó al entrar.

## Crafteo

- Los enemigos pueden dejar materiales y componentes al morir. El progreso se guarda al avanzar de una habitación superada a la siguiente o al morir. Abandonar vuelve al último checkpoint.
- El personaje elige espada, maza, daga, lanza, casco, peto, brazales, grebas o escudo; hierro, acero, bronce, plata u obsidiana. Los componentes ofensivos opcionales solo se admiten en armas.
- Se fabrica al Tier de su habilidad: I inicialmente; II/III/IV/V después de 5/15/30/50 fabricaciones. El coste es 3 unidades de material por Tier, un componente si se eligió y el coste en oro indicado en la previsualización.
- Los recursos se consumen primero del inventario del personaje y después del vault para completar lo que falte, incluidos los componentes. La previsualización desglosa ambas fuentes. El personaje elegido paga el oro, recibe el objeto y gana la experiencia de crafteo.
- El generador conserva el presupuesto del Tier: los perfiles transfieren puntos entre estadísticas con una variación relativa máxima del 10%. Los afijos reservan el 10% del presupuesto; la eficacia sobrenatural de la plata reserva un 3%.
- La creación produce una instancia con UUID. Nombrarla después no cambia sus estadísticas. Se puede equipar desde el taller.
- Armaduras y escudos usan las piezas del catálogo como modelos: conservan slot y requisitos, mejoran defensa o bloqueo según el Tier, material y perfil, y ajustan peso y durabilidad. La armadura aporta al menos un punto de defensa más que el modelo. Los perfiles pesados aumentan protección y peso; los ligeros los reducen. Los límites y factores están en `crafting.json`, sección `protecciones`. El escudo sigue siendo incompatible con armas de dos manos.
- La previsualización se calcula con las mismas fórmulas que la fabricación: muestra los rangos posibles de cada perfil, durabilidad, requisitos, materiales, coste de fabricación, valor de mercado y precio de venta. No consume recursos ni genera instancias. Fabricar se habilita cuando hay materiales, oro y espacio suficientes en el inventario del receptor. Agotar una pila del vault no libera un espacio en ese inventario.
- La barra de habilidad indica el progreso dentro del Tier actual y el siguiente desbloqueo; al llegar al Tier V permanece al 100%.
- Daño, velocidad, crítico, penetración y efectos periódicos de afijo alimentan ambos modos. Alcance y durabilidad se conservan como datos; esta versión no añade posicionamiento ni desgaste al combate existente.

Las tablas de balance, progresión, costes, botín, perfiles, materiales y afijos están en `crafting.json`. No hay rareza o calidad aleatoria adicional.

## Economía y ventas

`economy.py` calcula el valor de mercado usando el precio del equipo comparable del catálogo (misma familia de arma, slot de armadura o tipo de secundario). Usa el Tier disponible más alto que no supere al fabricado. Si ese Tier aún no existe en la tienda, extrapola un 40 % por Tier, siguiendo el salto actual de 50 a 70 oro de las armas. La lanza toma la espada como referencia, igual que su modelo de fabricación.

- Fabricación: **150 % del valor de mercado**, redondeado hacia arriba, además de materiales y componente.
- Venta: **50 % del valor de mercado**, redondeado hacia abajo.
- Ejemplo de arma Tier I: comprar el modelo cuesta 50 oro; fabricar cuesta 75 oro más 3 materiales; vender lo fabricado devuelve 25 oro. Fabricar y vender pierde 50 oro y los materiales.
- El precio se guarda en la instancia al crearla; cambiar el nombre, equiparla, transferirla o subir la habilidad no aumenta su valor. Los perfiles aleatorios y afijos no multiplican su precio.
- Se venden objetos del inventario del personaje, por instancia de equipo o cantidad de consumibles. El servidor calcula el ingreso; no admite precios enviados por el cliente. Una pieza vendida no puede venderse de nuevo.
- No se vende la copia equipada. Si hay varias copias de una pieza de catálogo, se reserva una para el equipamiento y se pueden vender o transferir las restantes.
- El arma inicial gratuita no se puede vender, aunque se transfiera a otro personaje. Los materiales, componentes y otros objetos con precio cero tampoco tienen valor de reventa. Se respetan las restricciones de objetos vinculados o bloqueados del catálogo.
- Las armas fabricadas antes de esta actualización siguen cargándose con su precio anterior (cero); no se les asigna valor retroactivamente.

El coste de oro por sí solo ya supera lo recuperado al vender, incluso si los materiales proceden íntegramente del botín o del vault. Fabricar no permite generar oro mediante un ciclo de fabricación y venta.

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

`roster.json` contiene los personajes y `shared_vault`, como secciones hermanas del estado global. Una transferencia o fabricación prepara copias del personaje y vault y confirma ambos con un único reemplazo atómico y checksum. Oro, recursos, objeto y experiencia se confirman juntos. La memoria se publica solo después del guardado. Una venta también se realiza sobre una copia. Un fallo conserva los contenedores y oro anteriores; el respaldo contiene un estado coherente.

Los inventarios antiguos sin instancias ni vault se migran en memoria y se escriben en el siguiente guardado normal. No se sobrescriben los slots legacy. Los UUID y datos completos del equipo procedural viajan con su contenedor; el catálogo estático no se llena con definiciones generadas. Se conserva el formato de las armas anteriores y se reconocen armaduras y escudos por sus campos de tipo. El descarte de un personaje conserva el vault.

## Verificación

```powershell
.\.venv\Scripts\python.exe -B -m unittest discover -q
node --check web/workshop.js
node --check web/shop.js
```

`test_crafting_economy.py` comprueba consumo desde ambas fuentes, precios de todas las recetas/Tiers/materiales/perfiles, capacidades, bloqueos, concurrencia, rollback, ventas, recarga, equipo táctico y recorridos HTTP. También ejecuta `test_workshop_pages.cjs` con datos temporales del servidor para comprobar los controles de las tres páginas; esa prueba no sustituye una revisión visual en navegador. Las dos especificaciones PyInstaller incluyen `crafting.json`.
