# Base de IA enemiga

## Verificación de la propuesta

Combinar políticas simples con comportamientos configurables es una base razonable.
La selección por utilidad permite comparar acciones u objetivos según su conveniencia:
[Building Utility Decisions into Your Existing Behavior Tree, Game AI Pro](https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter10_Building_Utility_Decisions_into_Your_Existing_Behavior_Tree.pdf).
Esto respalda la técnica, no las promesas de ahorrar 90% del trabajo o conseguir 80%
de profundidad: esas cifras no tienen evidencia en la propuesta y requieren medición.

Correcciones de diseño:

- Tres cerebros son una elección de alcance, no una ley de diseño. Incluso una bestia
  decide, comprueba blancos y busca rutas. Reducir reevaluaciones no elimina ese coste.
- Con siete tags hay 7 combinaciones de uno y 21 parejas sin orden: tres cerebros dan
  84 perfiles de uno o dos tags, o 87 incluyendo perfiles sin tags. No son necesariamente
  84 conductas diferentes ni todas compatibles. El cálculo `3 × 7 × 2 = 42` no cuenta parejas.
- Cazar sanadores e ignorar provocación son reglas distintas. Aquí la inmunidad es una
  opción explícita, desactivada por defecto. Un tanque no puede provocar a quien la ignore.
- La huida se decide antes del ataque y consume la acción. No hay ataque gratuito seguido
  de retirada. “Nunca cambia” necesita excepción cuando desaparece el objetivo.
- La formación indica posición/función; no determina inteligencia ni armadura.
- El archivo actual de arquetipos contiene seis, no cuatro, y ninguno exige curación.
  Los roles se declaran por capacidades, sin deducirlos del arma, chispa o nombre de clase.

## Código y responsabilidades

| Archivo | Responsabilidad |
| --- | --- |
| `enemy_ai.py` | Perfil validado, percepción compacta, memoria por actor y decisiones |
| `tactical_ai.py` | Conserva las prioridades de los personajes jugadores |
| `tactical_models.py` | Encuentro con perfil opcional; actores con roles y línea explícitos |
| `tactical_combat.py` | Adaptador del jefe: visión, rutas, ejecución y eventos |
| `tactical_board.py` | Conserva movimiento, costes, obstáculos, visión y trampas |
| `simulate_enemy_ai.py` | Demo de un jefe con dos tags, semilla y tablero |
| `test_enemy_ai.py` | Casos de comportamiento e integración |

Se conservan daño, iniciativa, habilidades, escudo, sangrado y presentación. El plan PDF
pide cambios incrementales y separar decisión, resolución y log: esta extensión sigue
esa separación. Copias de los dos archivos existentes modificados en `tmp/ia_checkpoint/`.

## Contrato

Una instancia de `CerebroEnemigo` por actor y por combate. Llamar a `elegir` exactamente
una vez por turno disponible del actor; no usarlo para previews de UI porque avanza memoria.
La decisión no modifica vida, posiciones, cooldowns ni recursos.

El llamador entrega solo enemigos percibidos, vivos y con ruta válida mediante `BlancoIA`:
ID único, vida como fracción 0..1, coste de acercamiento, defensa, amenaza observable 0..1,
roles semánticos y línea. Sin enemigos válidos devuelve `esperar`. IDs estables desempatan
sin azar. No conserva posiciones ocultas ni persigue blancos que ya no puede percibir.

El adaptador actual filtra con visión y rutas del tablero. Sin tablero todos los vivos
se consideran visibles y el coste espacial es cero. Amenaza usa `ataque / (ataque + 100)`
como aproximación provisional; no mide daño o curación históricos. Los roles proceden
de `Actor.roles_ia` y de la capacidad `curar`; `Actor.linea_ia` vale `frontal` por defecto.
La línea es metadata declarada, no se recalcula por coordenadas.

## Cerebros

| Cerebro | Selección |
| --- | --- |
| `bestia` | En cada turno selecciona el menor coste de ruta, después de preferencias por tags |
| `soldado` | Fija una orden inicial o recibe un ID prioritario; la mantiene mientras sea válida |
| `comandante` | Reevalúa en turnos propios 1, 3, 5…; intervalo configurable |

Un objetivo inválido fuerza nueva elección sin esperar el intervalo. El soldado conserva
su orden: usa otro objetivo si no está disponible y vuelve cuando la percibe de nuevo.
El comandante puntúa `2 × amenaza + (1 - vida_pct) - 0.1 × coste_ruta` dentro del grupo
preferido. Son pesos iniciales para ajustar con simulaciones, no balance definitivo.

## Precedencia y tags

Orden: sin blancos → retirada → provocación → fijación fanática → protección →
cadencia del cerebro → selección. Los tags que filtran objetivos se recorren en el orden
configurado y gana el primero con candidatos. La orden válida del soldado prima sobre
esos filtros. Esto hace explícitos los conflictos en lugar de depender de un orden accidental.

