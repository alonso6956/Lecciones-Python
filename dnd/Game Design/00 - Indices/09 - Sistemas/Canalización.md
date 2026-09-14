# Canalización

## Identidad

- **ID interno:** `channeling_system`
    
- **Tipo:** Sistema de combate
    

## Descripción

Una habilidad canalizada requiere mantener una acción durante uno o más turnos antes de completar o mantener su efecto.

Durante la canalización, el personaje queda expuesto a [[Interrupción]] y otros efectos de control.

## Tipos de canalización

### Preparación

La habilidad todavía no ha producido su efecto.

Ejemplo:

`Preparar ballesta pesada → Disparar`

### Canalización continua

La habilidad ya está activa pero necesita mantenerse.

Ejemplo:

`Mantener barrera`

### Carga

Cada turno dedicado aumenta la potencia final.

Ejemplo:

`Carga 1 → 120% daño`  
`Carga 2 → 160% daño`  
`Carga 3 → 220% daño`

## Propiedades de una habilidad canalizada

Cada habilidad debe definir:

- **Turnos requeridos:** X
    
- **Puede moverse durante la canalización:** Sí / No
    
- **Puede defenderse:** Sí / No
    
- **Puede esquivar:** Sí / No
    
- **Puede ser interrumpida:** Sí / No
    
- **Resistencia a Interrupción:** X
    
- **Coste inicial:** X
    
- **Coste por turno:** X
    
- **Cooldown si es interrumpida:** Completo / Parcial / Ninguno
    
- **Reembolso de recurso:** 0–100%
    

## Secuencia

`Inicio`  
↓  
`Canalizando`  
↓  
`Comprobación de interrupción`  
↓  
`Progreso +1`  
↓  
`Completa requisitos`  
↓  
`Ejecución`

## Interrupción

Una canalización puede ser cancelada por:

- [[Interrupción]]
    
- [[Derribo]]
    
- Determinados desplazamientos
    
- Incapacitación
    
- Muerte
    

## Resistencia a Interrupción

Puede utilizarse:

`Estabilidad efectiva = Estabilidad + ResistenciaCanalización`

Entonces:

`P_interrupción = P_base × (2 × Impacto / (Impacto + Estabilidad efectiva))`

## Ejemplo

### Disparo de Ballesta Pesada

- Preparación: 1 turno.
    
- Movimiento permitido: No.
    
- Puede ser interrumpido: Sí.
    
- Resistencia adicional: +10 Estabilidad.
    
- Coste: 1 munición al disparar.
    
- Si se interrumpe: no consume munición.
    

Turno 1:  
`Preparar`

Turno 2:  
`Disparo`

Si ocurre [[Interrupción]] entre ambos:

`Preparación cancelada`

## Notas de balance

La canalización permite justificar habilidades mucho más poderosas que las acciones instantáneas.

Cuanto mayor sea el riesgo de interrupción, mayor puede ser la recompensa de completar la habilidad.