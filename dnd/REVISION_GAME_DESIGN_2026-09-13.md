# Comparación de Game Design con el juego actual

Fecha: 13 de septiembre de 2026. Revisión del contenido disponible en disco durante esta sesión.

**Conclusión:** el nuevo diseño requiere una revisión transversal de las reglas de combate, no solo añadir clases. Hay infraestructura reutilizable para personajes, equipo, fabricación, guardado y tablero. Sin embargo, las fórmulas actuales y varias mecánicas especiales todavía responden a otro modelo. La mayor parte del control físico y de las estadísticas secundarias propuestas está por construir.

Esta revisión no modifica reglas, catálogos, documentos de diseño ni partidas. Las recomendaciones son propuestas para la siguiente etapa, no decisiones de diseño tomadas por anticipado.

## Alcance y criterio

Se leyeron los **33 archivos Markdown** de `Game Design`: 2 clases, 1 habilidad, 2 notas en Pasivas, 1 en Estados, 4 en Estadísticas, 17 sistemas, 5 efectos y 1 plantilla. La plantilla no se considera contenido jugable aprobado. Los textos que dicen «ejemplo», «opcional» o «recomendado» se tratan como propuestas, no como requisitos cerrados.

El contraste utiliza código ejecutable y catálogos actuales. Los documentos antiguos de la raíz no se toman como autoridad por encima de `Game Design`. No se realizó una revisión exhaustiva de esos PDF ni una prueba visual de todos los clientes. Las referencias de código enlazadas permiten localizar los modelos y resolutores relevantes.

Distingo tres situaciones:

- **Existe y se puede conservar:** cumple una parte concreta del diseño.
- **Existe, pero hay que modificar o ampliar:** hay implementación aprovechable, aunque sus reglas difieren o su integración está incompleta.
- **Por crear:** no se encontró una implementación funcional del sistema descrito. Puede haber una mecánica parecida sin equivalencia completa.

## 1. Qué juego hay actualmente

Hay dos rutas de combate servidas por el mismo backend:

| Ruta | Estado actual | Consecuencia para el rediseño |
|---|---|---|
| Dungeon, `MotorJuego` | Expedición de 50 habitaciones, combate individual, acciones de atacar/defender, energía, iniciativa con acciones adicionales, progresión y guardado. | Tiene varias resoluciones de daño y estados que deben revisarse al cambiar reglas compartidas. |
| Táctico, `CombatResolver` | Grupo de 3–6 personajes, rondas, una actuación por actor vivo, tablero de 10×8, rutas, alcance, escenarios, IA y registro de combate. | Reutiliza personajes y estadísticas, pero tiene su propio ciclo, iniciativa, estados y mecánicas de jefe. |
| Persistencia y servicios | Roster, inventario, bóveda compartida, taller, tienda y objetos procedurales persistentes. | Son una base útil; cambiar esquemas y reglas requiere conservar o migrar los datos existentes. |

Referencias: [main.py](main.py), [server.py](server.py), [game_engine.py](game_engine.py), [tactical_combat.py](tactical_combat.py), [tactical_controller.py](tactical_controller.py), [character_roster.py](character_roster.py).

**Una distinción importante:** tener código de una habilidad no significa que el jugador pueda obtenerla. Las tres clases actuales —Guerrero, Pícaro y Guardián— tienen árboles vacíos en `progression.py`, y `pasivas.json` está vacío. Hay seis habilidades en el catálogo, pero no están asignadas a esos árboles. El jefe sí recibe Golpe aplastante en su arquetipo.

En táctico, `Actor` tiene campos `habilidades_tacticas` y `unica`, y la IA contempla curar, limpiar, romper y otras acciones; `BuildManager.crear_party` no los rellena desde habilidades de clase. Los actores creados por esa ruta quedan con `()` y `None`. Por tanto, esas ramas no constituyen un repertorio accesible por la progresión actual.

Referencias: [progression.py](progression.py), [skills.json](skills.json), [habilidades.py](habilidades.py), [pasivas.json](pasivas.json), [enemies.py](enemies.py), [tactical_models.py](tactical_models.py), [tactical_ai.py](tactical_ai.py).

## 2. Estadísticas y fórmulas: comparación

En las fórmulas siguientes, FUE, DES y CON representan atributos efectivos cuando hay bonificaciones de equipo; L es el nivel. Las expresiones objetivo son las de las notas indicadas, sujetas a las contradicciones del apartado 6.

