# Sistema de Crafteo - Balance de Armaduras y Armas

## Identidad

- **ID interno:** `crafting_equipment_balance`
    
- **Tipo:** Sistema de crafteo / balance de equipo
    
- **Función:** Definir límites de estadísticas para armas y armaduras según Tier, calidad, tipo de objeto y perfil estadístico.
    

## Objetivo

El sistema de crafteo debe generar objetos dentro de límites matemáticos previsibles.

El poder de un objeto depende de:

`Tier + Tipo de objeto + Calidad + Material + Afijos`

El Tier define el presupuesto principal del objeto.

La Calidad determina dónde cae el objeto dentro de los límites de su Tier.

El tipo de objeto determina cómo se distribuye ese presupuesto.

Los requisitos de estadísticas determinan qué tipo de personaje puede utilizar correctamente el objeto.

---

# 1. Tier

El Tier representa el nivel general de poder del objeto.

Controla:

- Armadura máxima.
    
- Daño base.
    
- Estadísticas secundarias.
    
- Potencia de afijos.
    
- Cantidad de afijos.
    
- Requisitos de estadísticas.
    
- Complejidad mecánica del objeto.
    

El Tier no depende de la Calidad.

Un objeto Maestro Tier 1 sigue siendo Tier 1.

---

# 2. Calidad

La Calidad determina qué tan cerca está el objeto del máximo permitido por su Tier.

|Calidad|Factor|
|---|---|
|Defectuosa|0.10|
|Común|0.30|
|Buena|0.55|
|Excelente|0.80|
|Maestra|1.00|

## Fórmula general

`ValorObjeto = MinTier + ((MaxTier - MinTier) × FactorCalidad)`

La Calidad nunca permite superar el máximo natural del Tier.

---

# ARMADURAS

# 3. Presupuesto total de Armadura por Tier

Los valores representan la [[Armadura]] total aproximada de un conjunto completo.

|Tier|Mínimo|Máximo|
|---|---|---|
|Tier 1|5|17|
|Tier 2|18|40|
|Tier 3|41|80|
|Tier 4|81|120|

Estos valores se relacionan con [[Mitigación de Daño]]:

`Mitigación = Armadura / (Armadura + 100)`

Con:

`Mitigación máxima = 60%`

Valores de referencia:

- 17 Armadura → 14.5%
    
- 40 Armadura → 28.6%
    
- 60 Armadura → 37.5%
    
- 80 Armadura → 44.4%
    
- 100 Armadura → 50%
    
- 120 Armadura → 54.5%
    

---

# 4. Distribución por piezas

Cada slot posee un Coeficiente de Protección.

Ejemplo:

|Pieza|Coeficiente|
|---|---|
|Pechera|0.40|
|Piernas|0.25|
|Casco|0.20|
|Brazos / Guantes|0.15|

Total:

`1.00`

## Fórmula

`ArmaduraPieza = ArmaduraPresupuesto × CoeficienteSlot`

Ejemplo:

Conjunto de 100 Armadura:

- Pechera → 40
    
- Piernas → 25
    
- Casco → 20
    
- Guantes → 15
    

---

# 5. Calidad de una pieza de Armadura

Ejemplo:

Pechera Tier 2.

Tier 2:

`18–40 Armadura`

Coeficiente de pechera:

`0.40`

Rango de la pieza:

`7.2–16`

Pechera Buena:

`7.2 + ((16 - 7.2) × 0.55)`

`≈ 12 Armadura`

---

# 6. Tipo de Armadura

El tipo modifica la distribución del presupuesto.

## Ligera

- Armadura baja.
    
- Peso bajo.
    
- Sin penalización significativa de [[Evasión vs Precisión]].
    
- Mayor libertad de Movimiento.
    

Multiplicador orientativo:

`Armadura × 0.75`

## Media

- Armadura estándar.
    
- Peso medio.
    
- Sin especialización extrema.
    

Multiplicador:

`Armadura × 1.00`

## Pesada

- Armadura alta.
    
- Peso alto.
    
- Puede aumentar [[Estabilidad]].
    
- Puede reducir [[Evasión vs Precisión]] o Movimiento.
    

Multiplicador orientativo:

