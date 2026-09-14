# Sangrado

## Identidad

- **ID interno:** `bleeding`
    
- **Tipo:** Estado de daño en el tiempo
    
- **Naturaleza:** Física
    
- **Disipable:** Sí
    
- **Acumulable:** Sí / según diseño
    
- **Duración base:** X turnos
    

## Descripción

El objetivo sufre una herida abierta que continúa causando daño durante varios turnos.

Sangrado representa daño físico persistente y debe diferenciarse de daño elemental o mágico.

## Aplicación

- **Probabilidad base:** Variable según arma o habilidad
    
- **Requiere impacto:** Sí
    
- **Puede ser resistido:** Sí
    
- **Potencia asociada:** Potencia de Sangrado
    
- **Resistencia asociada:** [[Resistencia Física]]
    
- **Duración base:** X turnos
    

## Fórmula de aplicación

`P_sangrado = P_base × (2 × PotenciaSangrado / (PotenciaSangrado + ResistenciaFisica))`

Límite recomendado:

`5% ≤ P_sangrado ≤ 95%`

## Potencia de Sangrado

Puede provenir de:

`PotenciaSangrado = PotenciaArma + BonusHabilidad + BonusPasivas`

No recomiendo que escale directamente con Fuerza o Destreza salvo que una habilidad específica lo indique.

## Daño por turno

Fórmula inicial recomendada:

`DañoSangrado = DañoBaseSangrado + floor(PotenciaSangrado / 10)`

Alternativa porcentual:

`DañoSangrado = max(DañoMinimo, SaludMaximaObjetivo × PorcentajeSangrado)`

No recomiendo usar únicamente porcentaje de vida máxima porque puede volver el estado demasiado dominante contra enemigos grandes.

## Fórmula híbrida recomendada

`DañoSangrado = DañoPlano + (SaludMaximaObjetivo × 0.01)`

Ejemplo:

`DañoPlano = 3`

Objetivo con 200 HP:

`3 + 2 = 5 HP por turno`

## Duración

`Duración = DuraciónBase`

Opcionalmente:

`DuraciónFinal = max(1, DuraciónBase - ReduccionPorResistencia)`

## Acumulaciones

Si Sangrado puede acumularse:

- Cada nueva aplicación añade 1 acumulación.
    
- Cada acumulación aumenta el daño.
    
- La duración puede renovarse o mantenerse independiente.
    

Ejemplo:

`DañoTotal = DañoPorStack × Stacks`

Límite recomendado:

`Stacks máximos = 3–5`

## Renovación

Si no quieres múltiples stacks:

Nueva aplicación:

`Duración = max(DuraciónActual, DuraciónNueva)`

o:

`Duración = DuraciónBase`

Evitaría sumar duración indefinidamente.

## Interacciones

### Potenciado por

- Armas cortantes
    
- Perforaciones
    
- Habilidades específicas
    
- [[Desequilibrio]] si quieres representar vulnerabilidad física
    
- Traits o pasivas especializadas
    

### Contrarrestado por

- [[Resistencia Física]]
    
- Armaduras especializadas
    
- Habilidades de curación
    
- Estados de coagulación
    
- Consumibles médicos
    

### Puede reducir

- [[Regeneración de Vida]]
    

Por ejemplo:

`RegeneraciónFinal = Regeneración × 0.5`

mientras Sangrado esté activo.

## Efectos secundarios opcionales

Con varias acumulaciones:

- Reducción de [[Regeneración de Vida]]
    
- Penalización a Movimiento
    
- Penalización a Fuerza
    
- Mayor vulnerabilidad a nuevos Sangrados
    

No recomiendo activar todos a la vez.

## Fuentes

### Armas

- Espadas
    
- Dagas
    
- Lanzas
    
- Armas con afijos de Sangrado
    

### Habilidades

- Cortes profundos
    
- Ataques perforantes
    
- Técnicas de ejecución
    

### Pasivas

- Pasivas de doble ataque
    
- Especializaciones en heridas
    

## Evolución del estado

### Al acumularse

Aumenta el daño por turno.

### Al renovarse

Reinicia o extiende duración según la fuente.

### Al expirar

La herida deja de causar daño.

### Al ser disipado

El Sangrado termina inmediatamente.

## Notas de balance

- Sangrado debe castigar combates prolongados.
    
- No debería ignorar todas las defensas sin una razón explícita.
    
- Debe existir una resistencia clara.
    
- Su daño debe crecer de forma controlada contra enemigos con mucha vida.
    
- Puede funcionar como contrapeso natural a personajes con alta [[Regeneración de Vida]].