| Sistema | Game Design | Código actual | Evaluación |
|---|---|---|---|
| Fuerza / Poder de ataque | `M = 1 + 0.10 × √(FUE−1)`; daño de base y arma multiplicado con coeficiente propio del arma. | Escalado lineal por arma. En ataque básico se escala la base del personaje y luego se suma la tirada del arma. Las habilidades usan otra fórmula, generalmente `1 + 0.20 × (atributo−1)` sobre base + arma. | **Modificar.** Unificar significado de poder, escalado de arma y uso en básicos/habilidades. |
| Destreza | Alimenta Precisión, Evasión, Iniciativa y Movimiento. Su nota individual está vacía. | Aumenta evasión porcentual y velocidad; las dagas escalan su daño base con DES. | **Modificar y completar diseño.** Falta decidir el escalado ofensivo de DES y la fórmula de Evasión como puntuación. |
| Constitución | Estabilidad, Resistencia Física y Regeneración; no aumenta Salud ni Armadura. | Aumenta Salud, defensa base y capacidad de carga. | **Sustituir sus derivados.** Cambiar solo Salud dejaría casi toda la diferencia sin resolver. |
| Salud | `50 + 5 × (L−1)` en Salud.md; el índice dice +10/nivel. | `round(50 × [1 + 0.20 × (CON−1)] + 5 × (L−1))`. | **Parcial.** Base 50 y +5 por nivel ya existen; hay que retirar CON si prevalece Salud.md. |
| Energía | Índice: +1 cada 50 niveles. No tiene nota propia. | Base 3 y `L // 10` adicional. Atacar y defender recuperan 1 en Dungeon. | **Modificar crecimiento; completar ciclo objetivo.** El táctico no consume energía para sus acciones actuales. |
| Precisión frente a Evasión | Precisión `50 + 2 × (DES−1) + arma + bonos`; probabilidad `0.80 + 0.5 × (P−E)/(P+E+100)`, limitada a 10–95%. | Se compara una tirada directamente con la evasión del defensor; no interviene la precisión del atacante. Evasión base 5% + 3 puntos porcentuales por DES posterior al primero, hasta 100%, antes de penalizaciones. | **Reemplazar resolución.** Crear Precisión y convertir Evasión de probabilidad a puntuación. |
| Iniciativa | `10 + 2 × (DES−1) + equipo`. Ordena; no concede más acciones. | Dungeon acumula ventaja de velocidad y da una acción extra por cada 6 puntos. Táctico ordena por velocidad + aleatorio de hasta 10%, con una actuación por ronda. | **Modificar ambos.** El táctico ya cumple la separación conceptual, pero no la fórmula. |
| Movimiento | `min(6, 3 + floor((DES−1)/10))` antes de aclarar modificadores. | Táctico: presupuesto `max(2, min(4, int(velocidad/4)))`; terreno consume puntos. | **Modificar cálculo; conservar rutas y costes.** No existe atributo Movimiento independiente. |
| Capacidad de carga | `8 + 2 × (FUE−1)`; bandas ligera, normal, pesada y sobrecarga. | `8 + 4 × (CON−1)`; cada tramo iniciado de 10 de sobrepeso resta 5 puntos porcentuales de evasión y 3 de velocidad. | **Reemplazar atributo y umbrales.** Ya se suma peso equipado. |
| Armadura | Principalmente equipo; suma de fuentes sin escalado directo de CON. | `10 + CON // 2 + armadura de piezas + bono pasivo de defensa` para personajes. Enemigos: `1 + CON // 2`. | **Modificar.** El dato publicado como armadura incluye defensa innata. Los escudos actuales bloquean, pero no aportan armadura. |
| Defensa | Su nota propone `10 + 2(CON−1) + Armadura`, con K dependiente de nivel. | Tiene una defensa base propia y se integra en la armadura enviada a mitigación. | **Decisión pendiente.** La nota contradice el enfoque de Armadura/Mitigación; no implementar las dos a la vez. |
| Mitigación | Armadura efectiva / (Armadura efectiva + 100), máximo 60%. Bloqueo separado. | Armadura / (Armadura + 40), sin cap del 60%. El bloqueo ya es una capa separada. | **Modificar fórmula y límite; conservar separación de bloqueo.** |
| Penetración | `5 × √(FUE−1) + arma + bonos`, restada antes de mitigar. Dual: asociada al golpe participante. | Existe penetración de arma y resta antes de mitigación en las rutas que usan `armadura_tras_penetracion`; no deriva de FUE. | **Ampliar y homogeneizar.** En Dungeon, la ruta de daño enemigo no pasa por esa función; el ataque táctico sí. |
| Impacto | `10 + 2 × (FUE−1) + arma + bonos`, para control físico. | No hay estadística ni resolución equivalente. La ruptura de escudo táctico usa daño × factor de arma. | **Crear.** No confundir Impacto físico con probabilidad de acertar. |
| Estabilidad | `10 + 2 × (CON−1) + bonos`, opuesta a Impacto. | No hay atributo o cálculo equivalente. | **Crear.** |
| Resistencia Física | `2 × (CON−1) + bonos`; resiste estados, no daño directo. | Existe una resistencia porcentual al sangrado en el adaptador táctico, sin esta derivación ni fórmula; las builds actuales la fijan en 0. | **Crear sistema general.** La resistencia específica anterior solo sirve de antecedente. |
| Regeneración | `1 + floor((CON−1)/5) + bonos`, HP por turno, con modificadores. | Hay curación y pociones, pero no regeneración periódica por CON. | **Crear.** Definir cuándo ocurre y cómo interactúa con muerte y daño periódico. |

