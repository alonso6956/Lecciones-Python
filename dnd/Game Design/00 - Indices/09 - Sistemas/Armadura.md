# Armadura

## Identidad

- **ID interno:** `armor`
    
- **Tipo:** Estadística secundaria defensiva
    
- **Fuente principal:** Equipamiento
    
- **Naturaleza:** Física
    
- **Función principal:** Reducir daño físico recibido mediante [[Mitigación de Daño]]
    

## Descripción

Representa la protección física proporcionada por armaduras, escudos y otros elementos defensivos.

Armadura no reduce directamente el daño por sí sola. Su valor es utilizado por el sistema de [[Mitigación de Daño]] para determinar qué porcentaje del daño físico es absorbido.

## Fuentes de Armadura

La Armadura puede provenir de:

- Casco
    
- Pechera
    
- Guantes
    
- Grebas
    
- Escudos
    
- Traits
    
- Pasivas
    
- Estados temporales
    
- Bonificaciones de clase
    
- Efectos de habilidades
    

## Armadura Total

`ArmaduraTotal = ArmaduraEquipo + ArmaduraPasivas + ArmaduraTraits + ArmaduraEstados`

[[Constitución]] no aumenta Armadura directamente.

## Armadura efectiva

Antes de calcular mitigación:

`ArmaduraEfectiva = max(0, ArmaduraTotal - PenetraciónArmadura)`

La Armadura efectiva nunca puede ser negativa.

## Relación con Mitigación

La Armadura efectiva se envía al sistema de [[Mitigación de Daño]].

`Mitigación = ArmaduraEfectiva / (ArmaduraEfectiva + 100)`

Con límite:

`Mitigación máxima = 60%`

## Valores de referencia

|Armadura|Mitigación aproximada|
|---|---|
|5|4.8%|
|10|9.1%|
|17|14.5%|
|25|20.0%|
|40|28.6%|
|60|37.5%|
|80|44.4%|
|100|50.0%|
|120|54.5%|
|150+|60.0%|

## Escala orientativa por Tier

### Tier 1

`5–17 Armadura`

Protección ligera o inicial.

### Tier 2

`20–40 Armadura`

Protección intermedia.

### Tier 3

`40–80 Armadura`

Protección alta.

### Tier 4

`60–120 Armadura`

Protección muy alta.

### Valores excepcionales

`120–150+ Armadura`

Construcciones defensivas especializadas.

## Relación con Penetración de Armadura

[[Penetración]] reduce Armadura antes de calcular mitigación.

Ejemplo:

`ArmaduraTotal = 100`

`Penetración = 25`

`ArmaduraEfectiva = 75`

Mitigación:

`75 / 175 ≈ 42.9%`

Sin Penetración:

`100 / 200 = 50%`

## Relación con tipos de daño

Por defecto, Armadura protege principalmente contra:

- Daño cortante
    
- Daño contundente
    
- Daño perforante
    
- Otros tipos de daño físico
    

No debería proteger automáticamente contra:

- [[Quemadura]]
    
- Daño de Chispa
    
- Daño mental
    
- Daño interno
    
- Determinados estados
    

Cada sistema debe indicar explícitamente si Armadura interviene.

## Relación con Sangrado

La Armadura puede reducir la probabilidad de que un ataque aplique [[Sangrado]] si la fuente necesita atravesar protección física.

Ejemplo opcional:

`PotenciaSangradoEfectiva = PotenciaSangrado - ProtecciónContraHeridas`

No recomiendo utilizar directamente la Armadura total para resistir Sangrado, porque para eso ya existe [[Resistencia Física]].

## Relación con Peso

Las piezas de Armadura pueden tener Peso.

Una mayor protección suele implicar:

- Mayor peso
    
- Mayor exigencia de [[Capacidad de Carga]]
    
- Posibles penalizaciones a Movimiento
    
- Posibles penalizaciones a [[Evasión]]
    
- Bonificaciones potenciales a [[Estabilidad]]
    

Esto permite que Armadura tenga un coste táctico.

## Ejemplo

Pechera pesada:

- Armadura: +35
    
- Peso: 8
    
- Estabilidad: +10
    
- Evasión: -5
    

Casco:

- Armadura: +10
    
- Peso: 2
    

Grebas:

- Armadura: +15
    
- Peso: 4
    

Total:

`Armadura = 60`

Mitigación:

`60 / 160 = 37.5%`

## Interacciones

### Aumentada por

- Equipo
    
- Traits
    
- Pasivas
    
- Habilidades defensivas
    
- Estados temporales
    

### Reducida por

- [[Penetración]]
    
- Ruptura de armadura
    
- Estados de corrosión
    
- Habilidades especializadas
    

### No aumentada directamente por

- [[Constitución]]
    
- [[Fuerza]]
    
- [[Destreza]]
    

## Diseño de equipo

La Armadura debe permitir distinguir perfiles defensivos.

### Armadura ligera

- Armadura baja
    
- Peso bajo
    
- Alta compatibilidad con Evasión y Movimiento
    

### Armadura media

- Armadura moderada
    
- Peso moderado
    
- Pocas penalizaciones
    

### Armadura pesada

- Armadura alta
    
- Peso alto
    
- Mayor Estabilidad
    
- Posibles penalizaciones a Evasión o Movimiento
    

## Notas de balance

- Armadura debe ser principalmente una propiedad del equipo.
    
- No debe escalar de forma automática con Constitución.
    
- La diferencia entre tiers debe sentirse sin alcanzar rápidamente el límite de mitigación.
    
- Una Armadura alta debe mejorar supervivencia, pero no sustituir Salud, Evasión, Bloqueo o Regeneración.
    
- Penetración debe reducir Armadura, no ignorar porcentajes finales de mitigación salvo habilidades excepcionales.
    
- El cap de 60% pertenece al sistema de [[Mitigación de Daño]], no a Armadura en sí.