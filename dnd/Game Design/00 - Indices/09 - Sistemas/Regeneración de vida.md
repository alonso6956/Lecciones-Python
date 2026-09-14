# Regeneración de Vida

## Identidad

- **ID interno:** `health_regeneration`
    
- **Tipo:** Estadística secundaria defensiva
    
- **Estadística principal asociada:** [[Constitución]]
    
- **Unidad:** HP por turno
    

## Fórmula

`RegenVida = 1 + floor((Constitución - 1) / 5) + Bonificaciones`

## Aplicación

`HP_nuevo = min(HP_max, HP_actual + RegenVidaFinal)`

## Modificadores

`RegenVidaFinal = RegenVida × (1 + ModificadoresPorcentuales)`

## Interacciones

### Aumentada por

- [[Constitución]]
    
- Traits
    
- Pasivas
    
- Equipo
    
- Estados positivos
    

### Reducida por

- [[Sangrado]]
    
- [[Quemadura]]
    
- Veneno
    
- Anti-curación
    

## Notas de balance

La regeneración debe escalar más lentamente que el daño recibido.

Su función es mejorar el rendimiento en combates largos, no neutralizar daño explosivo.