Referencias de implementación: [character.py](character.py), [combat_formulas.py](combat_formulas.py), [combat_stats.py](combat_stats.py), [item.py](item.py), [items.py](items.py), [initiative.py](initiative.py), [weapon_effects.py](weapon_effects.py), [enemies.py](enemies.py), [tactical_combat.py](tactical_combat.py).

### Diferencias numéricas comprobadas

Personaje de nivel 10, FUE=DES=CON=10, espada de hierro, sin piezas de armadura ni secundario:

| Medida | Actual, calculado con el código | Objetivo de las notas |
|---|---:|---:|
| Salud máxima | 185 | 95, si prevalece Salud.md |
| Capacidad de carga | 44 | 26 |
| Armadura publicada | 15, aun sin piezas | 0 procedente de equipo; otros bonos deberán definirse |
| Energía máxima | 4 | 3 si se conserva base 3 y se cambia a +1/50 niveles |
| Velocidad / futura iniciativa | 19 de velocidad | 28 de iniciativa, sin bonos |
| Movimiento sobre suelo normal | 4 puntos en táctico | 3 antes de modificadores |

La comparación de iniciativa no equipara velocidad con la futura estadística: muestra precisamente la diferencia entre ambos modelos. La base 3 de Energía es una hipótesis de continuidad, no una definición presente en su nota.

| Armadura efectiva | Mitigación actual | Diseño Armadura/Mitigación |
|---|---:|---:|
| 17 | 29.82% | 14.53% |
| 40 | 50.00% | 28.57% |
| 100 | 71.43% | 50.00% |
| 150 | 78.95% | 60.00% |
| 200 | 83.33% | 60.00% |

Cambiar simultáneamente Salud y Mitigación reduce mucho la resistencia de los personajes actuales. La regeneración, el control y el nuevo presupuesto de equipo deben evaluarse junto con enemigos y encuentros; no basta trasladar coeficientes.

## 3. Equipamiento y crafteo

| Parte | Qué existe | Diferencia respecto al diseño |
|---|---|---|
| Slots | Principal, secundaria, casco, pecho, brazos, piernas. | Coincide con la estructura básica propuesta. |
| Dos manos | Una principal de dos manos vacía la secundaria y bloquea equipar una secundaria mientras está puesta. | Conservar y revisar validación de combinaciones/restauración. Faltan propiedades explícitas de compatibilidad dual. |
| Secundaria | Escudo o arma de tipo daga. | No hay compatibilidad genérica `dual_wield` ni herramientas/focos de clase implementados. |
| Ataque dual | Se suma el 50% de la tirada de la daga secundaria al daño básico. | No son dos golpes independientes. Usa crítico, penetración y afijo de la principal para el golpe combinado; faltan eventos y propiedades de la secundaria. |
| Escudos | Probabilidad de bloqueo y porcentaje bloqueado; fabricación y peso. | No aportan Estabilidad ni Armadura según el modelo nuevo. Ruptura de Guardia debe actuar sobre el bloqueo/postura, no sobre una barra de HP genérica. |
| Requisitos | Comparaciones numéricas con atributos del personaje. | No hay un evaluador completo de requisitos de clase, habilidad, trait o compatibilidad declarada. |
| Peso | Campo en equipo y suma por slots. | Las armas estáticas del catálogo omiten peso y reciben 0 por defecto. Falta completar datos además de cambiar la fórmula de carga. |
| Estadísticas de equipo | Daño, velocidad, crítico, penetración, alcance, peso, durabilidad; protección y bonos de atributos en piezas. | Faltan Precisión, Impacto, Estabilidad, potencias de estados, resistencias y coeficientes del nuevo modelo. Durabilidad está almacenada, sin ciclo de desgaste/reparación encontrado. |
| Fabricación | Armas, 4 piezas y escudos; materiales, perfiles aleatorios, preview, costes, experiencia, UUID y persistencia. | Base reutilizable. El cálculo estadístico requiere revisión sustancial. |
| Tier | Cinco tiers con presupuestos 100/130/170/220/290; acceso por experiencia de fabricación. | Diseño presenta cuatro tiers de referencia. No está decidido qué pasa con Tier 5 ni con equipo existente. |
| Calidad | No existe campo, tirada ni categoría de calidad. | Crear Defectuosa/Común/Buena/Excelente/Maestra con factores 0.10/0.30/0.55/0.80/1.00. Un perfil «preciso» o «pesado» no equivale a calidad. |
| Armaduras fabricadas | Multiplica defensa de pieza base por tier, material y perfil. | No reparte un presupuesto de conjunto por coeficientes 0.40/0.25/0.20/0.15 ni valida el cap final del nuevo tier. |
| Armas fabricadas | Reparte presupuesto entre daño, velocidad, crítico y penetración; material/perfil redistribuyen puntos. | Faltan rangos nuevos por tier, calidad, nuevos sistemas y perfiles de ballestas/martillo de asedio. |
| Materiales | Hierro, acero, bronce, plata y obsidiana con propiedades reales. | Hay que adaptar sus efectos a los nuevos presupuestos; no hace falta desechar el mecanismo de materiales. |
| Afijos | Un diccionario opcional por arma, seleccionado mediante componente. Daño periódico de veneno/sangrado/fuego/arcano/cristal. | No hay lista de 1–4 afijos según tier, afijos defensivos o potencias/resistencias generales. Armaduras y escudos rechazan componentes ofensivos. |
| Validación | Comprueba tipos, números finitos, rangos básicos y estructura de instancias. | No garantiza límites estadísticos por tier, calidad, tipo o suma de afijos del nuevo diseño. |
| Relación con clase | El generador no altera poder del objeto según clase. | Ya coincide con la independencia de clase propuesta en Crafteo. |

