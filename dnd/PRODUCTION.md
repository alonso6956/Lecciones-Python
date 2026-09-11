# Build de producción de Dungeon

El vertical slice de preparación y combate automático se abre desde
**Desafío táctico · Party de 3** en el menú web. Ver
[TACTICAL_PROTOTYPE.md](TACTICAL_PROTOTYPE.md) para ejecución, escenario de
derrota/reajuste/victoria, pruebas y simulaciones de balance.

## Generar el ejecutable

Requisito exclusivo del equipo de desarrollo: Python 3.8 a 3.15 en Windows.
El tester final no necesita Python ni instalar dependencias.

Preparar las dependencias una sola vez:

    Set-ExecutionPolicy -Scope Process Bypass
    .\setup-build-env.ps1

Generar el ZIP para testers después de cada cambio que quieras distribuir:

    .\build-tester.ps1

Este segundo comando no instala ni actualiza Python o dependencias.

El script crea:

    dist\Dungeon.exe
    release\Dungeon-Windows-x64.zip

## Instalar y ejecutar

1. Copiar Dungeon-Windows-x64.zip al equipo de pruebas.
2. Extraerlo en cualquier carpeta con permisos de escritura.
3. Ejecutar Dungeon.exe.
4. El juego abre automáticamente http://127.0.0.1:8765.

No requiere instalador, Python ni conexión a Internet.

Los datos se almacenan en:

    %LOCALAPPDATA%\Dungeon\roster.json
    %LOCALAPPDATA%\Dungeon\roster.backup.json
    %LOCALAPPDATA%\Dungeon\dungeon.log

El roster compartido guarda personajes al crearlos, al **avanzar de habitación**, al **comprar en el menú** y al **morir**,
con checksum y reemplazo atómico. Conserva ID, nombre, nivel, EXP, oro,
estadísticas base, puntos, clase, chispa, inventario y equipo. No guarda vida,
habitación, enemigos, turnos ni efectos temporales.

Morir guarda la experiencia, el oro y el resto de la progresión permanente antes
de volver al menú, incluso si aún no se superó una habitación. Elegir el personaje
recupera ese progreso y empieza en la habitación 1 con vida completa.
Confirmar el abandono vuelve al menú sin guardar y descarta los cambios desde
el último checkpoint (creación, habitación superada, compra en el menú o muerte).
El guardado manual está desactivado también en la API.

En **Elegir personaje**, **Descartar personaje** elimina del roster el personaje
seleccionado y su progreso, previa confirmación. La eliminación se guarda de
inmediato. Solo está disponible desde el menú y fuera de un combate táctico.
Si quedan menos de tres personajes, el modo táctico vuelve a bloquearse.

Si aún no existe `roster.json`, se importan los tres slots antiguos disponibles
sin modificarlos. Sus habilidades de arma se retiran y sus niveles invertidos
se devuelven como puntos de habilidad. Los slots dañados se informan en el menú;
sus archivos originales permanecen disponibles para recuperación.

La creación solo pide nombre y equipa `espada_basica`. El nivel máximo es 30:
al 10 se elige una etiqueta de clase (Guerrero, Pícaro o Guardián); al 30 se
asigna `chispa_latente`. Los árboles y modificadores futuros tienen ganchos
`TODO` en `progression.py` y `character.py`. Las armas no conceden habilidades
ni pasivas.

Cada nivel ganado suma 5 de vida máxima, además del bono de Constitución,
y aumenta la vida actual en esa misma cantidad. El nivel 1 conserva los 50
puntos base. La energía máxima empieza en 3 y aumenta a 4, 5 y 6 al alcanzar
los niveles 10, 20 y 30. Ambos máximos se recalculan al cargar el personaje.

El táctico requiere **tres personajes en el roster**, sin umbral adicional de
nivel. Usa sus últimos checkpoints y únicamente sus armas compradas. Sus
combates y cambios de preparación no modifican la progresión del calabozo.
En desarrollo los mismos archivos se guardan dentro de `.local`.

## Desarrollo

    $env:DUNGEON_ENV = "development"
    python main.py

Para generar un ejecutable de desarrollo con consola y debug habilitado:

    .\build-developer.ps1

El compilador de desarrollo tampoco instala dependencias. Ambos compiladores
reutilizan `.build-venv`, creado exclusivamente por `setup-build-env.ps1`.

El entorno se selecciona con DUNGEON_ENV=development o production.