`Armadura × 1.15`

El resultado continúa sujeto al máximo permitido por el Tier.

---

# 7. Materiales de Armadura

Los materiales modifican el perfil del objeto.

Ejemplos:

## Acero pesado

- +Armadura
    
- +Peso
    
- +Estabilidad
    

## Cuero tratado

- -Armadura
    
- -Peso
    
- Menor penalización a Evasión
    

Los materiales no deberían permitir saltar de forma rutinaria el límite de Tier.

---

# ARMAS

# 8. Presupuesto de daño por Tier

El Tier determina el daño base de referencia de las armas.

|Tier|Daño base de referencia|
|---|---|
|Tier 1|5–10|
|Tier 2|11–20|
|Tier 3|21–35|
|Tier 4|36–55|

Estos valores representan daño del arma antes de aplicar:

- [[Poder de Ataque]]
    
- Escalado del arma
    
- Críticos
    
- Habilidades
    
- Afijos
    
- [[Penetración]]
    
- [[Mitigación de Daño]]
    

---

# 9. Daño según Calidad

`DañoArma = MinTier + ((MaxTier - MinTier) × FactorCalidad)`

Ejemplo:

Espada Tier 2 Buena:

`11 + ((20 - 11) × 0.55)`

`≈ 16 daño`

---

# 10. Multiplicador por familia de arma

El daño de referencia corresponde a un arma equilibrada.

|Tipo|Multiplicador|
|---|---|
|Daga|0.70|
|Espada|1.00|
|Lanza|0.95|
|Maza|1.10|
|Martillo pesado|1.30|
|Ballesta ligera|1.05|
|Ballesta pesada|1.40|

Ejemplo:

Daño base de referencia:

`30`

Martillo:

`30 × 1.30 = 39`

Daga:

`30 × 0.70 = 21`

---

# 11. Presupuesto completo del arma

El poder de un arma no depende únicamente de su daño.

Cada arma distribuye su presupuesto entre:

- Daño
    
- [[Evasión vs Precisión]]
    
- [[Impacto]]
    
- [[Penetración]]
    
- Peso
    
- Alcance
    
- Velocidad de uso
    
- Aplicación de estados
    
- Canalización
    
- Preparación
    
- Número de impactos
    
- Compatibilidad con uso dual
    

Una mejora importante en una categoría debe compensarse con una debilidad en otra.

---

# 12. Perfiles base de armas

## Daga

- Daño: Bajo
    
- Precisión: Alta
    
- Impacto: Bajo
    
- Penetración: Alta
    
- Peso: Muy bajo
    
- Sangrado: Alto
    
- Uso dual: Sí
    

## Espada

- Daño: Medio
    
- Precisión: Media
    
- Impacto: Medio
    
- Penetración: Media
    
- Peso: Medio
    
- Versatilidad: Alta
    

## Lanza

- Daño: Medio
    
- Precisión: Media
    
- Impacto: Medio
    
- Penetración: Media
    
- Alcance: Alto
    
- Control de zona: Alto
    

## Maza

- Daño: Alto
    
- Precisión: Media-baja
    
- Impacto: Alto
    
- Penetración: Alta
    
- Peso: Alto
    

## Martillo pesado

- Daño: Muy alto
    
- Precisión: Baja
    
- Impacto: Muy alto
    
- Penetración: Muy alta
    
- Peso: Muy alto
    
- Uso: Dos manos
    

## Ballesta ligera

- Daño: Medio-alto
    
- Precisión: Alta
    
- Impacto: Bajo
    
- Penetración: Media
    
- Preparación: Baja
    

## Ballesta pesada

- Daño: Muy alto
    
- Precisión: Alta
    
- Impacto: Medio
    
- Penetración: Alta
    
- Preparación: Alta
    
- Vulnerable a [[Interrupción]]
    

---

# ESCALADO

# 13. Poder de Ataque

[[Fuerza]] afecta a [[Poder de Ataque]].

Cada arma posee un Coeficiente de Escalado con Poder de Ataque.

## Fórmula

`DañoFinalArma = DañoBaseArma + (PoderAtaque × EscaladoArma)`

---

# 14. Grados de escalado