Referencias: [inventario.py](inventario.py), [item.py](item.py), [items.json](items.json), [crafting.py](crafting.py), [crafting.json](crafting.json), [item_factory.py](item_factory.py), [combat_stats.py](combat_stats.py), [weapon_effects.py](weapon_effects.py), [workshop.py](workshop.py).

Ejemplo calculado: fabricar las cuatro piezas con acero y perfil equilibrado da **21 de armadura total en Tier 1**, **47 en Tier 4** y **64 en Tier 5**. Crafteo.md propone 5–17 para Tier 1 y 81–120 para Tier 4. El set estático de hierro suma 17, pero eso no significa que la fabricación ya respete esos límites.

Hay además un fallo concreto relevante para el uso dual: en `MotorJuego._accion_enemigo`, una secundaria se consulta como si siempre tuviera `tipo_secundario`. Con una daga devuelve **`AttributeError: 'Arma' object has no attribute 'tipo_secundario'`**. Se reprodujo en una llamada aislada con un personaje que tenía espada principal y daga secundaria. Debe corregirse al consolidar el equipo; no se corrigió durante esta revisión.

## 4. Efectos, estados y canalización

| Nota | Implementación actual | Trabajo necesario y decisiones pendientes |
|---|---|---|
| Sangrado | Tres mecanismos: sangrado de pasiva en Dungeon, afijo `sangrado` y estado táctico del jefe. Este último hace 4% de HP máximo por carga, hasta 4 cargas, y renueva expiración. El afijo hace daño fijo y renueva sin acumular. | Unificar identidad, aplicación tras impacto, potencia frente a Resistencia Física, duración, acumulaciones y limpieza. Elegir entre las fórmulas alternativas de la nota. La pasiva genérica no está actualmente asignada a clases. |
| Quemadura | Afijo `fuego` con probabilidad y daño periódico fijo; no es un estado `burning` con resistencia térmica y stacks. | Crear Quemadura como estado, su potencia y resistencia, máximo de cargas y extinción. Agua, aceite, congelación y propagación ambiental no están implementados. |
| Derribo | Hay aturdimiento en Dungeon que hace perder una acción, y vulnerabilidad del jefe por romper escudo en táctico. | Crear `knockdown` con Impacto/Estabilidad, renovación, cancelación de canalización, inmunidades y recuperación. No basta renombrar aturdimiento. |
| Desequilibrio | No se encontró `off_balance` ni modificador equivalente de Estabilidad. | Crear estado preparatorio, reducción de Estabilidad y sustitución por Derribo. Resolver valores opcionales sin sumarlos todos automáticamente. |
| Empuje | Existe movimiento voluntario con colisiones evitadas por rutas; no desplazamiento forzado. | Crear dirección, distancia, redondeo, bloqueo por obstáculos/unidades y disparadores de terreno. Caídas y destrucción son extensiones aún no definidas. |
| Interrupción | No hay acciones prolongadas cancelables con el modelo propuesto. | Crear resolución explícita; distinguirla de perder la próxima acción. Definir costes y cooldown tras cancelación. |
| Ruptura de Guardia | El jefe táctico tiene una barra de escudo, ruptura por daño y ventana vulnerable. Dungeon tiene Defender y bloqueo con escudo. | Crear efecto sobre postura/bloqueo activo, comprobación Impacto/Estabilidad y posible Guardia Rota. La barra del jefe es otra mecánica y puede conservarse separadamente. |
| Inamovible | No existe pasiva implementada ni asignada. | Crear modificadores condicionales de estabilidad/desplazamiento/control, vínculo con Rompemuros y rangos. Los valores y evoluciones de la nota son ejemplos. |
| Canalización | Hay cooldowns y duraciones de buffs, pero ninguna máquina de estados de preparación, mantenimiento o carga. | Crear inicio/progreso/ejecución/cancelación; límites de movimiento/defensa/evasión, costes iniciales y periódicos, reembolso y resistencia a interrupción. |

Referencias: [weapon_effects.py](weapon_effects.py), [game_engine.py](game_engine.py), [tactical_combat.py](tactical_combat.py), [tactical_models.py](tactical_models.py), [tactical_board.py](tactical_board.py), [habilidades.py](habilidades.py), [pasivas.py](pasivas.py).

