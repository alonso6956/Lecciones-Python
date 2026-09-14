# Escudo

## Identidad

- **ID interno:** `shield`
    
- **Tipo:** Equipamiento secundario defensivo
    
- **Función:** Absorber parte del daño recibido mediante una reserva independiente de Durabilidad.
    

## Principio general

Un Escudo tiene:

- Durabilidad máxima.
    
- Durabilidad actual.
    
- Absorción pasiva.
    
- Bloqueo activo.
    
- Peso.
    
- Estadísticas secundarias.
    

La Durabilidad funciona como una segunda barra defensiva.

---

# Durabilidad

Ejemplo:

`Durabilidad máxima = 60`

Estado inicial:

`Escudo = 60 / 60`

La Durabilidad se reduce al absorber daño.

Cuando:

`Durabilidad <= 0`

el Escudo queda roto.

---

# Absorción pasiva

Todos los ataques bloqueables interactúan automáticamente con el Escudo mientras tenga Durabilidad.

El escudo posee:

`Absorción pasiva = X%`

Ejemplo:

`Absorción = 10%`

Ataque:

`100 daño`

Distribución inicial:

`10 daño → Escudo`

`90 daño → personaje`

La Durabilidad pasa:

`60 → 50`

---

# Fórmula

`DañoEscudo = DañoEntrante × Absorcion`

`DañoPersonaje = DañoEntrante × (1 - Absorcion)`

Siempre que exista suficiente Durabilidad.

---

# Desbordamiento

Si la Durabilidad restante no alcanza para absorber toda su porción, el exceso vuelve al personaje.

Ejemplo:

Escudo:

`Durabilidad = 5`

Absorción:

`10%`

Ataque:

`100`

Intento de absorción:

`10`

Pero solo quedan:

`5`

Resultado:

`5 → Escudo`

`95 → personaje`

El Escudo queda:

`0 / 60`

Esto evita que un escudo con 1 punto de Durabilidad siga absorbiendo porcentajes completos.

---

# Orden con Armadura

El Escudo divide primero el daño entre:

`Escudo / Personaje`

La porción que alcanza al personaje es procesada posteriormente por:

[[Armadura]]

↓

[[Mitigación de Daño]]

Ejemplo:

Ataque:

`100`

Escudo:

`20% absorción`

Resultado inicial:

`20 → Escudo`

`80 → personaje`

Si el personaje posee:

`40% Mitigación`

entonces:

`80 × 0.60 = 48 daño a Salud`

---

# Bloqueo activo

Al utilizar [[Defender]] con Escudo, se utiliza el valor:

`Bloqueo activo`

en lugar de:

`Absorción pasiva`

Ejemplo:

Escudo:

`Absorción pasiva = 15%`

`Bloqueo activo = 70%`

Ataque normal:

`15% → Escudo`

Defender:

`70% → Escudo`

`30% → personaje`

---

# Fiabilidad

Mientras el Escudo tenga Durabilidad:

`Probabilidad de Bloqueo activo = 100%`

Por tanto se elimina el antiguo sistema de:

`X% probabilidad de bloquear`

La defensa depende ahora de:

- Durabilidad.
    
- Porcentaje de absorción.
    
- Tipo de ataque.
    
- Decisión de Defender.
    

---

# Consecuencia del Bloqueo activo

Si el personaje utiliza Defender y el escudo absorbe correctamente el golpe:

`Atacante pierde su siguiente acción`

salvo:

- Ataques inmunes.
    
- [[Ruptura de Guardia]].
    
- Habilidades especiales.
    

---

# Ejemplo completo

Escudo:

`Durabilidad = 60`

`Absorción pasiva = 10%`

`Bloqueo activo = 60%`

Ataque:

`50 daño`

## Sin Defender

Escudo:

`50 × 0.10 = 5`

Personaje:

`45`

Durabilidad:

`60 → 55`

## Defendiendo

Escudo:

`50 × 0.60 = 30`

Personaje:

`20`

Durabilidad:

`60 → 30`

Atacante:

`pierde siguiente acción`

---

# Escudo roto

Cuando:

`Durabilidad = 0`

el Escudo:

- Deja de absorber daño.
    
- No puede realizar Bloqueo activo.
    
- No proporciona efectos que requieran integridad física.
    
- Puede conservar algunos efectos pasivos si se define explícitamente.
    

Estado:

[[Escudo Roto]]

---

# Reparación

Un Escudo roto no desaparece.

Permanece en inventario con:

`Durabilidad = 0`

Puede recuperarse mediante [[Reparación de Equipo]].

---

# Perfiles de Escudo

## Escudo ligero

- Durabilidad baja
    
- Absorción pasiva baja
    
- Bloqueo activo medio
    
- Peso bajo
    
- Penalización mínima
    

## Escudo medio

- Durabilidad media
    
- Absorción media
    
- Bloqueo activo alto
    
- Peso medio
    

## Escudo pesado

- Durabilidad alta
    
- Absorción alta
    
- Bloqueo activo muy alto
    
- Peso alto
    
- Alta [[Estabilidad]]
    
- Penalización potencial a Movimiento / Evasión
    

---

# Interacciones

### Puede mejorar

- [[Estabilidad]]
    
- [[Armadura]]
    
- [[Ruptura de Guardia]] defensiva
    
- Bloqueo activo
    

### Contrarrestado por

- [[Ruptura de Guardia]]
    
- Penetración específica de Escudo
    
- Daño elevado sostenido
    
- Ataques inbloqueables
    

---

# Notas de balance

Durabilidad y absorción deben balancearse conjuntamente.

Un escudo con:

`Durabilidad muy alta + absorción muy alta`

equivale a una cantidad enorme de Salud efectiva.

El Bloqueo activo debe consumir mucha más Durabilidad que la absorción pasiva.

Eso crea una decisión:

`Defender ahora y deteriorar el Escudo`

vs.

`conservarlo para absorción pasiva durante más tiempo`