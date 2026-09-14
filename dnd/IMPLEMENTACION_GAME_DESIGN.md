# Implementación del diseño disponible — 13/09/2026

Se releyeron las 37 notas actuales de `Game Design`. Esta entrega implementa las reglas concretas y mantiene fuera el contenido que todavía necesita definición. Las notas originales no se modificaron. La revisión anterior queda como registro del estado previo.

## Reglas implementadas

| Área | Resultado |
|---|---|
| Salud | `50 + 5 × (nivel−1)`, con bonus plano y porcentual. CON deja de dar HP. Límites de salud actual, curación sin sobrecuración, umbrales alta/media/baja/crítica y vida efectiva en el estado público. |
| Constitución | Deja de dar armadura y capacidad de carga. Deriva Estabilidad, Resistencia Física y Regeneración con las fórmulas de sus notas. |
| Fuerza / daño | Rendimiento decreciente con raíz y coeficiente por arma: se aplica a base + daño de arma, también en la fórmula común de habilidades. La excepción de Bloqueo y contraataque conserva su escalado propio de CON. |
| Armadura / Mitigación | Protección del equipo y bonos, sin defensa innata por CON; K=100 y máximo 60%. Bloqueo permanece separado. |
| Penetración | `5 × √(FUE−1) + arma + bonos`, antes de mitigar. Se aplica también al daño enemigo de Dungeon. Cada mano usa su propia arma. |
| Iniciativa | `10 + 2 × (DES−1) + bonos`; una actuación por ciclo/ronda, sin acciones extra por velocidad. El táctico no añade aleatoriedad a la iniciativa. |
| Movimiento | Base 3–6 por escalones de DES, independiente de iniciativa. Se integra en aproximación y retirada táctica, con costes de terreno. |
| Carga | Capacidad `8 + 2 × (FUE−1) + bonos`; cuatro bandas continuas. Ligera +1 movimiento, normal 0, pesada −1 y −10% relativo de evasión, sobrecarga −2 y evasión cero. |
| Regeneración | `1 + floor((CON−1)/5) + bonos`, con modificador porcentual. Recuperación una vez por actuación; no revive unidades derrotadas. |
| Derivados de control | Impacto, Estabilidad y Resistencia Física están calculados y publicados. Existe la función común de probabilidad resistida. Su uso en los nuevos estados espera a que se cierren esos sistemas. |
| Precisión | Derivado calculado y publicado. No se sustituyó la resolución de acierto: aún falta la fórmula de Evasión como puntuación. |
| Equipo dual | Compatibilidad de ambas armas, una copia por mano, requisitos individuales, dos manos excluye secundaria. Dos golpes básicos independientes al 100% y 50%, con crítico, bloqueo, penetración y afijos de cada arma. |
| Calidad | Cinco calidades con los factores documentados, persistidas en armas y piezas nuevas. Preview contempla todas las calidades y perfiles posibles. |
| Armaduras fabricadas | Presupuesto de conjunto por tier, distribución 40/25/20/15 y validación por slot. Redondeo por mayores restos para no crear armadura adicional. |
| Armas fabricadas | Rangos 5–10 / 11–20 / 21–35 / 36–55, multiplicadores de las cuatro familias existentes y límite final tras material/perfil. |
| Requisitos de fabricación | Tabla orientativa por familia y tier de Crafteo, independiente de clase. Una daga T3 exige DES 9; las dos dagas no suman requisitos. |
| Afijos múltiples | Hasta 1/2/3/4 componentes diferentes en armas T1/T2/T3/T4. Cada componente se valida y consume; cada efecto se comprueba individualmente. Se reutilizan los efectos existentes. |
| Interfaz | Fichas con iniciativa, movimiento y derivados; textos de Constitución/escalado corregidos; calidad y selección múltiple de componentes en taller; posibilidad de equipar una segunda copia de la misma daga. |
| Guardados | Versión de equipamiento; objetos previos conservan UUID, cantidades y estadísticas almacenadas. Las combinaciones antiguas incompatibles se desequipan de la secundaria al cargar, sin eliminar el objeto. |