Actualmente los estados se reparten entre atributos de enemigo, diccionarios del motor, `efectos_arma` y `Actor.estados`. Sus momentos de resolución también difieren: el sangrado táctico ocurre al inicio de la actuación, los afijos del enemigo táctico después de su actuación, y las expiraciones tácticas al final de ronda. No existe todavía un contrato común de «turno» para todos los estados propuestos.

El sangrado del jefe táctico se aplica a aliados vivos en su área después de conectar el golpe al objetivo elegido; no tira impacto individual contra cada afectado. Es una regla de encuentro específica que no cumple por sí sola «Sangrado requiere impacto» para cada receptor.

## 5. Clases, habilidades y progresión

| Documento | Definición disponible | Comparación |
|---|---|---|
| Rompemuros | Tanque/control de línea; maza/martillo; Impacto Sísmico, Golpe Demoledor, Inamovible; evolución a Quebrantabaluartes. | Clase por crear. Puede aprovechar equipo y tablero, pero su identidad depende de los sistemas de control aún ausentes. No asumir que sustituye automáticamente al Guardián actual. |
| Verdugo de Cuerdas | Solo título. | No implementado como clase; faltan rol, armas, mecánica y progresión. El ID de encuentro `guardian_verdugo` no equivale a esta clase. |
| Impacto Sísmico | Activa de Rompemuros, nivel 25, maza/martillo, aplica Derribo. | Habilidad por crear. Faltan daño, alcance, área, probabilidad, coste, cooldown y selección de objetivos. Empuje la menciona como fuente, pero su ficha solo declara Derribo. |
| Plantilla de clase | Campos para identidad, recursos, reacciones, traits, hitos, IA y evolución; ejemplo de evolución a nivel 100. | Plantilla editorial, no catálogo implementado ni confirmación de cap 100. El juego limita nivel a 30 y elige clase desde nivel 10. |

Otras entidades están solo referenciadas: Quebrantabaluartes, Golpe Demoledor, Sombra, Guerrero Olvidado y Espectro de Ballesta. El nombre interno táctico `golpe_demoledor` existe en una tabla de multiplicadores, pero no hay ficha de habilidad de clase ni asignación normal a un actor. No permite afirmar que el Golpe Demoledor del nuevo diseño esté implementado.

La Chispa actual es una etiqueta desbloqueada en nivel 30. No hay un sistema funcional de Chispas elementales, traits o evoluciones de clase que satisfaga las relaciones descritas. Estos elementos necesitan definición antes de estimar su implementación.

Referencias: [progression.py](progression.py), [character.py](character.py), [level_system.py](level_system.py), [tactical_models.py](tactical_models.py), [tactical_combat.py](tactical_combat.py).

## 6. Contradicciones y vacíos del diseño

Estas diferencias pertenecen a la documentación, no son errores de implementación que deban resolverse arbitrariamente.

