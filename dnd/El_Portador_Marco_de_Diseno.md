# El Portador — Marco de diseño para el roguelite

## 0. Idea estructural central (revisada: sin permadeath)

El juego real tiene dos partes, y ninguna usa permadeath. Por suerte, el propio lore ya contiene la justificación perfecta para ambas, sin tocar la mecánica de reencarnación de chispas.

### Parte 1 — La mazmorra de 50 habitaciones = "El Bastión del Concilio"

Tu documento de mundo dice: *"Existen investigaciones, pruebas, supersticiones, acusaciones y torturas alrededor de estos casos"* y que *"el Concilio puede trasladarlo a Solerne con un propósito desconocido."* Eso convierte la mazmorra en algo concreto: una **instalación de prueba** (del Concilio, la Fe del Orden o una casa noble) donde arrojan a sospechosos de infestación a habitaciones con peligro creciente para observar si manifiestan poder y medir su límite.

Con este marco:
- "Morir" en una habitación no es morir de verdad: te recapturan (porque te necesitan vivo para seguir observándote/catalogándote) y te devuelven a la habitación 1.
- Conservas estadísticas e ítems porque son evidencia de lo que ya demostraste, no algo que "se resetea".
- El coste vital de los poderes (agotamiento, envejecimiento) es tu tensión de riesgo dentro del run: jugar agresivo te acerca a un colapso que corta el intento actual, sin que eso implique perder progreso permanente.
- La dificultad procedural creciente se explica sola: los examinadores escalan el peligro a propósito para encontrar el límite de cada sospechoso.

### Parte 2 — El táctico de escuadrones = "operaciones"

Tu documento también dice: *"El ejército emplea secretamente infestados para localizar y capturar a otros."* Los personajes que demuestran suficiente compatibilidad en la Criba no son eliminados de inmediato: son reclutados (en secreto) para operaciones donde varios infestados trabajan juntos bajo el mando de una facción (Concilio, una casa noble, o incluso una banda como los Skarhvan si el jugador se inclina hacia el crimen).

Esto conecta ambas partes de forma orgánica:
- Los personajes entrenados en la Criba pasan a formar escuadrones de 3 para misiones.
- El feedback de derrota táctica puede enmarcarse *in-universe* como el informe post-misión de un oficial, o como la propia chispa quejándose de la táctica (útil sobre todo con vínculos "conflictivos", ver sección 3).
- Te da progresión narrativa natural: Criba (origen y prueba individual) → Operaciones (uso institucional/colectivo del poder) → posible traición o fuga más adelante si quieres una campaña más larga.

## 1. Plantilla de origen (generador de hitos narrativos)

Generalizando el arco de Eliah/Ignis, cada chispa jugable necesita solo estos 6 beats para tener un "capítulo 1" propio:

1. **Necesidad** — condición social/económica que hace vulnerable al futuro huésped.
2. **Detonante** — una decisión cotidiana lo mete en una situación límite ligada al dominio de la chispa.
3. **Quiebre** — el huésped llega a un límite vital; la chispa interviene para salvarlo.
4. **Tutorial** — se descubren los límites, ventajas e inmunidades ligadas a esa chispa.
5. **Verdad** — el huésped revela (o le descubren) su condición ante alguien cercano.
6. **Cacería** — una facción reacciona: aparece el antagonista/jefe de esa clase.

Para crear una clase nueva, solo rellena estos 6 campos. No hace falta escribir la novela completa, basta con una escena por beat (funciona como cinemática corta o texto de introducción de personaje en el roguelite).

## 2. Arquetipos jugables por chispa

| Chispa | Dominio | Verbos de poder | Tipo de coste | Personalidad típica | Quién la caza |
|---|---|---|---|---|---|
| **Ignis** (Fuego) | Calor, combustión | Generar/manipular/apagar fuego, transferir calor | Agotamiento, insomnio, quemazón interna | Melancólica, melodramática, teatral | Skarhvan (contrabandistas), Guardia Civil |
| **Caos** | Termodinámica/entropía | Acelerar desorden, romper estructuras, generar entropía local | Envejecimiento acelerado, deterioro físico | Primigenia, indiferente, casi inhumana | Concilio (por su rareza y peligrosidad) |
| **Vínculo** | Gravedad | Atraer/repeler masas, anclar cuerpos, alterar peso | Dolor articular, fragilidad ósea | Primigenia, protectora pero posesiva | Ejército (uso táctico) |
| **El Arquitecto** | Química | Transmutar sustancias, acelerar/inhibir reacciones, crear venenos o curas | Daño a órganos internos, intoxicación propia | Metódico, obsesivo, frío | Gremio de Alquimistas, Fe del Orden |
| **El Juez** | Biología/evolución | Mutar tejido, acelerar curación, inducir enfermedad o mutación | Deformidad, pérdida de identidad física | Implacable, evaluador, poco empático | Sanadores, Fe del Orden |
| **Sombra** *(propuesta)* | Oscuridad/ausencia de luz | Ocultar, silenciar, moverse entre sombras | Aislamiento sensorial, pérdida de reflejo/imagen | Susurrante, manipuladora, paranoica | Contrabandistas rivales, cazarrecompensas |
| **Eco** *(propuesta)* | Sonido/vibración | Amplificar, anular sonido, ondas de choque | Sordera progresiva, dolor auditivo | Caótica, ruidosa, impulsiva | Marineros (por sabotaje a barcos) |
| **Marea** *(propuesta)* | Agua/fluidos | Controlar líquidos, presión hídrica, corrosión por humedad | Deshidratación, hinchazón, ahogo interno | Cíclica, cambiante, imprevisible | Gremio de Marineros, Aduana |

