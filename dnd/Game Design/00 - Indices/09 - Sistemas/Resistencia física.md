# Resistencia Física

## Identidad

- **ID interno:** `physical_resistance`
    
- **Tipo:** Estadística secundaria defensiva
    
- **Estadística principal asociada:** [[Constitución]]
    
- **Naturaleza:** Física / Fisiológica
    

## Descripción

Representa la capacidad del organismo para resistir efectos físicos persistentes sin depender de la protección externa de la armadura.

No reduce directamente el daño de ataques físicos.

## Fórmula

`ResistenciaFisica = 2 × (Constitución - 1) + Bonificaciones`

## Función

Se utiliza para resistir la aplicación o intensidad de estados físicos.

Ejemplos:

- [[Sangrado]]
    
- Heridas
    
- Fatiga
    
- Venenos físicos
    
- Debilitamientos corporales
    

## Fórmula general

`P_estado = P_base × (2 × PotenciaEstado / (PotenciaEstado + ResistenciaFisica))`

Límite recomendado:

`5% ≤ P_estado ≤ 95%`

## Ejemplo

`P_base = 40%`

`PotenciaSangrado = 50`

`ResistenciaFisica = 50`

`P_final = 40%`

Si:

`ResistenciaFisica = 100`

entonces:

`P_final ≈ 26.7%`

## Interacciones

### Aumentada por

- [[Constitución]]
    
- Traits
    
- Pasivas
    
- Equipo especializado
    
- Estados positivos
    

### Reducida por

- Heridas
    
- Fatiga
    
- Enfermedades
    
- Debilitamientos
    

## No afecta

- [[Armadura]]
    
- Mitigación directa de daño
    
- [[Estabilidad]]
    
- [[Evasión]]
    

## Notas de balance

Debe proteger frente a estados físicos persistentes, no frente al daño inicial que los produce.