---
name: marca
description: Configura el kit de marca de un negocio en Reel Studio (logo, colores, tipografía, llamado a la acción, música y glosario de nombres). Usar cuando el usuario diga "configura mi marca", "agrega un cliente nuevo", "cambia los colores/logo/música", o antes de editar el primer video de un negocio que no tiene marca.
---

# Kit de marca

Cada negocio tiene una carpeta `~/ReelStudio/marcas/<slug>/` con `brand.json` y sus archivos. Se configura una vez y todos los videos la usan.

Comando: `node "${CLAUDE_PLUGIN_ROOT}/scripts/reel.cjs" marca <slug>` (slug en minúsculas sin espacios, ej. `memostore`).

## Preguntas (máximo 5, en lenguaje simple)
1. **Nombre** exacto de la marca y cómo se escribe (mayúsculas, símbolos).
2. **Logo**: pide el archivo (PNG transparente o SVG ideal). Si no tiene, puede servir una foto nítida del letrero del local recortada.
3. **Colores**: 2 colores en HEX. Si no los sabe, sácalos del logo o del local (pregunta para confirmar).
4. **Llamado a la acción**: canal (WhatsApp, web, Instagram, tienda) y la frase. Ej.: `Escribe "PLAN" por WhatsApp`.
5. **Música**: estilo (deep house, energética, emotiva, corporativa…). Busca opciones **libres de derechos y sin Content ID** (Pixabay Music: en la página del tema no debe decir "Content ID Registered"), muéstrale 2-3 links para escuchar y descarga la elegida **con su permiso**.

## brand.json
```json
{
  "name": "Memo Store",
  "colors": { "accent": "#9B5CFF", "keyword": "#8CFF3F" },
  "keywords": ["memo", "store", "plan", "whatsapp"],
  "glossary": ["Memo Store", "WhatsApp", "PLAN"],
  "font": "Montserrat",
  "logo": "logo.png",
  "watermark": null,
  "cta": { "channel": "whatsapp", "title": "Escribe \"PLAN\" por WhatsApp", "subtitle": "Te ayudamos a elegir" },
  "music": { "file": "musica.mp3", "startS": 16, "underVoice": 0.2, "gaps": 0.45, "endCard": 0.7 },
  "endCard": { "enabled": true, "seconds": 2.5, "background": "#FFFFFF", "pill": "Escribe \"PLAN\" por WhatsApp" }
}
```
- `accent`: fondo de la palabra que se está diciendo (debe contrastar con texto blanco; si es un color claro, agrega `"activeText": "#111"`).
- `keyword`: color de palabras clave (`keywords`) y detalles.
- `glossary`: nombres propios y términos técnicos; mejora la transcripción.
- `font`: `Montserrat`, `Poppins` o `Inter`.
- `music.startS`: segundo de la canción donde entra la parte con energía (analiza el volumen por tramos con ffmpeg `astats` y elige el inicio del tramo fuerte).
- `watermark`: logotipo horizontal chico (opcional) que aparece arriba a la derecha después del hook.
- Si el logo trae un borde gris o fondo distinto al de la placa final, recórtalo (`ffmpeg -vf crop=…`) o ajusta `endCard.background` al color de su fondo.

Copia los archivos (logo, música) dentro de la carpeta de la marca y referencia solo el nombre del archivo.
