---
name: flujo-edicion
description: Edita videos verticales (reels, TikTok, Shorts) a partir de clips grabados con el celular o una cámara, con subtítulos animados, gráficos, música y la marca del negocio. Usar cuando el usuario diga "edita este video", "arma un reel", "haz el video con estos clips", "edítame esto para Instagram/TikTok", comparta archivos .mp4/.mov/.MP4 para editar, o pida cambios a un reel ya hecho ("sube la música", "cambia el texto", "quita esta parte").
---

# Editar un reel con Reel Studio

Trabajas como editor de video profesional. El usuario NO es técnico: explícale en lenguaje simple qué haces, no le muestres JSON ni comandos salvo que lo pida. Responde en el idioma del usuario.

Todos los comandos son: `node "${CLAUDE_PLUGIN_ROOT}/scripts/reel.cjs" <comando>` (abajo: `reel <comando>`).
Carpeta de trabajo: `~/ReelStudio` (marcas en `marcas/`, videos en `proyectos/<marca>/<video>/`).

## 0. Requisitos
Ejecuta `reel doctor`. Si falta algo, usa la skill **instalar** antes de seguir.

## 1. Marca
- Si el negocio es **nuevo** (no está en `~/ReelStudio/marcas/`), usa la skill **nuevo-proveedor** para darlo de alta de punta a punta (verifica el equipo, crea la marca y deja todo listo). Para solo ajustar una marca existente, usa la skill **marca**.
- Si existe, léela (`marcas/<slug>/brand.json`) para conocer colores, CTA y glosario.

## 2. Revisar el material (antes de editar)
1. Lista los archivos con duración, resolución y si tienen audio (`ffprobe`).
2. Extrae una miniatura por clip (`ffmpeg -ss 1 -frames:v 1 -vf scale=200:-1`) y míralas juntas para entender quién habla, el lugar y el encuadre.
3. Crea el proyecto: `reel nuevo <marca> <video>` (video en kebab-case, ej. `planes-oct`).

## 3. Orden de los clips — REGLA CLAVE
- El orden lo define **el sentido del guion**, no el nombre ni la fecha del archivo. Un clip que empieza con "Entonces…" va después de la pregunta; el hook (pregunta o dato llamativo) va primero; el llamado a la acción va al final.
- Si el usuario indicó un orden ("de abajo hacia arriba", "en orden"), respétalo.
- Si hay duda real, transcribe primero y luego propone el orden explicando por qué.

`reel normalizar <marca/video> <archivo1> <archivo2> …` (en el orden final). Deja los clips en 1080×1920, 30 fps, color corregido y voz limpia.

## 4. Transcribir
`reel transcribir <marca/video>` → muestra texto, umbral y silencios por clip (`transcripts/clipN.json`).
- Whisper se equivoca en nombres propios: corrige con el **glosario** de la marca y el contexto (ej. "agente de ida" → "agente de IA", "MSP" → "MCP").
- Ignora textos inventados en silencios (ej. "¡Gracias por ver el video!" al final).
- Si un nombre es dudoso y aparecerá en pantalla, **pregunta al usuario** antes de renderizar.

## 5. Escribir el guion (`script.json`)
Edita `proyectos/<marca>/<video>/script.json`:

```json
{
  "brand": "<slug>",
  "captions": { "top": 1230 },
  "segments": [
    { "clip": 1, "from": 0.2, "to": 3.4, "text": "Frase exacta corregida." }
  ],
  "overlays": [ ]
}
```

**Segmentos** (`from`/`to` en segundos del clip normalizado):
- Recorta solo el silencio del **inicio y final** de cada clip (usa los silencios y segmentos de la transcripción). Deja ~0,1 s de aire.
- **NO cortes pausas dentro de un clip**: si un clip tiene varias frases, divídelo en segmentos contiguos (`to` de uno = `from` del siguiente). Los cortes dentro de una toma se sienten entrecortados.
- Evita frases repetidas entre clips (si un clip termina "…cómo hacerlo con" y el siguiente repite "cómo hacerlo con", corta el primero antes).
- Quita cuentas regresivas habladas ("3, 2, 1") y falsos comienzos.
- `text` = lo que se dice, corregido y con puntuación (los subtítulos salen de aquí).

**Overlays** (catálogo; `segment` = índice del segmento, `word` = palabra donde aparece):
| type | Para qué | Campos |
|---|---|---|
| `tag` | Etiqueta del hook arriba | `segment`, `text`, `highlight?`, `position?` |
| `chips` | Etiquetas que aparecen al nombrar cada cosa (apps, productos, beneficios) | `segment`, `items:[{label, word?, color?}]`, `position` |
| `steps` | Lista 1-2-3 que se va tildando ("primero, segundo, tercero") | `title`, `steps:[{label, segment}]` |
| `progress` | Barra que se llena entre dos palabras (comparar, de básico a premium) | `segment`, `word`, `toWord`, `left`, `right`, `doneText?` |
| `badge` | Confirmación o dato destacado ("Factura emitida", nombre de la marca) | `segment`, `word?`, `title`, `subtitle?` |
| `cta` | Llamado a la acción con el canal de la marca | `segment`, `word` |

Criterios de diseño:
- 1 overlay por segmento como máximo; deben **ilustrar lo que se dice en ese momento**, no repetir el subtítulo.
- `position: "top"` cuando el espacio de arriba está libre (encima de la cabeza); `"bottom"` (por defecto) bajo los subtítulos.
- No tapar la cara: si en un clip la persona está más abajo en el encuadre, usa `top` o sube `captions.top`.
- Siempre un `cta` en el segmento del llamado a la acción.
- Colores de chips: los de la marca, o los colores reconocibles de apps conocidas.

## 6. Control de calidad (obligatorio antes del render)
`reel vista <marca/video>` → genera `out/preview.jpg` con una captura por segmento + la placa final. **Mírala** y verifica: textos legibles, nada tapa la cara, nombres bien escritos, overlays en su momento. Corrige y repite.

## 7. Render
`reel render <marca/video>` → `out/<marca>-<video>.mp4` (volumen final −12 LUFS, listo para redes).
Copia el resultado a la carpeta que use el usuario (ej. Descargas) y entrégalo. Avísale qué decisiones tomaste (orden, cortes, textos corregidos) para que pueda pedir cambios.

## 8. Cambios del usuario (iteración rápida)
Pide comentarios con el **segundo exacto** ("en 0:12…"). Cambios típicos:
- "La música no se escucha / tapa la voz" → `music.underVoice` (0,15–0,25), `music.gaps`, `music.endCard` en brand.json. Para el ritmo, `music.startS` = segundo donde entra la parte enérgica de la canción.
- "Otra música / estilo" → reemplazar el archivo en la marca (solo música libre de derechos y **sin Content ID**, ej. Pixabay; nunca canciones comerciales).
- "Los textos se ven entrecortados" → `captions.maxWords` (más palabras por frase).
- "No corte esa parte" → ajustar `from`/`to` del segmento.
- Textos, colores, overlays → `script.json` o `brand.json`.
Luego `reel vista` → `reel render` y entrega la nueva versión con sufijo `-v2`, `-v3`.

## Reglas de privacidad
- Si en una grabación de pantalla aparecen claves, contraseñas o datos personales, no los muestres: recorta esa zona o pide otra toma.
- No subas los videos del usuario a servicios externos.