| Tag | Regla implementada |
| --- | --- |
| `cazador_healer` | Prefiere capacidad `sanador`; no concede inmunidad a provocación |
| `rompe_tanque` | Prefiere mayor defensa; no concede penetración ni daño extra |
| `oportunista` | Prefiere menor fracción de vida entre blancos por debajo de 30% |
| `fanatico` | Fija el objetivo mientras siga válido; provocación puede sustituirlo temporalmente |
| `cobarde` | Bajo 30%, consume dos turnos en retirada, una sola vez por combate |
| `protector` | Devuelve `proteger` al aliado válido más herido bajo 40% |
| `asesino_backline` | Prefiere rol `dano` en línea `retaguardia` |

`cobarde` y `fanatico` juntos se rechazan. Máximo tres tags distintos. La retirada del
jefe aumenta localmente la distancia al enemigo más próximo respetando costes, ocupación,
muros, inmovilización y trampas. No busca una ruta global de escape: puede quedar encerrado.
Sin tablero consume la acción y registra `retirada_bloqueada`.

La provocación se recibe en el núcleo como `provocado_por`; el adaptador lee el estado
`provocado` con `origen_id` y `vence`. Todavía no existe una habilidad nueva que lo aplique.

## Activación y comprobación

Por compatibilidad `Encuentro()` mantiene el jefe original. Para activar la base:

```python
from enemy_ai import PerfilIA
from tactical_models import Encuentro

encuentro = Encuentro(perfil_ia=PerfilIA(
    cerebro="comandante",
    tags=("rompe_tanque", "cobarde"),
    intervalo=2,
))
# Entregar encuentro a CombatResolver como habitualmente.
```

También admite un diccionario en `perfil_ia`, útil para futuros catálogos de datos.
Cada decisión registra `decision_ia`: tipo, objetivo, motivo y si reevaluó. No hay controles
nuevos en Godot/web; se configura por Python. Ejecutar:

```sh
python3 simulate_enemy_ai.py --cerebro comandante --seed 1234
python3 -m unittest test_enemy_ai -v
python3 -m unittest discover -q
```

Validación de esta entrega: 42 pruebas descubiertas, 41 aprobadas y una omitida
por la suite existente. Las diez pruebas nuevas pasan. La demo con semilla 1234
termina en nueve rondas y registra reevaluaciones en turnos alternos. No constituye
una prueba de balance ni de rendimiento masivo.

## Límites y siguiente integración

El núcleo, el resolver y el tablero admiten grupos. La patrulla de prueba tiene tres rivales con memoria individual; el encuentro de jefe se conserva. `protector` ya elige a quién proteger pero aún necesita
un ejecutor de interposición, casillas legales y reglas de interceptación. En este encuentro
el jefe no tiene aliados que proteger. `asesino_backline` selecciona retaguardia, pero no
implementa movimiento de flanqueo. Ninguno de esos tags concede habilidades inexistentes.
Mandar esqueletos requiere órdenes de escuadrón, invocación y capacidades de invocación.

Para ampliar: implementar ejecución de protección/flanqueo;
conectar roles y perfiles a los catálogos de contenido cuando estén definidos. Elegir habilidades
con recursos, cooldown y alcance es otra capa: hoy el jefe ejecuta su ataque existente.

No se promete rendimiento con 200 enemigos. El selector recorre candidatos; la integración
calcula una ruta por blanco visible por turno. El ahorro de cadencia afecta la puntuación,
no esas rutas. Medir escenarios reales antes de agregar caché, campos de distancias o límites
de candidatos; invalidar cachés al cambiar terreno/ocupación.

## Respuestas tácticas propuestas para tus arquetipos

Son hipótesis de diseño, pendientes de implementar habilidades y balancear:

| Conducta enemiga | Respuesta posible |
| --- | --- |
| Caza sanadores | Rompemuros bloquea pasos; Cazarrecompensas inmoviliza al perseguidor |
| Rompe tanques | Rompemuros atrae atención mientras Espectro de Ballesta prepara daño |
| Busca retaguardia | Guerrero Olvidado controla accesos; Sombra prepara trampas |
| Cobarde | Cazarrecompensas impide la retirada; Espectro castiga desde distancia |
| Fanático | Su blanco lo lleva a una zona controlada por Guerrero Olvidado |
| Protector | Presionar a un aliado revela al guardia; Verdugo de Cuerdas busca aislarlo |
| Oportunista | Retirar al herido y cerrar rutas con Rompemuros |

Estos ejemplos no suponen un taunt ni un healer obligatorio en tus clases.

Actualización: tres escenarios fijos disponibles desde la UI; se eliminó la edición manual de terreno y trampas. La patrulla conoce las posiciones desplegadas de ambos bandos y usa rutas para aproximarse, incluso alrededor de muros; cada ataque exige alcance y visión. No hay niebla de guerra. El jefe conserva su adaptador anterior.
