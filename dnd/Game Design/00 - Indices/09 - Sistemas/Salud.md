# Salud

## Identidad

- **ID interno:** `health`
    
- **Tipo:** Sistema de personaje / Recurso defensivo
    
- **Naturaleza:** Universal
    
- **Valor mínimo:** 0
    
- **Fuente principal:** Nivel del personaje
    
- **Función:** Representar la cantidad de daño que una unidad puede recibir antes de quedar fuera de combate.
    

## Descripción

La Salud representa la capacidad total de una unidad para continuar combatiendo antes de ser derrotada.

No debe confundirse con:

- [[Constitución]]
    
- [[Armadura]]
    
- [[Mitigación de Daño]]
    
- [[Regeneración de Vida]]
    
- [[Resistencia Física]]
    

La Salud determina cuánto daño puede absorber una unidad en términos absolutos.

Los demás sistemas determinan cuánto daño recibe, qué tan fácilmente puede recuperarlo o qué efectos adicionales puede resistir.

---

# 1. Salud Máxima

La Salud máxima escala principalmente con el nivel del personaje.

Fórmula base:

`SaludMaxima = SaludBase + SaludPorNivel × (Nivel - 1)`

Valores iniciales:

`SaludBase = 50`

`SaludPorNivel = 5`

Por tanto:

`SaludMaxima = 50 + 5 × (Nivel - 1)`

## Ejemplos

|Nivel|Salud máxima|
|---|---|
|1|50|
|10|95|
|20|145|
|30|195|
|50|295|
|100|545|

---

# 2. Constitución

[[Constitución]] NO aumenta directamente la Salud máxima.

Constitución afecta principalmente:

- [[Estabilidad]]
    
- [[Resistencia Física]]
    
- [[Regeneración de Vida]]
    

Esto evita que Constitución concentre demasiados beneficios defensivos.

---

# 3. Modificadores de Salud Máxima

Después de calcular la Salud base por nivel, pueden aplicarse bonificaciones planas y porcentuales.

## Fórmula

`SaludFinal = (SaludBaseNivel + BonificacionesPlanas) × (1 + BonificacionesPorcentuales)`

Ejemplo:

Personaje nivel 20:

`SaludBaseNivel = 145`

Equipo:

`+20 Salud`

Trait:

`+10% Salud máxima`

Resultado:

`(145 + 20) × 1.10 = 181.5`

`SaludFinal = 182`

---

# 4. Fuentes de Salud adicional

La Salud máxima puede aumentar mediante:

- Traits
    
- Pasivas
    
- Equipo
    
- Evoluciones de clase
    
- Estados temporales
    
- Efectos narrativos
    
- Afijos
    

No debería aumentar directamente mediante:

- [[Fuerza]]
    
- [[Destreza]]
    
- [[Constitución]]
    

salvo efectos excepcionales.

---

# 5. Salud actual

La unidad mantiene dos valores:

`HP_actual`

`HP_maximo`

Condición:

`0 ≤ HP_actual ≤ HP_maximo`

Al recibir daño:

`HP_actual = max(0, HP_actual - DañoFinal)`

Al recibir curación:

`HP_actual = min(HP_maximo, HP_actual + Curación)`

---

# 6. Relación con Mitigación

La Salud se modifica únicamente después de resolver los sistemas defensivos.

Orden recomendado:

1. Resolver [[Precisión]] vs [[Evasión]].
    
2. Determinar daño bruto.
    
3. Aplicar [[Penetración de Armadura]].
    
4. Resolver [[Armadura]].
    
5. Resolver [[Mitigación de Daño]].
    
6. Aplicar bloqueos o reducciones adicionales según el orden definido.
    
7. Obtener Daño Final.
    
8. Restar Daño Final de Salud.
    

Por tanto:

`HP_nuevo = HP_actual - DañoFinal`

---

# 7. Relación con Armadura

[[Armadura]] y Salud cumplen funciones distintas.

## Armadura

Reduce el daño recibido.

## Salud

Permite soportar daño que no pudo ser mitigado.

Dos personajes pueden tener perfiles distintos:

### Perfil A

- Salud alta
    
- Armadura baja
    

Puede absorber golpes, pero recibe gran parte del daño bruto.

### Perfil B

- Salud media
    
- Armadura alta
    

Recibe menos daño por ataque, pero dispone de menor margen absoluto.

Ambos perfiles deben ser viables.

---

# 8. Relación con Regeneración

[[Regeneración de Vida]] recupera Salud perdida.

`HP_nuevo = min(HP_maximo, HP_actual + RegenVida)`

La Regeneración no aumenta Salud máxima.

Su valor aumenta principalmente mediante [[Constitución]].

---

# 9. Relación con estados de daño

Estados como:

- [[Sangrado]]
    
- [[Quemadura]]
    
- Veneno
    

reducen directamente la Salud cuando realizan su tick de daño.

Ejemplo:

`HP_actual -= DañoSangrado`

El estado debe definir si su daño:

- Es mitigado por Armadura.
    
- Ignora Armadura.
    
- Puede reducirse mediante resistencias específicas.
    

---

# 10. Umbrales de Salud

La Salud puede utilizar umbrales para activar mecánicas.

Valores recomendados:

## Salud alta

`HP > 75%`

## Salud media

`40% < HP ≤ 75%`

## Salud baja

`20% < HP ≤ 40%`

## Estado crítico

`HP ≤ 20%`

Estos umbrales pueden ser utilizados por:

- Traits
    
- Pasivas
    
- IA
    
- Habilidades
    
- Hitos
    

---

# 11. Estado crítico

Una unidad entra en estado crítico cuando:

`HP_actual / HP_maximo ≤ 0.20`

El estado crítico no necesita aplicar penalizaciones universales.

