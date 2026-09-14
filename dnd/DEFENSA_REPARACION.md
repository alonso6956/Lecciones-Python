# Revisión de defensa y reparación

Implementación del 14 de septiembre de 2026, comparada con Sistema de Parada,
Escudo, Reparación, Ataques rápidos y Ruptura de guardia de Game Design.

| Regla anterior | Comportamiento implementado |
| --- | --- |
| Defender duplicaba armadura | Parada con arma principal o bloqueo activo con escudo; armadura pasiva independiente |
| Escudo con probabilidad de bloqueo | Absorción automática, limitada por durabilidad actual |
| Durabilidad como propiedad fija del catálogo | Máxima en catálogo y actual por instancia, conservada en guardados y transferencias |
| Sin mantenimiento en taller | Reparación completa por oro y materiales del inventario/vault, fuera de combate |
| Ataque rápido solo adelantaba su acción | Además evita parada, bloqueo activo y generación de contraataque; respeta absorción pasiva y armadura |

## Decisiones para reglas abiertas

- Parada (revisión de balance inicial): daño medio del arma principal defensora,
  sin escalado por Fuerza, dividido por la presión del arma atacante. Presión:
  daño medio ×1 normal, ×1.25 poderoso. Ratio ≥1: completa (-50% daño y pierde
  siguiente acción); ≥.60: parcial (-25%); menor: débil (-10%). No se suman
  armas secundarias, críticos, habilidades ni estados. Rápidos omiten la parada.
- El escudo de hierro conserva sus 100 puntos máximos existentes y utiliza 10%
  de absorción pasiva y 60% de bloqueo activo. Los ejemplos numéricos del diseño
  no se interpretan como una orden de sustituir todas las durabilidades por 60.
- Crafteo: absorción y bloqueo crecen con el poder del perfil/material/tier,
  con límites de 30% y 90%. Conserva la calidad elegida. Los objetos anteriores
  reciben los valores defensivos predeterminados sin regenerar su equipo.
- Bloqueo activo sustituye a absorción pasiva: nunca se aplican ambos al mismo
  golpe. Absorbe como máximo la durabilidad restante y después la armadura
  mitiga lo que alcanza al personaje. Si absorbe una cantidad positiva, pierde
  una acción el atacante, incluso si ese golpe termina de romper el escudo.
- La pérdida afecta a la siguiente acción, no a todo el turno, y no se acumula
  con varios golpes de una misma ofensiva. Una parada parcial o débil no la genera.
- Contraataque: la habilidad existente conserva su daño básico; su bono requiere
  una defensa activa exitosa previa y un escudo todavía funcional. La oportunidad
  vence en la siguiente acción propia. No se añade un ataque gratuito automático.
- Ruptura usa Impacto contra Estabilidad, con probabilidad base predeterminada
  50% y los límites compartidos de 5–95%. Cancela Defender si tiene éxito; no
  introduce los estados opcionales Guardia Rota o Desequilibrio. Las habilidades
  pueden declarar `rompe_guardia`, `probabilidad_ruptura`, `inbloqueable`,
  `imparable`, `ignora_parada` y `rapido`. No se asignan estos efectos a habilidades
  cuyo diseño no los declara.
- Escudo roto: permanece equipado/inventariado y con peso; deja de absorber,
  bloquear o aportar armadura y bonificaciones. No se convierte automáticamente
  en parada con arma mientras siga equipado.
- Desgaste automático inicial solo en escudos, permitido por Reparación.md.
  El taller admite también armas y armaduras dañadas; no se inventa una tasa
  de desgaste por ataque o por golpe para estas piezas. Equipo roto pierde su
  función; reparar restaura sus propiedades originales.
- Reparación completa: `ceil(50 × tier × fracción perdida × material × calidad × tipo)`
  de oro y `ceil(tier × fracción perdida)` unidades del material del objeto.
  Equipo antiguo sin material usa hierro. Material: hierro/bronce 1, acero 1.25,
  plata 1.5, obsidiana 2. Calidad: defectuosa .8, común/antigua 1, buena 1.1,
  excelente 1.35, maestra 1.5. Tipo: armadura 1.25, arma/escudo 1.
  No pierde calidad, afijos, tier ni durabilidad máxima. No se añaden kits opcionales.

## Compatibilidad y comprobación

Los guardados sin durabilidades se cargan con equipo íntegro. Cada copia mantiene
su propio desgaste, también al depositar, retirar, fabricar otros objetos o guardar
el personaje. El taller trabaja sobre copias y solo publica tras guardar; un error
de recursos o disco no deja cobros ni reparaciones parciales.

Dungeon y el simulador táctico comparten el cálculo. El simulador mantiene su
comportamiento previo de trabajar con copias del roster; no publica progreso de
sus simulaciones. Su escudo especial de jefe sigue siendo una mecánica distinta
del objeto equipable. La reparación se accede desde los detalles del objeto en el
taller web. Web y Godot muestran la durabilidad del escudo en combate.

Se conserva la mitigación vigente de Armadura.md/Mitigación de daño.md
(`armadura / (armadura + 100)`, máximo 60%). Defensa.md contiene una propuesta
anterior de otra fórmula; no sustituye las reglas explícitas actuales.

Pruebas: `python -B -m unittest discover`, validación sintáctica de los seis
scripts web modificados, importación y arranque headless de Godot. Incluyen
absorción antes de armadura, desbordamiento, rápidos, parada, ruptura resistida,
acciones perdidas, combos/habilidades, equipo roto, guardados antiguos,
transferencias y reparación con rechazo durante combate y ante errores.

Los coeficientes nuevos de escudos y reparación son valores iniciales de balance;
las pruebas verifican reglas y regresiones, no garantizan equilibrio económico
o dificultad definitiva de las expediciones.
