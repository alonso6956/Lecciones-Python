# Sistema de Defensa, Parada y Contraataque

## Identidad

- ID interno: `defense_parry_system`.
- Tipo: sistema de combate.
- Función: ofrecer defensa activa con arma o escudo, independiente de la Armadura.

[[Defender]] no aumenta la [[Armadura]]. Sin escudo utiliza únicamente el arma
principal para realizar una Parada. Con [[Escudo]] utiliza su Bloqueo activo.
La Armadura mantiene su mitigación pasiva.

## Poder de Parada y presión del ataque

`DañoMedioArma = (DañoMinimo + DañoMaximo) / 2`

`PoderParada = DañoMedioArmaDefensor`

`PresionAtaque = DañoMedioArmaAtacante × ModificadorAtaque`

`RatioParada = PoderParada / PresionAtaque`

| Ataque | Modificador de presión |
| --- | --- |
| Normal | ×1.00 |
| [[Ataques poderosos|Poderoso]] | ×1.25 |
| [[Ataques rápidos|Rápido]] | No admite Parada |

La comparación usa la media del arma, nunca la tirada aleatoria del golpe.
No incluye Fuerza, críticos, habilidades, estados ni bonificaciones situacionales.
El daño real sigue teniendo su tirada normal. Cada golpe utiliza su propia arma.
Una segunda arma no aumenta el poder de la Parada; necesitaría una habilidad,
pasiva, estilo o trait que declare expresamente esa excepción.

## Grados de defensa

| Ratio | Resultado | Daño restante | Control |
| --- | --- | --- | --- |
| ≥1.00 | Parada completa | 50% | Atacante pierde su siguiente acción; habilita Contraataque |
| ≥0.60 y <1.00 | Parada parcial | 75% | No pierde acción ni habilita Contraataque |
| <0.60 | Defensa débil | 90% | No pierde acción ni habilita Contraataque |

La reducción se aplica antes de Armadura y otras mitigaciones.
Defender conserva una reducción mínima del 10% frente a ataques que admiten
Parada, incluso con un arma más débil. Un arma rota no permite Parada.

La pérdida afecta a una acción, no a todo el turno, y no se acumula entre varios
golpes de una misma ofensiva. Defender dura hasta la siguiente acción propia.
Contraataque es una oportunidad para una habilidad que lo utilice; no añade un
ataque gratuito automático. Esa oportunidad vence en la siguiente acción propia.

## Ejemplo de progresión

Arma defensora de daño medio 7 frente a arma enemiga de daño medio 8:

- Normal: `7 / 8 = 0.875` → Parada parcial.
- Poderoso: `7 / (8 × 1.25) = 0.70` → Parada parcial.

Si mejora el arma defensora a daño medio 10:

- Normal: `10 / 8 = 1.25` → Parada completa.
- Poderoso: `10 / (8 × 1.25) = 1` → Parada completa.

Los valores del ejemplo ilustran la fórmula; no sustituyen el catálogo de armas.

## Defender con Escudo

El escudo no compara su poder con el arma atacante. Su Bloqueo activo es 100%
fiable si tiene Durabilidad y el golpe es bloqueable. Fiabilidad no significa
absorber todo el daño: usa el porcentaje de Bloqueo activo del escudo, en lugar
de su Absorción pasiva, y consume Durabilidad con desbordamiento al personaje.
La porción del personaje pasa después por Armadura.

Si el Bloqueo activo absorbe una cantidad positiva, el atacante pierde su
siguiente acción, salvo excepciones. Un escudo roto permanece en inventario,
deja de bloquear y puede recuperarse mediante [[Reparación]].

## Excepciones y Ruptura de Guardia

- [[Ataques rápidos]] evitan Parada y Bloqueo activo, pero conservan Absorción
  pasiva del escudo y Armadura. No generan pérdida de acción ni Contraataque.
- `inbloqueable` evita escudo y defensa activa; conserva Armadura.
- `imparable` evita defensa activa; conserva defensas pasivas.
- `ignora_parada` evita Parada con arma.
- `rompe_guardia` intenta [[Ruptura de guardia]] con Impacto contra Estabilidad.
  Si tiene éxito cancela Defender antes de resolver el golpe. No elimina Armadura.

Guardia Rota y Desequilibrio siguen siendo efectos opcionales: necesitan una
definición adicional para aplicarse. Las tres capas son independientes:
Parada/Bloqueo activo, Absorción pasiva cuando corresponda, y Armadura.