| Asunto | Diferencia o vacío | Propuesta para cerrarlo |
|---|---|---|
| Salud | Índice: +10/nivel. Salud.md: base 50 y +5/nivel. | Elegir una fuente canónica. Recomiendo usar la nota específica de Salud como base de discusión. |
| Defensa y CON | Defensa.md mantiene defensa derivada de CON y `K=50+2L`. Armadura/Mitigación usan K=100, cap 60% y protección sin CON. | Recomiendo que Armadura/Mitigación rijan el modelo y archivar o reescribir Defensa.md una vez acordado. |
| Poder de ataque | Fuerza/Poder usan un multiplicador con raíz. Crafteo §12 usa `DañoBaseArma + PoderAtaque × EscaladoArma`, con poder aditivo. | Elegir si Poder de Ataque es multiplicador o magnitud aditiva. No se pueden mezclar las unidades. |
| Coeficientes de arma | Fuerza ejemplifica daga 0.40, espada 0.75, maza 1.00, martillo 1.20. Crafteo propone grados E–S con otra tabla. | Definir una tabla canónica y su presentación visual; los ejemplos no deben convertirse en dos fuentes divergentes. |
| Dagas y penetración | Crafteo describe penetración baja; Equipamiento describe alta penetración como identidad de doble daga. | Decidir si la fortaleza está en cada daga o en habilidades que combinan ambas. |
| Ataque dual | Primero define secundaria al 50%, luego vuelve a mostrar `DañoSecundaria × 0.50`. | Aclarar que el descuento se aplica una vez sobre daño normal para evitar 25% accidental. Definir la suma de penetración en secuencias frente a golpes combinados. |
| Tier | Crafteo usa conjuntos T2 18–40, T3 41–80, T4 81–120. Armadura/Mitigación presentan rangos orientativos parcialmente distintos. | Separar tabla normativa de fabricación de ejemplos de defensa observada. Decidir Tier 5. |
| Caps de piezas y afijos | Hay cap de conjunto y coeficientes, pero la validación final solo expresa `Armadura ≤ LimiteTier`. | Especificar límite por slot, tratamiento del escudo, equipo de tiers mezclados, afijos y excepciones de material. |
| Precisión y Evasión | Hay fórmula de Precisión y del enfrentamiento; falta fórmula de Evasión como puntuación. Destreza.md está vacía. | Completar Evasión antes de sustituir porcentajes actuales. El mínimo 10% de impacto es un límite formal: con puntuaciones no negativas, la fórmula propuesta no baja de aproximadamente 30%. |
| Impacto | Impacto.md mezcla la potencia de control y una sección «Probabilidad de impacto» de precisión. | Separar «acierto» de «Impacto físico» en nombres y datos. |
| Carga | Umbrales escritos como 0–50, 51–75 y 76–100 dejan huecos si se usan porcentajes decimales. | Usar comparaciones continuas `≤0.50`, `≤0.75`, `≤1`, `>1`. Definir si −10% Evasión es relativo a puntuación y qué significa «sin Evasión» con impacto capado al 95%. |
| Movimiento | Cap natural 6, pero no indica si bonos pueden superarlo ni mínimo tras sobrecarga. | Definir orden de modificadores, cap base/final y piso. Precisar si terreno consume puntos o casillas. |
| Control y estados | Fórmulas limitadas a 5–95%; no resuelven potencia cero, inmunidad o denominador cero. | Definir elegibilidad e inmunidades antes de aplicar el límite. No conceder 5% a una fuente que no puede aplicar el estado. |
| Sangrado | Daño plano + potencia, porcentaje puro e híbrido aparecen como alternativas; stacks 3–5; duración X. | Elegir fórmula, duración, cap y renovación. Definir reducción de regeneración solo si se adopta esa interacción opcional. |
| Quemadura | Duración X; resistencia térmica sin nota; múltiples efectos ambientales opcionales. | Cerrar versión mínima: aplicación, daño, stacks, duración y extinción; separar expansiones ambientales. |
| Empuje | Distancia depende de estabilidad; el redondeo queda abierto y puede producir cero casillas. | Definir redondeo, mínimo, dirección, colisiones y relación con probabilidad de aplicación. |
| Derribo y turnos | Pierde «siguiente acción», dura «1 turno» y cancela canalización. No hay regla de protección contra cadenas. | Definir acción/ronda/turno, limpieza del estado y resistencia temporal si se desea evitar control continuo. |
| Canalización | Enumera alternativas de costes, restricciones, cancelación y reembolso. | Definir valores por habilidad y defaults del sistema; aún no hay una habilidad completamente especificada para validarlo. |
| Inamovible | Valores iniciales incluyen varias ventajas, pero evolución I solo menciona Estabilidad. Contacto con suelo/correr/saltar no está modelado. | Elegir qué es requisito real de la primera versión y qué se reserva para estados futuros. |
| Clases y acceso a armas | Crafteo dice que una clase no debe ser obligatoria para usar un arma; Equipamiento permite requisitos de clase. | Definir si son excepciones o si los requisitos de clase se eliminan para armas comunes. |
| Progresión | Plantilla con evolución a 100 y textos sobre cientos de niveles, sin curva aprobada ni máximo definitivo. | No extrapolar el cap o hitos a partir de una plantilla. Cerrar cap, puntos, evoluciones y energía conjuntamente. |

### Organización de las notas

- Sangrado y Quemadura están en **Pasivas**, pero sus fichas los definen como estados de daño periódico.
- Inamovible está en **Estados**, pero su ficha lo define como pasiva.
- `Evasión vs Precisión.md` se titula Precisión; faltan notas propias o aliases de Evasión y Precisión.
- Hay diferencias de mayúsculas entre enlaces y nombres: Resistencia Física/física, Regeneración de Vida/vida, Mitigación de Daño/daño, etc. Conviene normalizar nombres o aliases.
- Ignorando mayúsculas y excluyendo la plantilla, hay **18 nombres de destino sin nota propia**: Chispa de Fuego, Congelación, Desplazamiento, En llamas, Energía, Espectro de Ballesta, Evasión, Golpe Demoledor, Guardia Rota, Guerrero Olvidado, Martillo de asedio, Maza, Precisión, Quebrantabaluartes, Resistencia Térmica, Retroceso, Sombra y Vacío. Algunos están descritos parcialmente dentro de otras notas; esto no significa 18 sistemas totalmente indefinidos.

## 7. Qué conservar, modificar, crear y retirar

**Conservar como base:** slots e inventario; identidades de objetos; bóveda y transferencias; taller y previsualización; carga de catálogos; guardado; separación de bloqueo/mitigación; tablero, rutas, alcance y línea de visión; escenarios, registro y simuladores. Conservar infraestructura no implica conservar su balance actual.

**Modificar:** derivados de atributos; resolución de acierto y daño; iniciativa de ambos modos; movimiento; sobrecarga; equipo secundario y dual; esquemas de objetos; presupuestos y validaciones de crafteo; modelos de enemigo; progresión y asignación de habilidades; interfaz y serialización.

