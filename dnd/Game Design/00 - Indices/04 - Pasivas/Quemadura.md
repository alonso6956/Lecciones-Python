# Quemadura

## Identidad

- **ID interno:** `burning`
    
- **Tipo:** Estado de daño en el tiempo
    
- **Naturaleza:** Térmica / Chispa
    
- **Disipable:** Sí
    
- **Acumulable:** Sí, con límite
    
- **Duración base:** X turnos
    

## Descripción

El objetivo permanece expuesto a una fuente de calor capaz de seguir dañándolo después del impacto inicial.

Quemadura representa daño térmico persistente y puede afectar tanto a unidades como, si el sistema lo permite, a elementos del entorno.

## Aplicación

- **Probabilidad base:** Variable según habilidad, arma o fuente
    
- **Requiere impacto:** Depende de la fuente
    
- **Puede ser resistido:** Sí
    
- **Potencia asociada:** Potencia de Quemadura
    
- **Resistencia asociada:** [[Resistencia Térmica]]
    
- **Duración base:** X turnos
    

## Fórmula de aplicación

`P_quemadura = P_base × (2 × PotenciaQuemadura / (PotenciaQuemadura + ResistenciaTermica))`

Límite recomendado:

`5% ≤ P_quemadura ≤ 95%`

## Potencia de Quemadura

`PotenciaQuemadura = PotenciaFuente + BonusHabilidad + BonusPasivas + BonusChispa`

Puede provenir de:

- Habilidades de [[Chispa de Fuego]]
    
- Armas incendiarias
    
- Superficies en llamas
    
- Explosiones
    
- Estados ambientales
    

## Daño por turno

Fórmula recomendada:

`DañoQuemadura = DañoBase + floor(PotenciaQuemadura / 10)`

Ejemplo:

`DañoBase = 4`

`PotenciaQuemadura = 30`

`DañoQuemadura = 4 + 3 = 7 HP por turno`

## Escalado por acumulaciones

Cada acumulación aumenta la intensidad del estado.

Ejemplo:

`DañoTotal = DañoQuemadura × Acumulaciones`

Límite recomendado:

`Máximo de acumulaciones = 3`

Ejemplo:

- 1 stack → 7 daño
    
- 2 stacks → 14 daño
    
- 3 stacks → 21 daño
    

## Duración

Cada aplicación puede:

### Opción recomendada

Renovar duración y añadir intensidad.

`DuraciónFinal = DuraciónBase`

`Stacks = min(Stacks + 1, StacksMaximos)`

Esto evita acumular duraciones excesivamente largas.

## Interacciones

### Potenciado por

- [[Chispa de Fuego]]
    
- Superficies inflamables
    
- Aceite
    
- Estados que reduzcan [[Resistencia Térmica]]
    
- Determinadas pasivas o traits
    

### Contrarrestado por

- [[Resistencia Térmica]]
    
- Agua
    
- Habilidades de enfriamiento
    
- Armaduras resistentes al calor
    
- Determinadas Chispas
    

### Puede interactuar con

- Aceite → aumenta Potencia o duración
    
- Agua → reduce stacks o extingue
    
- [[Congelación]] → puede cancelar o ser cancelada
    
- [[Vacío]] → puede extinguirla si el lore lo permite
    

## Efectos secundarios opcionales

Con 2 o más acumulaciones:

- -X% [[Defensa]]
    
- -X [[Evasión vs Precisión]]
    
- Mayor coste de acciones físicas
    

Con 3 acumulaciones:

- Puede aplicar un estado superior como [[En llamas]]
    

No recomiendo usar todos estos efectos simultáneamente.

## Fuentes

### Habilidades

- Proyectiles incendiarios
    
- Explosiones
    
- Técnicas de [[Chispa de Fuego]]
    

### Armas

- Armas con afijos de fuego
    
- Munición incendiaria
    

### Entorno

- Suelos en llamas
    
- Aceite incendiado
    
- Objetos combustibles
    

## Evolución del estado

### Al acumularse

Aumenta el daño por turno.

### Al renovarse

Reinicia la duración base.

### Al expirar

El objetivo deja de recibir daño térmico persistente.

### Al ser disipado

Se eliminan todas o parte de las acumulaciones, dependiendo de la fuente.

## Diferencia frente a Sangrado

[[Sangrado]] representa una herida física persistente.

[[Quemadura]] representa exposición térmica persistente.

Sangrado debería interactuar principalmente con:

- [[Resistencia Física]]
    
- Curación
    
- Regeneración
    
- Heridas
    

Quemadura debería interactuar principalmente con:

- [[Resistencia Térmica]]
    
- Entorno
    
- Chispas
    
- Superficies
    
- Materiales
    

## Notas de balance

- Quemadura debería destacar por sus interacciones con el entorno.
    
- No debería ser simplemente "Sangrado pero de fuego".
    
- Su daño puede ser algo mayor que Sangrado si existen más formas de extinguirla.
    
- Los stacks deberían aumentar intensidad, no prolongar indefinidamente la duración.
    
- Debe existir contrajuego claro mediante [[Resistencia Térmica]] y efectos de extinción.