Debe funcionar principalmente como condición para otros sistemas.

Ejemplos:

- [[Guardián]] se activa cerca de aliados críticos.
    
- Una IA puede priorizar retirada.
    
- Una habilidad de ejecución puede obtener bonificación.
    
- Un Hito puede registrar haber sobrevivido con Salud crítica.
    

---

# 12. Derrota

Por defecto:

`HP_actual ≤ 0 → unidad derrotada`

En combate táctico, el resultado exacto puede depender del sistema.

Posibles resultados:

- Inconsciente.
    
- Incapacitado.
    
- Muerto.
    
- Retirado del combate.
    

La Salud únicamente determina que la unidad ya no puede continuar normalmente.

El sistema narrativo decide las consecuencias posteriores.

---

# 13. Vida efectiva

Para balancear personajes no debe observarse únicamente la Salud nominal.

Puede utilizarse la métrica:

`VidaEfectiva = SaludMaxima / (1 - Mitigación)`

Ejemplo:

Personaje A:

`Salud = 200`

`Mitigación = 0%`

`Vida efectiva = 200`

Personaje B:

`Salud = 200`

`Mitigación = 50%`

`Vida efectiva = 400`

Esto permite comparar builds defensivas.

---

# 14. Límite defensivo

La [[Mitigación de Daño]] por Armadura tiene un límite de:

`60%`

Por tanto, solo mediante Armadura:

`VidaEfectivaMaxima = Salud / 0.40`

`VidaEfectivaMaxima = Salud × 2.5`

Otros sistemas como:

- Bloqueo
    
- Evasión
    
- Regeneración
    
- Pasivas
    
- Estados
    

pueden aumentar la supervivencia real, pero deben evaluarse por separado.

---

# 15. Salud y Tier

La Salud no depende directamente del Tier de equipo.

Un personaje no gana Salud automáticamente por utilizar equipo de Tier superior.

El Tier puede proporcionar objetos con:

- Afijos de Salud.
    
- Traits especiales.
    
- Bonificaciones porcentuales.
    

pero estos efectos consumen parte del presupuesto del objeto.

---

# 16. Salud en enemigos

Los enemigos pueden utilizar la misma estructura:

`SaludMaxima = SaludBaseTipo + EscaladoNivel + ModificadorEnemigo`

Ejemplo conceptual:

`SaludEnemigo = SaludBase × MultiplicadorRango`

Posibles rangos:

- Normal
    
- Veterano
    
- Élite
    
- Jefe
    

El aumento de Salud debe utilizarse con cuidado para evitar enemigos que solo se conviertan en "esponjas de daño".

---

# 17. Salud y clases

La clase no necesita modificar directamente la fórmula base de Salud.

En cambio, puede especializarse mediante pasivas.

Ejemplo:

[[Rompemuros]]

`+10% Salud máxima`

o:

`+X Salud mediante pasiva`

mientras otra clase puede especializarse en:

- Evasión
    
- Regeneración
    
- Bloqueo
    
- Control
    

Esto mantiene una fórmula universal de Salud.

---

# 18. Salud y Traits

Los Traits pueden modificar Salud de forma excepcional.

Ejemplos:

## Robusto

`+10% Salud máxima`

## Frágil

`-10% Salud máxima`

## Superviviente

No aumenta Salud máxima, pero puede otorgar beneficios cuando:

`HP ≤ 25%`

Los Traits no deberían convertir Salud en una estadística que el jugador pueda maximizar fácilmente sin coste.

---

# 19. Curación

La curación utiliza:

`CuracionReal = min(CuracionGenerada, HP_maximo - HP_actual)`

La curación excedente se pierde salvo que exista un sistema específico de sobrecuración.

Ejemplo:

`HP = 80 / 100`

`Curación = 30`

Solo recupera:

`20 HP`

---

# 20. Sobrecuración

Por defecto:

`HP_actual ≤ HP_maximo`

No existe sobrecuración.

Si una habilidad permite sobrecuración debe declararlo explícitamente.

Ejemplo:

`Escudo temporal = CuracionExcedente`

Esto no aumenta permanentemente Salud máxima.

---

# 21. Regeneración fuera de combate

Si es necesario reducir tiempos muertos:

`RegenFueraCombate = RegenCombate × Multiplicador`

Ejemplo:

`Multiplicador = 3`

Otra opción es recuperar un porcentaje de Salud al terminar encuentros.

Este sistema debe permanecer separado de la fórmula de Salud máxima.

---

# 22. Filosofía de diseño

La Salud debe cumplir una sola función principal:

`Determinar cuánto daño puede recibir una unidad antes de caer.`

No debe convertirse en una extensión de Constitución.

La supervivencia debe resultar de la combinación:

`Salud`

`+ Armadura`

`+ Mitigación`

`+ Evasión`

`+ Regeneración`

`+ Resistencia`

`+ habilidades`

Esto permite múltiples modelos defensivos sin convertir una única estadística en obligatoria.

---

# 23. Fórmulas resumidas

## Salud por nivel

`HP_BaseNivel = 50 + 5 × (Nivel - 1)`

## Salud máxima

`HP_Max = (HP_BaseNivel + BonusPlano) × (1 + BonusPorcentual)`

## Daño recibido

`HP_Nuevo = max(0, HP_Actual - DañoFinal)`

## Curación

`HP_Nuevo = min(HP_Max, HP_Actual + Curacion)`

## Regeneración

`HP_Nuevo = min(HP_Max, HP_Actual + RegenVida)`

## Porcentaje de Salud

`HP_Porcentaje = HP_Actual / HP_Max`

## Vida efectiva frente a daño mitigable

`EHP = HP_Max / (1 - Mitigacion)`