# Reparación de Equipo

## Identidad

- **ID interno:** `equipment_repair`
    
- **Tipo:** Subsistema de [[Sistema de Crafteo]]
    
- **Función:** Restaurar objetos cuya Durabilidad ha sido reducida o agotada.
    

## Principio general

Los objetos con Durabilidad no son destruidos permanentemente al alcanzar:

`Durabilidad = 0`

Pasan al estado:

[[Objeto Roto]]

y deben ser reparados antes de volver a utilizarse normalmente.

---

# Objetos reparables

Inicialmente:

- [[Escudo]]
    
- Armas con Durabilidad
    
- Armaduras con Durabilidad
    

El sistema puede limitarse inicialmente a Escudos si todavía no existe desgaste general del equipo.

---

# Estado del objeto

## Funcional

`Durabilidad > 0`

## Roto

`Durabilidad = 0`

Un objeto roto:

- Permanece en inventario.
    
- No proporciona su función principal.
    
- Puede ser reparado.
    
- Conserva Tier, Calidad, material y afijos.
    

---

# Reparación básica

La reparación restaura:

`DurabilidadActual → DurabilidadMaxima`

o una cantidad parcial.

## Reparación completa

`DurabilidadRecuperada = DurabilidadMaxima - DurabilidadActual`

## Reparación parcial

`DurabilidadNueva = min(DurabilidadMaxima, DurabilidadActual + Reparacion)`

---

# Coste de reparación

El coste depende de:

- Tier.
    
- Durabilidad perdida.
    
- Material.
    
- Tipo de objeto.
    
- Calidad.
    

Fórmula conceptual:

`Coste = CosteBaseTier × PorcentajeDurabilidadPerdida × ModificadorMaterial`

Donde:

`PorcentajeDurabilidadPerdida = 1 - (DurabilidadActual / DurabilidadMaxima)`

---

# Ejemplo

Escudo:

`60 Durabilidad máxima`

Estado:

`0 / 60`

Tier:

`2`

Coste base Tier 2:

`100`

Como perdió:

`100% de Durabilidad`

Coste:

`100 × 1.00 = 100`

Si estuviera:

`30 / 60`

perdió:

`50%`

Coste:

`100 × 0.50 = 50`

---

# Materiales de reparación

La reparación puede requerir materiales relacionados con el objeto.

Ejemplos:

Escudo de acero:

- Metal.
    
- Componentes.
    

Escudo de madera:

- Madera.
    
- Herrajes.
    

Equipo avanzado:

- Material correspondiente al Tier.
    

No es necesario utilizar exactamente los materiales originales del crafteo.

---

# Tier y reparación

Objetos de Tier superior:

- Requieren más recursos.
    
- Pueden requerir materiales más raros.
    
- Tienen mayor coste de reparación.
    

El Tier no cambia durante una reparación.

---

# Calidad y reparación

La Calidad no se pierde mediante reparación normal.

Un objeto:

`Maestro Tier 3`

continúa siendo:

`Maestro Tier 3`

después de repararlo.

---

# Afijos

Los afijos no desaparecen al romperse el objeto.

Reparar restaura Durabilidad, no vuelve a generar el objeto.

---

# Reparación y Durabilidad máxima

Por defecto:

`Reparar NO reduce DurabilidadMaxima`

No recomiendo inicialmente un sistema donde cada reparación degrade permanentemente el objeto.

Añade mantenimiento, pero también puede generar frustración y pérdida inevitable de equipo valioso.

Puede incorporarse posteriormente como una mecánica específica.

---

# Reparación en combate

Por defecto:

`No permitida`

La reparación requiere:

- Fuera del combate.
    
- Estación apropiada.
    
- Sistema de crafteo.
    

Las habilidades especiales pueden realizar reparaciones temporales en combate.

---

# Reparación de emergencia

Opcional:

Una habilidad o consumible puede recuperar:

`X Durabilidad`

sin reparar completamente el objeto.

Ejemplo:

`Kit de reparación`

`+20 Durabilidad`

No puede superar:

`DurabilidadMaxima`

---

# Integración con Escudos

Cuando un [[Escudo]] llega a:

`0 Durabilidad`

deja de absorber daño.

Después de repararlo:

`Durabilidad = DurabilidadMaxima`

y vuelve a funcionar normalmente.

---

# Filosofía de diseño

La Durabilidad debe funcionar como un recurso consumible del objeto, no como una cuenta regresiva hacia su desaparición permanente.

La reparación proporciona:

- Consumo de materiales.
    
- Valor al crafteo.
    
- Decisiones económicas.
    
- Gestión entre expediciones.
    

sin destruir permanentemente objetos importantes.