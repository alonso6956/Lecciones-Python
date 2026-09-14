# Mitigación de Daño

## Identidad

- **ID interno:** `damage_mitigation`
    
- **Tipo:** Sistema de combate
    
- **Función:** Convertir Armadura en reducción de daño físico
    

## Descripción

La Mitigación de Daño determina qué porcentaje del daño físico recibido es absorbido por la [[Armadura]] efectiva del objetivo.

La Armadura tiene rendimientos decrecientes y un límite máximo de mitigación.

## Armadura

La Armadura proviene principalmente de:

- Equipamiento
    
- Escudos
    
- Pasivas
    
- Traits
    
- Estados
    
- Bonificaciones de clase
    

[[Constitución]] no aumenta Armadura directamente.

## Armadura efectiva

Antes de calcular mitigación:

`ArmaduraEfectiva = max(0, ArmaduraTotal - Penetración)`

## Fórmula de mitigación

`Mitigación = ArmaduraEfectiva / (ArmaduraEfectiva + 100)`

## Límite máximo

`MitigaciónMaxima = 60%`

Por tanto:

`MitigaciónFinal = min(0.60, Mitigación)`

## Daño final

`DañoFinal = DañoFisico × (1 - MitigaciónFinal)`

Redondeo recomendado:

`DañoFinal = max(1, round(DañoFinal))`

## Valores de referencia

|Armadura|Mitigación|
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
|150|60.0%|
|200|60.0%|

## Escala orientativa por Tier

### Tier 1

Aproximadamente:

`5–17 Armadura`

Mitigación aproximada:

`5–15%`

### Tier 2

Aproximadamente:

`20–40 Armadura`

Mitigación aproximada:

`17–29%`

### Tier 3

Aproximadamente:

`40–80 Armadura`

Mitigación aproximada:

`29–44%`

### Tier 4

Aproximadamente:

`60–120 Armadura`

Mitigación aproximada:

`38–55%`

### Valores excepcionales

`150+ Armadura`

Mitigación máxima:

`60%`

## Penetración de Armadura

La Penetración reduce puntos de Armadura antes de calcular mitigación.

Ejemplo:

`Armadura = 120`

`Penetración = 30`

`ArmaduraEfectiva = 90`

Mitigación:

`90 / 190 ≈ 47.4%`

Sin Penetración:

`120 / 220 ≈ 54.5%`

## Orden de resolución recomendado

1. Calcular [[Poder de Ataque]] y daño bruto.
    
2. Aplicar modificadores ofensivos.
    
3. Resolver [[Precisión]] vs [[Evasión]].
    
4. Resolver bloqueo si corresponde.
    
5. Calcular Penetración.
    
6. Calcular Armadura efectiva.
    
7. Calcular Mitigación.
    
8. Aplicar reducciones adicionales de daño.
    
9. Aplicar daño final a [[Salud]].
    

## Relación con Bloqueo

Bloqueo debe ser un sistema separado.

Ejemplo:

`DañoTrasBloqueo = DañoBruto × (1 - Bloqueo%)`

Luego:

`DañoFinal = DañoTrasBloqueo × (1 - MitigaciónArmadura)`

El orden debe mantenerse consistente en todo el juego.

## Relación con reducción de daño

Los efectos como:

`-20% daño recibido`

deben aplicarse después de Armadura.

Ejemplo:

`DañoBruto = 100`

`MitigaciónArmadura = 40%`

`DañoTrasArmadura = 60`

Pasiva:

`-20% daño recibido`

`DañoFinal = 60 × 0.80 = 48`

## Hard cap

La Armadura no puede superar:

`60% de mitigación`

pero otras fuentes defensivas pueden seguir actuando después.

Esto permite que:

- Bloqueo
    
- Traits
    
- Pasivas
    
- Estados
    
- Regeneración
    

sigan siendo relevantes.

## Notas de balance

- Armadura alta debe ser valiosa sin volver obligatoria la Penetración.
    
- El Tier 1 no debe consumir una parte excesiva de la curva defensiva.
    
- El intervalo 60–120 de Armadura debe representar defensas medias y altas.
    
- El cap de 60% evita escalados extremos de vida efectiva.
    
- Penetración debe ser una propiedad especializada, no una estadística obligatoria para todos los atacantes.