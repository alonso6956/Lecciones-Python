Usaría rendimiento decreciente:

\[ \boxed{ M_{FUE}=1+0.10\sqrt{FUE-1} } \]

Y:

\[ \boxed{ DañoBruto=(DañoBase+DañoArma)\times M_{FUE} } \]

Ejemplos:

|FUE|Multiplicador|
|---|---|
|1|×1.00|
|5|×1.20|
|10|×1.30|
|25|×1.49|
|50|×1.70|
|100|×1.99|
|200|×2.41|

Esto permite subir Fuerza durante cientos de niveles sin que el daño se vuelva absurdo.

Y además las armas pueden tener un **coeficiente de escalado**:

\[ Daño=(Base+Arma)\times[1+C_{arma}(M_{FUE}-1)] \]