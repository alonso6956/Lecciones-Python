No le daría a Fuerza penetración directamente punto por punto porque sería demasiado.

Haría:

\[ \boxed{ Penetración= 5\sqrt{FUE-1}+PenetraciónArma } \]

La penetración reduciría **Defensa**, no el porcentaje final.

\[ \boxed{ DEF_{efectiva}=\max(0,DEF-Penetración) } \]

Ejemplo:

```
Defensa enemigo = 100
Penetración = 25

Defensa efectiva = 75
```

Esto también encaja con tu arquitectura actual, porque el motor ya contempla penetración de armadura antes de calcular la mitigación.