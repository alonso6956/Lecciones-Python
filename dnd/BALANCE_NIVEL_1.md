# Parada y balance de entrada

Revisión solicitada tras observar derrotas del personaje de nivel 1.

## Correcciones

- Parada por daño medio sin reducir primero a la mitad el arma defensora:
  completa con ratio ≥1, parcial con ratio ≥0.60, débil por debajo.
  Reducciones de 50%, 25% y 10%; solo completa quita una acción y habilita
  la oportunidad de contraataque. Poderoso aumenta la presión ×1.25;
  rápido no admite defensa activa. El escudo conserva su modelo independiente.
- Antes, la intención se deducía comparando el daño escalado aleatorio contra
  límites sin escalado. Eso sesgaba la frecuencia hacia ataques poderosos y
  eliminaba los normales de algunas combinaciones. Ahora se elige la intención
  independientemente: 25% rápido, 60% normal, 15% poderoso.
- Poderoso: daño ×1.5, prioridad baja y prohibición de usarlo consecutivamente.
  Tras uno, su probabilidad se convierte en normal hasta ejecutar otra acción.
  Una acción perdida no elimina esta restricción. Las habilidades mantienen sus
  propios multiplicadores y cooldowns.
- Tras probar la nueva parada, se redujo el daño base de Goblins y Esqueletos de
  3 a 2. No se modificaron su equipo, HP, atributos, iniciativa ni recompensas;
  las demás razas conservan su daño base. Los 50 HP iniciales se mantienen.
- Primera habitación: solo Goblins. Desde la segunda se conserva la tabla
  anterior de Goblins/Esqueletos. La medición muestra que los Esqueletos Guerrero
  y Bárbaro no son apropiados para presentar el combate a un personaje mínimo.

## Medición

`simulate_level_one.py --n 500`: 6.000 duelos en total, 500 por combinación de
raza, arquetipo y política. Semillas 0–499. Personaje de nivel 1 con Fuerza,
Destreza y Constitución 1, espada básica 3–5, 50 HP, sin armadura, escudo,
consumibles ni habilidades. Usa el motor real, incluida evasión y regeneración;
los finales del duelo no guardan personajes ni conceden progreso.

| Enemigo | Solo atacar | Defender si permite parada completa; atacar en otra situación |
| --- | ---: | ---: |
| Goblin Rogue | 99,8% | 81,0% |
| Goblin Guerrero | 71,2% | 91,6% |
| Goblin Bárbaro | 75,6% | 75,6% |
| Esqueleto Rogue | 96,6% | 43,8% |
| Esqueleto Guerrero | 8,8% | 0,0% |
| Esqueleto Bárbaro | 13,6% | 13,6% |

Son políticas simples, no un jugador óptimo. No incluyen mejora de equipo,
consumibles ni gestión de la expedición completa. Defender indiscriminadamente
puede alargar un combate y perjudicar al personaje; una parada no causa daño
al enemigo por sí sola. Los Esqueletos requieren mejor preparación que los
Goblins y no se presentan como encuentros iniciales equivalentes.

En la medición previa de 100 semillas, solo atacar ganaba 67% contra Bárbaro
Goblin y 44% contra Guerrero Goblin. Con solo la nueva parada y el nuevo ataque
poderoso, pero antes del ajuste de daño base, daban 58% y 30%: la fórmula por sí
sola no resolvía el presupuesto ofensivo. Esa comprobación motivó ajustar el
daño, en lugar de aumentar globalmente la vida o la mitigación del jugador.

El Bárbaro Goblin inflige 6,6–9,9 de daño normal bruto, media 8,25, y 9,9–14,85
de poderoso, media 12,375. Sin defensas ni regeneración, 50 HP equivalen a unas
6,1 veces su daño normal medio. Los daños a salud se redondean al resolver.

La espada básica real tiene media 4, no 7 como el ejemplo conceptual. Frente a
la maza de media 6 produce parada parcial contra normal y débil contra poderoso.
Un arma de media 6 consigue completa contra normal; necesita media 7,5 contra
poderoso. No se alteró el catálogo para forzar una parada completa inicial.

## Validación

La suite cubre los límites de ratio, ejemplos del diseño, presión poderosa,
rápidos, escudo fiable, selección de intención, daño ×1.5, prioridad baja,
restricción de consecutivos y tabla del primer encuentro, además de las
regresiones de combate, crafteo, equipo y persistencia existentes.

Resultados detallados locales: `.local/level_one_balance.json`.