|Grado|Coeficiente|
|---|---|
|E|0.20|
|D|0.35|
|C|0.50|
|B|0.70|
|A|0.90|
|S|1.10|

Ejemplo:

`PoderAtaque = 30`

Martillo con escalado A:

`30 × 0.90 = 27`

Daga con escalado D:

`30 × 0.35 = 10.5`

---

# 15. Perfil estadístico del arma

Las armas deben estar orientadas a perfiles estadísticos, no a clases específicas.

Ejemplo:

## Martillo de asedio

Perfil:

- Fuerza alta
    
- Poder de Ataque alto
    
- Impacto alto
    
- Baja Precisión
    

Sinergia común:

- [[Rompemuros]]
    

## Daga

Perfil:

- Destreza alta
    
- Alta Precisión
    
- Alta Penetración
    
- Bajo daño individual
    

Sinergia común:

- [[Sombra]]
    

## Lanza

Perfil:

- Fuerza media
    
- Destreza media
    
- Alcance
    
- Control de zona
    

Sinergia común:

- [[Guerrero Olvidado]]
    

La clase no es un requisito directo.

---

# REQUISITOS DE ESTADÍSTICAS

# 16. Principio general

Cada arma puede exigir valores mínimos de estadísticas primarias.

Los requisitos dependen de:

- Peso.
    
- Tamaño.
    
- Complejidad de manejo.
    
- Necesidad de precisión.
    
- Fuerza necesaria para controlarla.
    
- Uso a una o dos manos.
    
- Uso dual.
    

Los requisitos no dependen directamente de la clase.

---

# 17. Fuerza como requisito

Fuerza se utiliza cuando el arma implica:

- Gran peso.
    
- Alto Impacto.
    
- Uso a dos manos.
    
- Golpes contundentes.
    
- Control de retroceso.
    
- Manejo de armas pesadas.
    

---

# 18. Destreza como requisito

Destreza se utiliza cuando el arma implica:

- Alta Precisión.
    
- Coordinación fina.
    
- Ataques rápidos.
    
- Uso dual.
    
- Apuntar a distancia.
    
- Manejo de armas ligeras.
    

---

# 19. Constitución como requisito

[[Constitución]] no se utiliza normalmente como requisito de arma.

Constitución representa resistencia fisiológica, no capacidad de manejo.

Solo debe utilizarse como excepción muy específica.

---

# 20. Valores base por Tier

|Tier|Base de requisito|
|---|---|
|Tier 1|2|
|Tier 2|5|
|Tier 3|9|
|Tier 4|14|

Este valor funciona como referencia.

---

# 21. Modificadores de requisito por perfil

## Peso

- Ligero → `-1 FUE`
    
- Normal → `0`
    
- Pesado → `+2 FUE`
    
- Muy pesado → `+4 FUE`
    

## Impacto

- Bajo → `0 FUE`
    
- Medio → `+1 FUE`
    
- Alto → `+2 FUE`
    
- Muy alto → `+3 FUE`
    

## Precisión

- Baja → `0 DES`
    
- Media → `+1 DES`
    
- Alta → `+2 DES`
    
- Muy alta → `+3 DES`
    

## Uso dual

- Compatible → `+1 DES`
    

## Dos manos

- Requerida → `+2 FUE`
    

---

# 22. Fórmulas orientativas

## Fuerza requerida

`FUE_Requerida = BaseTier + ModPeso + ModImpacto + ModDosManos`

## Destreza requerida

`DES_Requerida = BaseTier + ModPrecision + ModUsoDual + ModComplejidad`

Estas fórmulas sirven como guía.

El resultado final puede ajustarse manualmente por balance.

---

# 23. Requisitos orientativos por familia

|Arma|Tier 1|Tier 2|Tier 3|Tier 4|
|---|---|---|---|---|
|Daga|DES 2|DES 5|DES 9|DES 14|
|Espada|FUE 2|FUE 5|FUE 9|FUE 14|
|Lanza|FUE 2 / DES 2|FUE 5 / DES 4|FUE 9 / DES 7|FUE 14 / DES 10|
|Maza|FUE 3|FUE 6|FUE 10|FUE 15|
|Martillo pesado|FUE 4|FUE 8|FUE 13|FUE 19|
|Ballesta ligera|DES 2|DES 5|DES 8|DES 12|
|Ballesta pesada|FUE 3 / DES 2|FUE 6 / DES 4|FUE 10 / DES 7|FUE 15 / DES 10|

