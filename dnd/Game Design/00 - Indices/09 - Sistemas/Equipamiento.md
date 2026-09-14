# Sistema de Equipamiento

## Identidad

- **ID interno:** `equipment_system`
    
- **Tipo:** Sistema de personaje
    
- **Función:** Gestionar armas, armaduras, secundarios y las interacciones derivadas de su combinación.
    

## Objetivo

El sistema de equipamiento debe permitir que distintos objetos modifiquen no solo estadísticas directas, sino también la forma en que un personaje combate.

El equipo debe afectar:

- Daño
    
- [[Poder de Ataque]]
    
- [[Evasión vs Precisión]]
    
- [[Armadura]]
    
- [[Penetración]]
    
- [[Impacto]]
    
- [[Estabilidad]]
    
- Peso
    
- Alcance
    
- Estados
    
- Sinergias de clase
    

---

# 1. Slots principales

## Arma principal

Slot ofensivo principal.

Determina:

- Daño principal.
    
- Tipo de ataque.
    
- Escalado.
    
- Precisión.
    
- Impacto.
    
- Penetración.
    
- Alcance.
    
- Estados posibles.
    

## Secundario

Puede contener:

- Segunda arma.
    
- Escudo.
    
- Herramienta.
    
- Foco.
    
- Objeto de clase.
    

El comportamiento depende del tipo de objeto equipado.

## Armadura

Ejemplo de slots:

- Cabeza
    
- Torso
    
- Brazos
    
- Piernas
    

Cada pieza contribuye a [[Armadura]], Peso y posibles estadísticas secundarias.

---

# 2. Segunda arma

Una segunda arma puede equiparse en el slot secundario si:

- El personaje cumple los requisitos.
    
- El arma es compatible con uso dual.
    
- No existe una restricción específica de clase, habilidad o tipo de arma.
    

## Penalización de daño

La segunda arma utiliza:

`DañoSecundaria = DañoNormalSecundaria × 0.50`

La penalización afecta únicamente al daño directo.

No afecta automáticamente:

- [[Penetración]]
    
- [[Evasión vs Precisión]]
    
- [[Impacto]]
    
- Probabilidad de aplicar estados
    
- Afijos
    
- Efectos especiales
    

Cada propiedad puede declarar explícitamente si se reduce en mano secundaria.

---

# 3. Ataque con dos armas

Cuando el personaje utiliza dos armas compatibles:

`AtaquePrincipal = 100% daño`

`AtaqueSecundario = 50% daño`

Daño bruto combinado:

`DañoDual = DañoPrincipal + (DañoSecundaria × 0.50)`

Cada ataque se resuelve de forma independiente cuando corresponda.

Esto implica que cada golpe puede tener su propia:

- Tirada de [[Evasión vs Precisión]]
    
- Crítico
    
- Bloqueo
    
- Penetración
    
- Aplicación de estado
    
- Afijo
    

---

# 4. Penetración con dos armas

La Penetración pertenece al golpe o al arma que lo genera.

Por defecto:

`PenetraciónPrincipal = PenetraciónArmaPrincipal`

`PenetraciónSecundaria = PenetraciónArmaSecundaria`

Si ambas armas participan en una habilidad o ataque combinado:

`PenetraciónCombinada = PenetraciónPrincipal + PenetraciónSecundaria`

Solo debe utilizarse esta suma cuando la habilidad declare explícitamente que ambas armas participan en el mismo ataque.

---

# 5. Doble daga

Las dagas están diseñadas como armas de:

- Daño individual bajo.
    
- Alta [[Evasión vs Precisión]].
    
- Baja [[Impacto]].
    
- Alta [[Penetración]].
    
- Alta capacidad de aplicar [[Sangrado]].
    
- Bajo peso.
    

Una sola daga no destaca por daño bruto.

Su fortaleza aparece al utilizar dos armas.

## Sinergia de doble daga

Al equipar dos dagas:

- La secundaria inflige 50% de su daño normal.
    
- Ambas aportan Penetración.
    
- Ambas pueden aplicar estados.
    
- Cada golpe puede resolverse por separado.
    

## Penetración

Si la habilidad utiliza ambas dagas como una secuencia:

`PenetraciónTotal = PenetraciónDaga1 + PenetraciónDaga2`

Ejemplo:

Daga principal:  
`+12 Penetración`

Daga secundaria:  
`+12 Penetración`

Ataque dual especializado:

`24 Penetración`

Esto permite que el arquetipo de dagas sea especialmente efectivo contra objetivos con Armadura media o alta sin depender de daño bruto elevado.

---

# 6. Identidad táctica de doble daga

La doble daga debe favorecer:

- Objetivos con baja Salud.
    
- Objetivos con Armadura vulnerable a Penetración.
    
- Ataques repetidos.
    
- Aplicación de [[Sangrado]].
    
- Críticos.
    
- Alta [[Evasión vs Precisión]].
    

Debe ser menos eficaz contra:

- Enemigos con mucha [[Salud]].
    
- Enemigos con alta regeneración.
    
- Enemigos inmunes o resistentes a estados.
    
