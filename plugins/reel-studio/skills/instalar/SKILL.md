---
name: instalar
description: Instala y verifica lo que Reel Studio necesita en la computadora (motor de video, ffmpeg, Whisper para transcribir y generador de PDFs). Usar la primera vez que se usa Reel Studio, cuando el usuario diga "instala Reel Studio", "configura el editor", o cuando `reel doctor` reporte requisitos faltantes.
---

# Instalar Reel Studio

Funciona en **macOS** y en **Linux (Ubuntu/Debian)**. El comando `doctor` detecta el sistema y muestra la instrucción correcta para cada requisito; sigue exactamente lo que imprime.

1. Ejecuta `node "${CLAUDE_PLUGIN_ROOT}/scripts/reel.cjs" doctor` y lee qué falta. Cada línea con ✗ trae el comando exacto para ese sistema.
2. Resuelve cada requisito faltante, explicándole al usuario en simple qué vas a instalar:
   - **macOS**: `brew install ffmpeg node python` · herramientas: `xcode-select --install`. Si no hay Homebrew, guíalo desde https://brew.sh.
   - **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install -y ffmpeg nodejs npm python3 python3-venv build-essential`.
   - **Node.js 18+** (cualquier sistema): si la versión del repo es vieja, instalar la LTS desde https://nodejs.org.
   - **Linux — librerías de Chrome** (para que Remotion renderice): el `doctor` imprime la línea `sudo apt-get install -y libnss3 ...`. Es necesaria en servidores/escritorios Linux limpios.
3. Ejecuta `node "${CLAUDE_PLUGIN_ROOT}/scripts/reel.cjs" instalar`. La primera vez compila Whisper y descarga el modelo de transcripción (~1,5 GB): tarda varios minutos, avísale.
4. Repite `doctor` hasta ver "Todo listo".

Notas:
- Los comandos con `sudo` (Linux) los ejecuta **el usuario** en su Terminal; nunca escribas su contraseña por él.
- Todo queda en `~/ReelStudio`. Para usar otra carpeta, definir `REEL_STUDIO_HOME`.
- Al actualizar el plugin, vuelve a ejecutar `instalar` (actualiza el motor si cambió la versión).