Estos valores deben revisarse cuando se conozcan los rangos definitivos de Fuerza y Destreza.

---

# 24. Armas del mismo Tier con requisitos distintos

Dos armas del mismo Tier pueden tener requisitos diferentes.

## Espada ligera Tier 3

- Peso: Bajo
    
- Precisión: Alta
    
- Impacto: Medio
    

Requisitos orientativos:

`FUE 7`

`DES 6`

## Espada pesada Tier 3

- Peso: Alto
    
- Precisión: Baja
    
- Impacto: Alto
    

Requisitos:

`FUE 11`

`DES 3`

---

# 25. Ejemplo: Martillo de asedio Tier 3

Base:

`9`

Perfil:

- Muy pesado
    
- Impacto muy alto
    
- Dos manos
    
- Precisión baja
    

El cálculo teórico puede producir un requisito alto.

Requisito de balance recomendado:

`FUE 13–16`

No necesita Destreza relevante salvo que una variante concreta lo indique.

---

# 26. Ejemplo: Daga Tier 3

Perfil:

- Ligera
    
- Alta Precisión
    
- Uso dual
    
- Bajo Impacto
    

Requisito recomendado:

`DES 9–11`

Fuerza mínima o inexistente.

---

# 27. Ejemplo: Ballesta pesada Tier 3

Perfil:

- Peso alto
    
- Alta Precisión
    
- Preparación
    
- Daño alto
    

Requisito recomendado:

`FUE 10`

`DES 7`

Fuerza permite manejar y estabilizar el arma.

Destreza permite apuntar correctamente.

---

# 28. Requisito y escalado no son lo mismo

Ejemplo:

Martillo:

`Requisito = FUE 13`

`Escalado Poder de Ataque = A`

Daga:

`Requisito = DES 9`

`Escalado Poder de Ataque = D`

El requisito determina:

`¿Puede utilizar correctamente el arma?`

El escalado determina:

`¿Cuánto se beneficia el arma de las estadísticas del personaje?`

---

# 29. Uso dual

Para utilizar dos armas:

- Deben ser compatibles con uso dual.
    
- El personaje debe cumplir los requisitos de ambas.
    

Los requisitos no se suman.

Ejemplo:

Daga principal:

`DES 9`

Daga secundaria:

`DES 9`

Requisito final:

`DES 9`

No:

`DES 18`

Una habilidad específica de Uso Dual puede exigir requisitos adicionales.

---

# 30. Arma secundaria

Una segunda arma equipada en el slot secundario utiliza las reglas de [[Sistema de Equipamiento]].

Por defecto:

`DañoSecundaria = DañoNormal × 0.50`

La penalización afecta al daño directo.

No reduce automáticamente:

- Penetración
    
- Precisión
    
- Impacto
    
- Afijos
    
- Aplicación de estados
    

Estas propiedades deben definirse individualmente.

---

# 31. Doble daga

La doble daga utiliza el bajo daño individual como contrapartida a:

- Alta Precisión.
    
- Alta Penetración.
    
- Múltiples golpes.
    
- Aplicación de Sangrado.
    
- Bajo Peso.
    

En ataques duales específicos puede utilizarse:

`PenetraciónCombinada = PenetraciónDagaPrincipal + PenetraciónDagaSecundaria`

Esto solo ocurre cuando ambas armas participan realmente en el ataque.

---

# AFIJOS

# 32. Tipos de afijos

## Ofensivos

- +Poder de Ataque
    
- +Impacto
    
- +Penetración
    
- +Precisión
    
- +Potencia de Sangrado
    
- +Potencia de Quemadura
    

## Defensivos

- +Armadura
    
- +Estabilidad
    
- +Resistencia Física
    
- +Regeneración de Vida
    
- +Resistencia Térmica
    

## Utilidad

- Reducción de Peso
    
- Aumento de Alcance
    
- Reducción de preparación
    