Puedes seguir esta tabla como base y añadir más chispas menores (viento, óxido/corrosión, luz, frío, etc.) usando la misma estructura de columnas.

## 3. Eje secundario: tipo de vínculo (subclases sin inventar más chispas)

Para multiplicar variedad sin crear más chispas, cruza cada chispa con un "tipo de relación" entre huésped y entidad. Esto te da subclases jugables con el mismo poder base pero distinto estilo de juego:

- **Armonioso** — huésped y chispa cooperan; menor coste vital, pero menos potencia bruta. Recompensa juego consistente/defensivo.
- **Conflictivo** — la chispa presiona/manipula constantemente; mayor potencia, pero riesgo de que tome el control brevemente en momentos críticos (mecánica de "posesión temporal" como riesgo/recompensa).
- **Parasitario** — la chispa drena activamente al huésped incluso sin usar poder; run más corta pero con habilidades pasivas más fuertes desde el inicio.
- **Dominante** — el huésped controla más de lo normal a la chispa; poder más limitado y predecible, pero inmune a la manipulación/mentiras de la entidad (relevante porque, según tu lore, las chispas pueden mentir sobre sus capacidades).

Cada combinación (chispa × tipo de vínculo) es esencialmente una build jugable distinta con el mismo lore base.

## 4. Categorías de items ancladas al mundo

- **Alquímicos** (Gremio de Alquimistas): pólvora, venenos, catalizadores que amplifican o distorsionan el poder de una chispa; armas de fuego artesanales (raras, poco fiables, coherentes con tu lore de que aún no están industrializadas).
- **De contrabando**: herramientas para ocultar mercancía o identidad, mapas de rutas clandestinas, sobornos, disfraces de gremio.
- **Gremiales**: equipo que da acceso legítimo temporal (herramientas de estibador, sellos de aduana falsificados, cartas de recomendación como la de Tomás).
- **Religiosos/anti-chispa** (Fe del Orden): grilletes o símbolos "purificadores" que dificultan el uso de poder, textos que dan pistas falsas sobre las chispas (coherente con que la religión miente sobre su naturaleza).
- **Reliquias de huéspedes anteriores**: objetos personales de huéspedes muertos de la misma chispa; ideales como sistema de meta-progresión entre runs (desbloqueos permanentes, mini-historias opcionales, easter eggs de "santos y monstruos" mencionados en tu lore).

## 5. Roles tácticos para el modo de operaciones (equipos de 3)

Para que el sistema de feedback de derrota tenga algo concreto que señalar ("faltó control de área", "no tenías sanador", "tu tanque no aguantó"), conviene que cada chispa tenga un rol táctico claro además de su sabor narrativo:

| Chispa | Rol táctico | Contador natural (para el feedback de derrota) |
|---|---|---|
| Ignis (Fuego) | Daño sostenido/área | Débil si el enemigo controla oxígeno/combustible (ej. enemigos de Marea) |
| Vínculo (Gravedad) | Tanque/control de posición | Débil ante enemigos con daño a distancia que evitan el agarre |
| Caos | Daño explosivo de alto riesgo | Débil en peleas largas por su propio desgaste acelerado |
| El Arquitecto (Química) | Debuff/control de estado (veneno, corrosión) | Débil ante enemigos con regeneración biológica (contraparte de El Juez) |
| El Juez (Biología) | Soporte/curación/mutación | Débil ante daño puro de alta velocidad que no da tiempo a curar |
| Sombra | Sigilo/asesino de objetivo único | Débil en combates con mucha luz/detección temprana |
| Eco | Control de área/aturdimiento | Débil ante enemigos con inmunidad o resistencia a efectos |
| Marea | Control de terreno/daño over-time | Débil ante enemigos de fuego que evaporan su ventaja |

Con esta tabla, un equipo de 3 fallido puede diagnosticarse con reglas simples: ¿tenían tanque?, ¿tenían control de área o solo daño puntual?, ¿alguien cubría la debilidad elemental del enemigo? Eso te da contenido automático para el mensaje de feedback sin tener que scriptear cada derrota a mano.

## 6. Cómo seguir usando esto

Para cada chispa nueva que quieras añadir al roster jugable:
1. Rellena la fila de la tabla (dominio, verbos, coste, personalidad, cazadores).
2. Aplica la plantilla de 6 beats para generar su escena de origen.
3. Elige o combina un tipo de vínculo para definir el estilo de juego.
4. Diseña 2-3 items de las categorías de la sección 4 que encajen específicamente con su dominio.
5. Asígnale un rol táctico y un contador (sección 5) para que tenga sentido tanto en la Criba como en operaciones.

Con este proceso puedes generar una clase jugable completa (lore + mecánica de mazmorra + rol táctico + items) en una sesión de trabajo, sin necesitar una novela por personaje.