**Crear:** Precisión como atributo, Evasión como puntuación, Impacto, Estabilidad, resistencia física general, regeneración; calidad y afijos múltiples; estados de control generalizados; Quemadura completa y resistencia térmica; canalización; Inamovible; Rompemuros e Impacto Sísmico cuando su ficha quede definida.

**Candidatos a retirar o sustituir después del acuerdo:**

1. CON → Salud, armadura y carga, si prevalecen las nuevas notas específicas.
2. Evasión como porcentaje independiente del atacante.
3. Velocidad → acciones adicionales de Dungeon, si Iniciativa rige también ese modo.
4. Escalado lineal antiguo de daño y K=40 sin cap.
5. Suma de daga secundaria al golpe principal, al implementar golpes independientes.
6. Implementaciones duplicadas de sangrado, una vez migradas a un contrato común.
7. Tablas antiguas de fabricación que resulten reemplazadas, manteniendo compatibilidad de objetos guardados.

No hay evidencia en `Game Design` para eliminar automáticamente la tienda, la bóveda, el Dungeon, las tres clases anteriores, el jefe con barra de escudo o todo el cliente Godot. Que una pieza no aparezca en una carpeta incompleta no constituye una decisión de retirarla.

## 8. Impacto transversal y orden propuesto

1. **Cerrar el contrato numérico:** Salud, Armadura/Defensa, fórmula de poder, Evasión, iniciativa/acciones y progresión. Marcar explícitamente qué números son provisionales.
2. **Consolidar estadísticas y resolución compartidas:** exponer los nuevos derivados y dar el mismo significado a acierto, daño, bloqueo y penetración en ambas rutas. Incluir enemigos desde el principio.
3. **Revisar equipo y fabricación:** esquema de objetos, calidad, afijos y caps; resolver armas duales; definir migración de objetos existentes antes de retirar campos.
4. **Consolidar estados y control:** eventos de inicio/final de actuación y ronda, resistencias, duración, acumulaciones, inmunidades, muerte y desplazamiento. Incorporar canalización cuando haya una habilidad de referencia definida.
5. **Implementar una clase de extremo a extremo:** Rompemuros, habilidad accesible, equipo compatible, pasiva, IA, presentación y guardado. Así se comprueba que el diseño funciona integrado.
6. **Rebalancear y ampliar contenido:** enemigos, encuentros, economía y progresión; después incorporar otras clases y sistemas aún incompletos.

La interfaz también requiere cambios concretos: `web/app.js` anuncia CON como vida/armadura; los paneles muestran Evasión en porcentaje y Velocidad; `web/tactical.html` describe movimiento 2–4 por velocidad. Taller y fichas no muestran calidad ni las nuevas estadísticas. Hay que actualizar datos y textos a la vez que las reglas.

La persistencia reconstruye vida usando las fórmulas vigentes y valida nivel/clase al cargar. Los objetos custom guardan sus estadísticas completas. Añadir campos obligatorios, quitar clases o cambiar el límite de nivel puede invalidar guardados; cambiar fórmulas puede alterar una build al cargar sin modificar su archivo. La migración debe ser parte del trabajo, no una limpieza posterior.

Referencias: [state.py](state.py), [web/app.js](web/app.js), [web/character-panel.js](web/character-panel.js), [web/tactical.js](web/tactical.js), [web/tactical.html](web/tactical.html), [web/workshop.js](web/workshop.js), [character_roster.py](character_roster.py), [item_factory.py](item_factory.py), [persistence.py](persistence.py).

## 9. Comprobaciones realizadas y límites

- Inventario y lectura de los 33 Markdown, comparación de enlaces y búsqueda de sistemas tanto por nombres españoles como IDs propuestos.
- Inspección de modelos, fórmulas, catálogos, resolutores, progresión, equipo, crafteo, persistencia y consumidores de estadísticas en clientes.
- Cálculos directos en memoria para personaje, mitigación y fabricación. No se fabricó equipo en partidas reales.
- Comprobación de que los árboles de clase actuales están vacíos y de que la construcción táctica deja sin asignar habilidades tácticas/única.
- `python3 -B simulate_tactical.py --n 20 --seed-base 1234`: 5 perfiles × 20 semillas, **100 combates**. Todos finalizaron sin excepción; los cinco perfiles obtuvieron 0% de victorias y 0% de rupturas exitosas en ese encuentro. Los cambios de solo IA no produjeron mejoras en esta muestra, coherente con las habilidades sin asignar.
- Dos ejecuciones con tablero, semilla 1234 y grupo de prueba: Patrulla en ruinas, victoria en 9 rondas; Guardián del patio, derrota en 12 rondas.
- Reproducción aislada del error de secundaria tipo daga en la respuesta enemiga de Dungeon.

