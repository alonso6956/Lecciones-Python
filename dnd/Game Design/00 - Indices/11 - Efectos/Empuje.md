# Empuje

## Identidad

- **ID interno:** `push`
    
- **Tipo:** Control / Desplazamiento
    
- **Naturaleza:** Física
    
- **Disipable:** No
    
- **Acumulable:** No
    
- **Máximo de acumulaciones:** 1
    
- **Duración base:** Instantánea
    

## Descripción

El objetivo es desplazado involuntariamente desde su posición actual debido a un impacto, explosión, onda de choque o fuerza externa.

Empuje modifica directamente la posición de una unidad y puede utilizarse para romper formaciones, alejar enemigos, exponer objetivos o provocar colisiones con elementos del escenario.

## Efecto mecánico

- **Efecto principal:** Desplaza al objetivo una cantidad determinada de casillas.
    
- **Efectos secundarios:** Puede provocar colisiones, romper formaciones o activar interacciones con el terreno.
    
- **Restricciones:** El desplazamiento se detiene si el objetivo encuentra una casilla bloqueada.
    
- **Penalizaciones:** Por sí mismo no hace perder acciones, salvo que otra interacción lo provoque.
    

## Aplicación

- **Probabilidad base:** Variable según habilidad.
    
- **Requiere impacto:** Sí.
    
- **Puede ser resistido:** Sí.
    
- **Resistencia asociada:** [[Estabilidad]]
    
- **Distancia base:** Variable según habilidad.
    
- **Condiciones especiales:** La masa, tamaño, postura y terreno pueden modificar la distancia final de desplazamiento.
    

## Fórmula base

Una opción inicial:

`Distancia final = Distancia base × (100 / (100 + Estabilidad))`

El resultado puede redondearse según las reglas del sistema.

Ejemplo:

Una habilidad genera un Empuje de 3 casillas.

El objetivo posee 50 de [[Estabilidad]]:

`3 × (100 / 150) = 2`

El objetivo es desplazado **2 casillas**.

## Interacciones

### Contrarrestado por

- [[Estabilidad]]
    
- [[Inamovible]]
    
- Posturas defensivas
    
- Elementos del terreno que impidan el desplazamiento
    

### Potenciado por

- Golpes pesados
    
- Explosiones
    
- Ondas de choque
    
- Diferencia de masa favorable al atacante
    
- Objetivos afectados por [[Desequilibrio]]
    

### Puede provocar

- [[Derribo]]
    
- [[Desequilibrio]]
    
- Colisiones
    
- Caídas
    
- Daño ambiental
    

### Puede interrumpir

- Habilidades canalizadas
    
- Preparaciones de ataque
    
- Formaciones defensivas
    

## Colisiones

Si el objetivo es empujado contra una unidad, pared u obstáculo, puede producirse una interacción adicional.

Ejemplos:

- **Contra pared:** daño adicional o [[Derribo]].
    
- **Contra otra unidad:** ambas pueden sufrir [[Desequilibrio]].
    
- **Contra precipicio:** caída si el terreno lo permite.
    
- **Contra objeto destructible:** puede romperlo o atravesarlo.
    

## Fuentes

### Habilidades

- [[Impacto Sísmico]]
    
- Golpes de escudo
    
- Cargas
    
- Ondas expansivas
    

### Armas

- [[Martillo de asedio]]
    
- Mazas pesadas
    
- Escudos grandes
    

### Pasivas

-   
    

### Chispas

- Algunas manifestaciones de fuerza, aire o presión podrían generar Empuje.
    

## Evolución del estado

- **Al acumularse:** No aplica.
    
- **Al renovarse:** Cada nuevo Empuje se resuelve de forma independiente.
    
- **Al expirar:** El efecto termina inmediatamente después del desplazamiento.
    
- **Al ser disipado:** No puede disiparse porque es un efecto instantáneo.
    

## Notas de balance

- Empuje debe ser principalmente una herramienta de posicionamiento, no una fuente de daño directa.
    
- El daño debería aparecer mediante interacciones como colisiones, precipicios o habilidades específicas.
    
- [[Estabilidad]] debería reducir la distancia desplazada sin convertir fácilmente al objetivo en completamente inmune.
    
- Las unidades muy grandes pueden tener resistencia adicional a Empuje.
    
- Empuje puede ser una de las mecánicas principales de [[Rompemuros]], permitiéndole controlar físicamente el campo de batalla.