# Build de producción de Dungeon

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

    %LOCALAPPDATA%\Dungeon\save_slot_1.json
    %LOCALAPPDATA%\Dungeon\save_slot_1.backup.json
    %LOCALAPPDATA%\Dungeon\save_slot_2.json
    %LOCALAPPDATA%\Dungeon\save_slot_2.backup.json
    %LOCALAPPDATA%\Dungeon\save_slot_3.json
    %LOCALAPPDATA%\Dungeon\save_slot_3.backup.json
    %LOCALAPPDATA%\Dungeon\dungeon.log

Cada partida guarda el estado completo del personaje y del combate. Después de
guardar o cargar manualmente un slot, el progreso se actualiza automáticamente
en ese slot activo.

## Desarrollo

    $env:DUNGEON_ENV = "development"
    python main.py

Para generar un ejecutable de desarrollo con consola y debug habilitado:

    .\build-developer.ps1

El compilador de desarrollo tampoco instala dependencias. Ambos compiladores
reutilizan `.build-venv`, creado exclusivamente por `setup-build-env.ps1`.

El entorno se selecciona con DUNGEON_ENV=development o production.
