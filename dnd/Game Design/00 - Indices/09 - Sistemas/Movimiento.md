Tampoco lo haría lineal.

Usaría escalones:

\[ \boxed{ Movimiento=3+\left\lfloor\frac{DES-1}{10}\right\rfloor } \]

con límite natural, por ejemplo:

\[ Movimiento\le6 \]

Así:

|DES|Movimiento|
|---|---|
|1–10|3|
|11–20|4|
|21–30|5|
|31+|6|

Luego:

```
Armadura pesada: -1
Trait Ágil: +1
Estado Ralentizado: -1
```

Esto evita que Destreza convierta automáticamente al rogue en una unidad que cruza medio mapa.