- Objetivos con defensa basada en bloqueo o reducción fija de daño.
    
- Enemigos que castigan múltiples impactos.
    

---

# 7. Limitación importante de Penetración

La Penetración no debe duplicarse universalmente solo por portar dos armas.

Incorrecto:

`PenetraciónPersonaje = PenetraciónPrincipal + PenetraciónSecundaria`

para todos los ataques.

Correcto:

- Ataque con arma principal → usa Penetración principal.
    
- Ataque con secundaria → usa Penetración secundaria.
    
- Habilidad de doble arma → puede sumar ambas.
    

Esto evita que una daga secundaria convierta todos los ataques del personaje en ataques de alta penetración sin participar realmente.

---

# 8. Escudos

Si el secundario es un escudo, sustituye las ventajas ofensivas de una segunda arma por:

- Bloqueo.
    
- [[Armadura]].
    
- [[Estabilidad]].
    
- Posible [[Ruptura de Guardia]] defensiva.
    
- Reducción de daño.
    
- Acceso a habilidades específicas.
    

El jugador intercambia:

`Daño / Penetración / estados`

por:

`Bloqueo / Armadura / Estabilidad`

---

# 9. Armas de dos manos

Un arma de dos manos ocupa:

- Arma principal.
    
- Slot secundario.
    

No puede combinarse normalmente con:

- Segunda arma.
    
- Escudo.
    
- Herramienta secundaria.
    

A cambio puede ofrecer:

- Mayor daño.
    
- Mayor [[Impacto]].
    
- Mayor alcance.
    
- Mayor Penetración.
    
- Propiedades únicas.
    

---

# 10. Requisitos de equipamiento

Los objetos pueden exigir:

- [[Fuerza]]
    
- [[Destreza]]
    
- Clase
    
- Nivel
    
- Habilidad
    
- Trait
    
- Tipo de arma compatible
    

No todos los requisitos deben utilizarse simultáneamente.

---

# 11. Peso

Todo equipo posee Peso.

`PesoTotal = suma(PesoObjetosEquipados)`

Se compara contra [[Capacidad de Carga]].

El Peso puede afectar:

- Movimiento
    
- [[Evasión vs Precisión]]
    
- Iniciativa
    
- Consumo de energía
    
- [[Estabilidad]]
    

---

# 12. Compatibilidad

Cada arma debe declarar:

- `una_mano`
    
- `dos_manos`
    
- `dual_wield`
    
- `secundaria_permitida`
    
- `tipo`
    

Ejemplo:

Daga:

`una_mano = Sí`

`dual_wield = Sí`

Martillo de asedio:

`dos_manos = Sí`

`dual_wield = No`

---

# 13. Modificadores por combinación

Determinadas combinaciones pueden desbloquear reglas especiales.

Ejemplos:

## Daga + Daga

- Segundo ataque.
    
- Penetración combinada en habilidades duales.
    
- Mayor capacidad de Sangrado.
    

## Espada + Escudo

- Bloqueo.
    
- Contraataques.
    
- Mayor Estabilidad.
    

## Pistola + Daga

- Ataque híbrido.
    
- Flexibilidad de distancia.
    

## Lanza + Escudo

- Control de línea.
    
- Defensa frontal.
    

---

# 14. Resolución de un ataque dual

Secuencia recomendada:

1. Determinar si la habilidad usa una o ambas armas.
    
2. Resolver ataque principal.
    
3. Resolver Precisión vs Evasión.
    
4. Aplicar Penetración del arma principal.
    
5. Calcular Mitigación.
    
6. Aplicar daño.
    
7. Resolver estados y afijos.
    
8. Resolver ataque secundario.
    
9. Aplicar penalización de 50% de daño.
    
10. Resolver su propia Precisión.
    
11. Aplicar su propia Penetración.
    
12. Resolver estados y afijos.
    

Si la habilidad declara Penetración combinada:

`Penetración = PenetraciónPrincipal + PenetraciónSecundaria`

antes de resolver la mitigación correspondiente.

---

# 15. Filosofía de balance

La segunda arma no debe equivaler a:

`+50% daño gratis`

El coste de usar dos armas debe ser perder:

- Escudo.
    
- Armadura adicional.
    
- Bloqueo.
    
- Estabilidad.
    
- Utilidad secundaria.
    

La recompensa es:

- Más impactos.
    
- Más estados.
    
- Más oportunidades de crítico.
    
- Mayor presión ofensiva.
    
- Sinergias específicas de doble arma.
    

---

# 16. Doble daga como referencia

La doble daga representa una build de alta especialización.

Fortalezas:

- Alta Precisión.
    
- Alta Penetración.
    
- Múltiples impactos.
    
- Sangrado.
    
- Buen rendimiento contra enemigos poco resistentes.
    

Debilidades:

- Bajo daño por golpe.
    
- Bajo Impacto.
    
- Poco control físico.
    
- Sin escudo.
    
- Menor supervivencia.
    
- Dependencia de múltiples impactos.
    

## Principio de diseño

`No vence por golpear más fuerte.`

`Vence porque sus ataques encuentran huecos en la defensa y se acumulan rápidamente.`