Implementación principal: [derived_stats.py](derived_stats.py), [combat_formulas.py](combat_formulas.py), [combat_stats.py](combat_stats.py), [equipment_balance.py](equipment_balance.py), [crafting.py](crafting.py), [inventario.py](inventario.py), [game_engine.py](game_engine.py), [tactical_combat.py](tactical_combat.py).

## Criterios aplicados donde coexistían propuestas

- **Salud:** prevalece la nota específica ampliada, +5/nivel, frente al +10 del índice.
- **Armadura:** prevalecen Armadura y Mitigación, coincidentes con Constitución y Salud. No se implementa la alternativa de Defensa con K dependiente del nivel.
- **Poder de ataque:** prevalece la fórmula de Fuerza/Poder de ataque. No se combina con el poder aditivo de Crafteo ni con su segunda tabla de grados de escalado.
- **Dual:** el 50% se aplica una sola vez al daño normal de la secundaria. Las habilidades antiguas no reciben un ataque secundario gratis; no hay aún una habilidad dual nueva que declare penetración combinada.
- **Turno de regeneración:** en Dungeon, al inicio de la actuación. En táctico, después del daño de inicio y antes de actuar; un tick letal no permite regenerarse. Activar una habilidad gratuita no añade regeneración.
- **Movimiento:** el máximo 6 es de la base; los bonos se aplican después, con mínimo final 0. Los umbrales de carga no dejan huecos decimales. El −10% de evasión pesada es relativo, mientras siga funcionando el sistema porcentual anterior.
- **Fabricación:** calidad y perfil se sortean uniformemente. El daño de cada arma nueva queda fijado por su calidad; se conserva el formato de dos extremos iguales por compatibilidad. Materiales y perfiles existentes alteran ese resultado, sujetos al cap.
- **Tiers:** la fabricación nueva llega a T4. Se conserva toda la experiencia anterior y se permite cargar equipo T5 antiguo; no se inventa una tabla nueva para T5.
- **Enemigos:** se conservan sus HP de encuentro anteriores en tablas por raza/arquetipo, sin dependencia automática de CON. La nueva curva de nivel/rango para enemigos todavía es conceptual.

## Sistemas y contenidos excluidos por falta de definición

