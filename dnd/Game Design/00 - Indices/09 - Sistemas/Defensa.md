Actualmente tu motor ya pasa la armadura por un sistema de mitigación antes de aplicar el daño. La idea debería mantenerse, pero documentaría una fórmula explícita con rendimientos decrecientes:

\[ \boxed{ Reducción= \frac{DEF}{DEF+K} } \]

El problema es elegir \(K\).

Como ahora estás pensando en progresión potencialmente de cientos de niveles, haría que dependa del nivel:

\[ \boxed{ K=50+2L } \]

Por tanto:

\[ \boxed{ Reducción= \frac{DEF}{DEF+50+2L} } \]

Y:

\[ DañoRecibido = DañoBruto(1-Reducción) \]

### Defensa derivada

\[ \boxed{ DEF=10+2(CON-1)+Armadura } \]

Ejemplo, nivel 50:

```
CON = 25
Armadura = 40

DEF = 10 + 48 + 40
DEF = 98
```

\[ K=50+100=150 \]\[ Reducción=\frac{98}{248}=39.5\% \]

Eso ya es una defensa considerable sin convertirse en invulnerabilidad.