- Bonificaciones de Movimiento
    
- Bonificaciones de energía
    

---

# 33. Cantidad máxima de afijos

|Tier|Afijos máximos|
|---|---|
|Tier 1|1|
|Tier 2|2|
|Tier 3|3|
|Tier 4|4|

La Calidad puede afectar la potencia de los afijos.

---

# 34. Límites de afijos

Los afijos no deben permitir que un objeto ignore completamente su identidad.

Ejemplo:

Una daga no debería convertirse mediante afijos en:

- El arma con mayor daño.
    
- El arma con mayor Impacto.
    
- El arma con mayor alcance.
    

Los afijos mejoran un perfil; no deberían reemplazarlo.

---

# MATERIALES

# 35. Función de los materiales

El material modifica propiedades concretas.

Puede afectar:

- Daño
    
- Armadura
    
- Peso
    
- Impacto
    
- Penetración
    
- Resistencias
    
- Durabilidad
    
- Afinidad con Chispas
    

El material no debería cambiar por completo el rol del objeto.

---

# 36. Ejemplo de material ofensivo

## Acero pesado

Arma:

- +Impacto
    
- +Peso
    
- +Penetración
    
- -Precisión
    

Armadura:

- +Armadura
    
- +Estabilidad
    
- +Peso
    

---

# 37. Ejemplo de material ligero

## Aleación ligera

Arma:

- -Peso
    
- +Precisión
    
- -Impacto
    

Armadura:

- -Peso
    
- Menor Armadura
    
- Menor penalización a Evasión
    

---

# VALIDACIÓN DEL OBJETO

# 38. Orden de generación

1. Determinar Tier.
    
2. Determinar tipo de objeto.
    
3. Determinar familia de arma o armadura.
    
4. Determinar rango estadístico del Tier.
    
5. Determinar Calidad.
    
6. Calcular valor base.
    
7. Aplicar perfil del objeto.
    
8. Aplicar material.
    
9. Calcular requisitos de estadísticas.
    
10. Determinar escalado.
    
11. Generar afijos.
    
12. Validar límites.
    
13. Crear objeto final.
    

---

# 39. Validación de Armadura

Debe comprobarse:

`ArmaduraTotal ≤ LimiteTier`

salvo excepciones explícitas del sistema.

---

# 40. Validación de daño

Debe comprobarse:

`DañoBase ≤ MaxTier × MultiplicadorTipo`

Los afijos y propiedades especiales se evalúan aparte.

---

# 41. Validación de requisitos

Debe comprobarse que los requisitos:

- Sean coherentes con el Tier.
    
- Sean coherentes con el peso.
    
- Sean coherentes con Impacto.
    
- Sean coherentes con Precisión.
    
- No favorezcan artificialmente una clase concreta.
    

---

# 42. Validación de escalado

El escalado debe corresponder al perfil.

Ejemplos:

Martillo pesado:

- Poder de Ataque: A / S
    

Espada:

- Poder de Ataque: B
    

Daga:

- Poder de Ataque: D / C
    

Ballesta pesada:

- Poder de Ataque: E / D
    

---

# 43. Validación de identidad

Todo objeto debe tener:

1. Una ventaja.
    
2. Una desventaja.
    
3. Una función táctica.
    
4. Una estadística o sistema que aprovecha.
    
5. Una estadística o sistema que sacrifica.
    

Ejemplos:

`Martillo = Daño + Impacto + Penetración - Precisión - Peso`

`Daga = Precisión + Penetración + Sangrado - Daño - Impacto`

`Lanza = Alcance + control - rendimiento a corta distancia`

`Ballesta pesada = Daño + Precisión - preparación - movilidad`

---

# 44. Filosofía general

El Tier define cuánto poder puede tener un objeto.

La Calidad define qué tan bueno es dentro de ese Tier.

El Material altera su perfil.

Los Afijos especializan el objeto.

Los Requisitos determinan quién puede utilizarlo correctamente.

El Escalado determina cuánto se beneficia de las estadísticas del personaje.

La Clase no modifica directamente las estadísticas del objeto.

La sinergia aparece porque las habilidades, pasivas y estadísticas de una clase aprovechan mejor determinados perfiles de arma.