| Notas / área | Motivo y comportamiento conservado |
|---|---|
| Destreza / Evasión vs Precisión | Destreza.md sigue vacío y falta la puntuación de Evasión. La evasión porcentual anterior continúa resolviendo los ataques. Precisión queda preparada, sin atribuirle un efecto que todavía no tiene. |
| Sangrado | Duración X, acumulación opcional y varias fórmulas de daño alternativas. Se mantienen el sangrado del jefe y los afijos anteriores. |
| Quemadura | Duración X y Resistencia Térmica sin definición; interacciones de extinción/entorno opcionales. El afijo de fuego existente no se presenta como el nuevo sistema completo. |
| Derribo / Desequilibrio / Empuje | Hay propuestas de efectos, pero faltan fuentes jugables completas, probabilidades y decisiones de redondeo/encadenamiento. No se sustituyó el aturdimiento anterior por un estado diferente ni se añadieron efectos a armas sin una fuente definida. |
| Interrupción / Canalización | No hay habilidad terminada que declare preparación, costes, restricciones y consecuencias de cancelación. No se añadieron habilidades de ejemplo como contenido definitivo. |
| Ruptura de Guardia | Guardia Rota, fuentes y valores siguen abiertos. La barra de escudo del jefe conserva su mecánica y no se confunde con bloqueo/postura. |
| Inamovible | Acceso/rangos variables, condiciones de suelo/movimiento y mejoras de ejemplo; depende de una clase incompleta. |
| Rompemuros | Ahora tiene ID `wallbreaker` y acceso 1, pero conserva numerosos campos de plantilla y no tiene árbol terminado. No se añadió una clase vacía al selector. |
| Verdugo de Cuerdas | Solo título. |
| Sombra / Espectro de Ballesta / Guerrero Olvidado / Cazarrecompensas | Archivos vacíos. |
| Impacto Sísmico | Faltan daño, área/alcance, probabilidad, coste y cooldown. |
| Plantilla de clase | No se interpreta como progresión aprobada. El nivel máximo continúa en 30; elección de clases anteriores desde 10. La energía ya usa +1/50 niveles, aunque ese hito no sea accesible con el cap actual. |
| Chispas, traits, evoluciones, hitos, resistencias elementales | Menciones o enlaces sin sistemas completos. |
| Nuevas familias de armas | Martillo pesado y ballestas todavía carecen de datos completos de equipo y, en su caso, preparación. La fabricación continúa ofreciendo espada, daga, maza y lanza. |
| Afijos defensivos / secundarios nuevos de equipo | No hay tablas de magnitud/coste por tier. No se inventaron bonos de Precisión, Impacto, Estabilidad o resistencias para los objetos existentes. El perfil secundario anterior de crítico/penetración se conserva hasta definir su reemplazo; por tanto, la identidad nueva de «penetración alta» de las dagas aún requiere esa tabla. |
| Escudos fabricados | No existe tabla nueva de calidad/presupuesto de bloqueo. Conservan su fabricación anterior. Su modelo admite Armadura y bonos, pero no se asignan valores nuevos sin definición. |
| Armaduras ligeras/medias/pesadas y nuevos materiales | Multiplicadores orientativos sin catálogo terminado. Los perfiles/materiales existentes siguen funcionando y respetan los nuevos caps; no se añadieron familias de armadura incompletas. |
| Regeneración fuera de combate, anticuración, consecuencias narrativas de derrota | Son alternativas o ejemplos aún abiertos. |

## Compatibilidad

Los nuevos objetos llevan `version_diseno=2`; los objetos sin versión son anteriores. Los límites de fabricación nuevos se validan en el registro de objetos nuevos, sin destruir objetos guardados con números anteriores. Esto conserva la colección, pero no significa que esos objetos antiguos estén rebalanceados.

El cambio de fórmulas sí modifica las estadísticas derivadas de todos los personajes al cargar: menos vida para builds de CON, armadura sin defensa innata, carga por FUE e iniciativa sin acciones extra. No se modificaron archivos de partidas reales durante el desarrollo ni se gastaron materiales de la colección del usuario.

El catálogo estático mantiene sus valores de daño/peso y requisitos originales; las nuevas tablas se aplican a la fabricación. Las bonificaciones futuras a Salud/Regeneración pueden usar el mecanismo de bonos, pero no se añadieron traits o pasivas nuevos.

## Verificación

- `python3 -B -m unittest test_game_design`: 28 pruebas de fórmulas, fronteras de carga, acciones, regeneración, dual, integridad de equipo, migración, taller/bóveda, endpoint de preview y combates completos.
- La prueba de fabricación recorre **4.500 variantes**: 4 tiers × 5 materiales × 9 tipos × 5 perfiles × 5 calidades. Verifica registro, caps y coherencia con preview.
- Los seis JavaScript modificados de lógica se analizaron con JavaScriptCore; sintaxis válida. No se realizó una revisión visual completa de navegador/Godot ni una build empaquetada.
- `python3 -B simulate_tactical.py --n 20 --seed-base 1234 --output tmp/game_design_balance.json`: 100 combates de fixtures completados. Los cinco perfiles siguen con 0% de victoria frente a ese jefe; las clases/habilidades de esos fixtures siguen sin árboles asignados. No se considera una validación de balance final.

Pruebas: [test_game_design.py](test_game_design.py). Resultados de simulación: [game_design_balance.json](tmp/game_design_balance.json).