Las simulaciones usan fixtures del simulador, no el roster del usuario, y la tanda de 100 combates usa el encuentro del simulador sin tablero. Sirven para comprobar comportamiento actual y detectar límites de integración; no estiman el balance global ni prueban las fórmulas futuras.

El archivo `test_crafting_economy.py` mencionado entre las pestañas del IDE no está presente en el árbol disponible en disco; no se pudo ejecutar. No se presenta esta revisión como una suite de pruebas aprobada. Tampoco se han probado aquí animaciones, navegación visual completa ni todos los flujos de guardado.


## 10. Inventario completo de fuentes de diseño

Cada nota está incluida en la comparación anterior. Se enlazan los archivos originales para facilitar su revisión; ninguno fue editado.

| Carpeta | Nota |
|---|---|
| 01 - Clases | [Rompemuros](<Game Design/00 - Indices/01 - Clases/Rompemuros.md>) |
| 01 - Clases | [Verdugo de Cuerdas](<Game Design/00 - Indices/01 - Clases/Verdugo de Cuerdas.md>) |
| 03 - Habilidades | [Impacto Sísmico](<Game Design/00 - Indices/03 - Habilidades/Impacto Sísmico.md>) |
| 04 - Pasivas | [Quemadura](<Game Design/00 - Indices/04 - Pasivas/Quemadura.md>) |
| 04 - Pasivas | [Sangrado](<Game Design/00 - Indices/04 - Pasivas/Sangrado.md>) |
| 05 - Estados | [Inamovible](<Game Design/00 - Indices/05 - Estados/Inamovible.md>) |
| 06 - Estadísticas | [Constitución](<Game Design/00 - Indices/06 - Estadísticas/Constitución.md>) |
| 06 - Estadísticas | [Destreza](<Game Design/00 - Indices/06 - Estadísticas/Destreza.md>) |
| 06 - Estadísticas | [Estadísticas](<Game Design/00 - Indices/06 - Estadísticas/Estadísticas.md>) |
| 06 - Estadísticas | [Fuerza](<Game Design/00 - Indices/06 - Estadísticas/Fuerza.md>) |
| 09 - Sistemas | [Armadura](<Game Design/00 - Indices/09 - Sistemas/Armadura.md>) |
| 09 - Sistemas | [Canalización](<Game Design/00 - Indices/09 - Sistemas/Canalización.md>) |
| 09 - Sistemas | [Capacidad de carga](<Game Design/00 - Indices/09 - Sistemas/Capacidad de carga.md>) |
| 09 - Sistemas | [Crafteo](<Game Design/00 - Indices/09 - Sistemas/Crafteo.md>) |
| 09 - Sistemas | [Defensa](<Game Design/00 - Indices/09 - Sistemas/Defensa.md>) |
| 09 - Sistemas | [Equipamiento](<Game Design/00 - Indices/09 - Sistemas/Equipamiento.md>) |
| 09 - Sistemas | [Estabilidad](<Game Design/00 - Indices/09 - Sistemas/Estabilidad.md>) |
| 09 - Sistemas | [Evasión vs Precisión](<Game Design/00 - Indices/09 - Sistemas/Evasión vs Precisión.md>) |
| 09 - Sistemas | [Impacto](<Game Design/00 - Indices/09 - Sistemas/Impacto.md>) |
| 09 - Sistemas | [Iniciativa](<Game Design/00 - Indices/09 - Sistemas/Iniciativa.md>) |
| 09 - Sistemas | [Mitigación de daño](<Game Design/00 - Indices/09 - Sistemas/Mitigación de daño.md>) |
| 09 - Sistemas | [Movimiento](<Game Design/00 - Indices/09 - Sistemas/Movimiento.md>) |
| 09 - Sistemas | [Penetración](<Game Design/00 - Indices/09 - Sistemas/Penetración.md>) |
| 09 - Sistemas | [Poder de ataque](<Game Design/00 - Indices/09 - Sistemas/Poder de ataque.md>) |
| 09 - Sistemas | [Regeneración de vida](<Game Design/00 - Indices/09 - Sistemas/Regeneración de vida.md>) |
| 09 - Sistemas | [Resistencia física](<Game Design/00 - Indices/09 - Sistemas/Resistencia física.md>) |
| 09 - Sistemas | [Salud](<Game Design/00 - Indices/09 - Sistemas/Salud.md>) |
| 11 - Efectos | [Derribo](<Game Design/00 - Indices/11 - Efectos/Derribo.md>) |
| 11 - Efectos | [Desequilibrio](<Game Design/00 - Indices/11 - Efectos/Desequilibrio.md>) |
| 11 - Efectos | [Empuje](<Game Design/00 - Indices/11 - Efectos/Empuje.md>) |
| 11 - Efectos | [Interrupción](<Game Design/00 - Indices/11 - Efectos/Interrupción.md>) |
| 11 - Efectos | [Ruptura de guardia](<Game Design/00 - Indices/11 - Efectos/Ruptura de guardia.md>) |
| 99 - Plantillas | [Clase](<Game Design/99 - Plantillas/Clase.md>) |
