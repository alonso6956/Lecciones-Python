# Fuerza

## Identidad

- **ID interno:** `strength`
    
- **Tipo:** Estadística primaria
    
- **Abreviatura:** `FUE`
    
- **Valor mínimo recomendado:** 1
    
- **Naturaleza:** Física
    
- **Función principal:** Potencia ofensiva y control físico
    

## Descripción

Representa la capacidad del personaje para ejercer fuerza física sobre enemigos, armas, objetos y el entorno.

Fuerza no debe limitarse únicamente a aumentar el daño. También determina la capacidad de imponer movimiento, romper defensas y utilizar equipo pesado de manera eficiente.

## Sistemas derivados

Fuerza alimenta principalmente:

- [[Poder de ataque]]
    
- [[Impacto]]
    
- [[Penetración]]
    
- [[Capacidad de Carga]]
    

## Daño Físico

### Multiplicador de Fuerza

`M_FUE = 1 + 0.10 × √(FUE - 1)`

### Daño bruto

`DañoBruto = (DañoBase + DañoArma) × [1 + EscaladoArma × (M_FUE - 1)]`

Donde `EscaladoArma` determina cuánto aprovecha cada arma la Fuerza.

### Ejemplos de escalado

- Daga: `0.40`
    
- Espada: `0.75`
    
- Lanza: `0.80`
    
- Maza: `1.00`
    
- Martillo de asedio: `1.20`
    

## Impacto

Representa la capacidad del personaje para imponer fuerza física sobre otro cuerpo.

`Impacto = 10 + 2 × (FUE - 1) + ImpactoArma + Bonificaciones`

[[Impacto]] interviene en:

- [[Empuje]]
    
- [[Derribo]]
    
- [[Interrupción]]
    
- [[Ruptura de Guardia]]
    
- [[Desequilibrio]]
    

Se enfrenta principalmente a [[Estabilidad]].

## Penetración

Representa la capacidad de superar protección física mediante potencia, diseño del arma o fuerza aplicada.

`Penetración = 5 × √(FUE - 1) + PenetraciónArma + Bonificaciones`

La Penetración reduce la Defensa efectiva antes de calcular mitigación:

`DEF_efectiva = max(0, DEF - Penetración)`

## Capacidad de Carga

Determina cuánto peso puede llevar el personaje sin recibir penalizaciones.

`CargaMax = 8 + 2 × (FUE - 1) + Bonificaciones`

Puede modificarse mediante:

- Traits
    
- Pasivas
    
- Equipo
    
- Estados
    
- Clase
    

## Carga relativa

`CargaRelativa = PesoEquipado / CargaMax`

Ejemplo de categorías:

- 0–50% → Ligera
    
- 51–75% → Normal
    
- 76–100% → Pesada
    
-   
    
    > 100% → Sobrecargado
    

## Interacciones

### Potencia

- [[Poder de ataque]]
    
- [[Impacto]]
    
- [[Penetración]]
    
- [[Capacidad de Carga]]
    

### Favorece

- Armas pesadas
    
- Control físico
    
- Ruptura de defensas
    
- Uso de armadura pesada
    
- Builds basadas en contacto directo
    

### Contrarrestada indirectamente por

- [[Defensa]]
    
- [[Estabilidad]]
    
- [[Evasión vs Precisión]]
    
- Distancia
    
- Control de movimiento
    

## Relación con armas

No todas las armas deben beneficiarse por igual de Fuerza.

Ejemplo:

`DañoFinal = DañoBase × Escalado de Fuerza`

Esto permite que:

- Un martillo aproveche enormemente FUE.
    
- Una daga aproveche poco FUE.
    
- Un arma híbrida combine Fuerza con [[Destreza]].
    

## Relación con control físico

Fuerza no aplica directamente [[Derribo]] o [[Empuje]].

Primero genera [[Impacto]].

Luego el sistema compara:

`Impacto ↔ Estabilidad`

De esta manera, Fuerza participa en control físico sin convertir cada punto de FUE en una probabilidad directa de control.

## Relación con equipo pesado

Una Fuerza alta permite utilizar:

- Martillos
    
- Mazas
    
- Escudos grandes
    
- Armaduras pesadas
    

con menos penalizaciones derivadas del peso.

Esto permite que FUE mejore indirectamente movilidad y supervivencia sin otorgar Evasión ni Defensa directamente.

## Fuentes de modificación

### Aumentada por

- Nivel
    
- Puntos de estadística
    
- Traits
    
- Pasivas
    
- Equipo
    
- Estados temporales
    
- Chispas específicas
    

### Reducida por

- Debilitamiento
    
- Fatiga
    
- Heridas
    
- Estados físicos
    
- Penalizaciones narrativas
    

## Ejemplo

Personaje:

`FUE = 25`

Martillo de asedio:

`EscaladoFuerza = 1.20`  
`ImpactoArma = 25`  
`PenetraciónArma = 10`

### Multiplicador de Fuerza

`M_FUE = 1 + 0.10 × √24`

`M_FUE ≈ 1.49`

### Impacto

`Impacto = 10 + 2 × 24 + 25`

`Impacto = 83`

### Penetración

`Penetración = 5 × √24 + 10`

`Penetración ≈ 34`

El personaje no solamente golpea más fuerte: también es mucho más eficaz desplazando, derribando y rompiendo guardias.

## Notas de balance

- Fuerza no debe reducirse a “+daño”.
    
- Su valor debe sentirse especialmente en armas pesadas y efectos físicos.
    
- No debe aumentar Defensa, Salud o Estabilidad directamente.
    
- El escalado de daño debe tener rendimientos decrecientes.
    
- Impacto y Penetración permiten que Fuerza siga siendo relevante incluso cuando el daño bruto no sea la prioridad.
    
- La Capacidad de Carga crea una ventaja indirecta importante para personajes que utilicen equipo pesado.