---
name: flujo-edicion
description: Edita videos verticales (reels, TikTok, Shorts) a partir de clips grabados con el celular o una cámara, con subtítulos animados en varios estilos (hormozi, clásico, cinemático, karaoke, calma), ajuste de color, gráficos, música, locución aparte para tomas mudas y la marca del negocio. Usar cuando el usuario diga "edita este video", "arma un reel", "haz el video con estos clips", "edítame esto para Instagram/TikTok", comparta archivos .mp4/.mov/.MP4 para editar, o pida cambios a un reel ya hecho ("sube la voz", "cambia el estilo", "ponlo en blanco y negro", "cambia el texto", "quita esta parte").
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
- **Clips horizontales** (apaisados, de WhatsApp, de dron): el recorte vertical deja afuera lo que no esté al centro. Mira la miniatura y pasa `archivo@x` (0 izquierda, 0.5 centro, 1 derecha) con la posición de la persona; si se mueve durante el clip, después `reel seguir <marca/video> <N> --puntos "t:x …"` (ver 4b.3). Resolución baja (menos de 1080 de alto): no uses `--zoom`.
- **Clip con la imagen en negro o sin imagen útil** (solo audio): no lo normalices tal cual; primero fabrícale un visual con la skill **ilustraciones** (dibujos a medida con zoom lento sobre el audio) y normaliza el archivo resultante.

## 3b. Estilo de edición y color (antes de escribir el guion)
Pregunta en una sola frase **qué quiere transmitir** el video (si no lo dijo ya): vender/urgencia, explicar/contar, premium/elegante, joven/TikTok, bienestar/calma. Con eso:
- `reel estilo <marca/video> <intención>` (vender | explicar | premium | joven | bienestar) → el motor **sortea** un estilo entre los que van con esa intención y lo deja escrito en `script.json` (`estilo`). Si el usuario pidió un estilo por nombre, fíjalo directo: `reel estilo <marca/video> hormozi|clasico|cinematico|karaoke|calma`.
- **Cuéntale al usuario qué estilo salió y cómo se ve** (una línea; `reel estilo` sin argumentos lista las descripciones) y ofrécele cambiarlo. Cuando pida otro, `reel estilo … <nombre>` o `… sortear` y repite vista → render.
- Color: por defecto `natural`. Si el material está apagado, o el usuario pide "más color", "blanco y negro", "cálido", "frío", "look de cine", "vintage": `reel color <marca/video> <preset>`. Para afinar ("un poco más cálido", "menos saturado"): `reel color <marca/video> '{"base":"calido","saturacion":1.2,"temperatura":0.6,"vineta":0.3}'` (brillo, contraste, saturacion, temperatura −1…1, vineta 0…1, sepia 0…1). Mira siempre la vista previa después de cambiar el color.
- Estilos: **hormozi** (mayúsculas, caja de color, pop: vende y apura), **clasico** (minúsculas en pastilla oscura: explica), **cinematico** (serif, bandas de cine, zoom lento: autos, inmuebles, gastronomía), **karaoke** (2–3 palabras enormes al centro: TikTok, joven), **calma** (letra redonda, pastilla suave: bienestar, salud, belleza).

## 3c. Corrección de color y rescate (después de normalizar y seguir)
- Siempre: `reel corregir <marca/video> todos --auto`. Trabaja clip por clip sobre los ya normalizados y deja una copia intocable (`clipN.base.mp4`); cada corrección parte de esa base, así que se puede repetir sin degradar.
- **Mira `out/corregir.jpg`**: por clip, arriba el antes y abajo el después. Si algo se ve lavado, exagerado o con la piel rara, afina o vuelve atrás.
- El auto hace: balance de blancos (gray-world con tope), exposición y contraste, **igualar** los clips entre sí (cámaras distintas: dron, DJI, celular) para que parezcan una sola película, ruido + nitidez en fuentes de menos de 1080 px, y estabilizar solo si la imagen tiembla (un dron suave o un plano fijo no se tocan).
- Manual por clip: `--wb auto|<kelvin>`, `--exposicion auto|<-1..1>`, `--igualar <N>`, `--estabilizar`, `--ruido`, `--nitidez`.
- Look: `--lut cine|calido|frio` (LUTs propias en `~/ReelStudio/luts/`) o un `.cube` propio (`--lut ruta/mi.cube`).
- `reel corregir <marca/video> <N|todos> --original` vuelve al clip normalizado.
- La corrección por clip va **antes** del ajuste global `reel color` (3b), que es el look del video entero. Si vuelves a `normalizar` o `seguir`, la base y la corrección de ese clip se descartan: repite `corregir`.

## 3d. Ritmo: jump cuts y transiciones (clips con voz grabada)

- **Jump cuts**: `reel cortes <marca/video> on` quita las pausas de más de 0.45 s dentro de cada clip (deja 0.12 s de aire a cada lado) y alterna el encuadre (100 % ↔ 112 %) en cada corte para que se sienta intencional. `reel cortes <marca/video> <segundos>` cambia la pausa mínima (más bajo = más cortes; 0.3 si el video sigue lento; 0.6 si suena entrecortado). `off` los apaga. Después de `construir` el log dice `cortes: N pausas quitadas (X s)`; mira la vista previa y, si suena entrecortado, sube el número o apaga. Para apagar sólo el zoom alterno: `"cortes": { "pausas": 0.45, "aire": 0.12, "zoom": false }` en `script.json`.
- **No aplica con locución aparte** (el comando avisa "cortes: no aplica con locución"): ahí la voz manda el tiempo.
- **Transición entre clips** según el estilo: hormozi `flash`, karaoke `zoom` (zoom-through con desenfoque), clasico y calma `fundido` (cruzado, 8 frames), cinematico `fundido` largo (14 frames). Cambiarla: `"transicion": "corte" | "flash" | "fundido" | "zoom"` en `script.json`. Los jump cuts dentro de un mismo clip no llevan transición, sólo el zoom alterno.
- Si el usuario dice "muy lento / hay muchos silencios" → `cortes … on` (o un número menor). "Muy brusco / mareado" → `cortes … off` o `"zoom": false`.

## 3e. Ocultar placas y datos de terceros (después de normalizar/seguir/corregir)
- **Por defecto, en videos de venta de vehículos SIEMPRE se ocultan las placas** (y cualquier cara de terceros, cédula, teléfono ajeno o dato personal) en **todas** las tomas donde se vean, salvo que el cliente pida lo contrario. Hacerlo antes del render, nunca dejarlo "para después".
- Ubicar: `reel ocultar <marca/video> <N> --ver [t1,t2,…]` imprime el tamaño del clip y guarda `out/ocultar-clipN.jpg` (8 cuadros con regla amarilla en píxeles). Mira el JPG con Read y anota `x,y,w,h` (esquina sup. izq. y tamaño, en px) de la placa en varios instantes. Si no la ves bien, pide más instantes (`--ver 0.5,1,1.5,…`).
- Aplicar: `reel ocultar <marca/video> <N> --caja "x,y,w,h@t;x,y,w,h@t" [--modo blur|pixel] [--margen 0.25] [--desde s --hasta s]`. Rastrea hacia adelante y hacia atrás desde la primera caja, así que cubre todo el clip. **Pon una caja de reinicio cada vez que cambie mucho el ángulo o la distancia** (dron: una cada 1.5–3 s si el carro gira o se acerca) y una justo cuando la placa asoma por un borde. Si el aviso dice que el rastreador se perdió desde X s, agrega una caja cerca de ese instante. Usa `--hasta` cuando la placa sale del cuadro.
- **Verificar siempre**: `reel ocultar <marca/video> <N> --ver 8_instantes_repartidos` y mira `out/ocultar-clipN.jpg` (caja roja = zona rastreada) y `out/ocultar-clipN-detalle.jpg` (zoom): la placa debe quedar ilegible en todos los cuadros, incluidos los de entrada y salida. Si asoma, repite con cajas extra o `--margen 0.4`.
- Es idempotente: el original queda en `clips/clipN.sinocultar.mp4` y repetir el comando parte siempre de él. `--quitar` vuelve al original. Si luego repites `corregir` o `seguir`, el ocultar se reaplica solo (tras `seguir` el encuadre cambia: revisa las cajas con `--ver`); `normalizar` lo descarta.
- **Portada**: si el fotograma elegido muestra una placa, la portada sale de los clips de origen y la placa se vería. Elige un `--frame` donde no se vea o tapa esa toma antes; revisa `out/portada.png`. Una sola zona por comando: otros carros con placa legible en el fondo requieren otro paso aparte.

## 4. Transcribir
`reel transcribir <marca/video>` → muestra texto por frase con tiempos, umbral y silencios por clip (`transcripts/clipN.json`). Un clip **sin audio** se informa como toma muda: para esos se usa la locución (sección 4b).
- Whisper se equivoca en nombres propios: corrige con el **glosario** de la marca y el contexto (ej. "agente de ida" → "agente de IA", "MSP" → "MCP").
- Ignora textos inventados en silencios (ej. "¡Gracias por ver el video!" al final).
- Si un nombre es dudoso y aparecerá en pantalla, **pregunta al usuario** antes de renderizar.

## 4b. Tomas mudas con locución aparte (productos, autos, lugares, drone)
Cuando los clips no tienen a nadie hablando, la voz va aparte y **manda el tiempo** del video:
1. Escribe el guion de la locución con el usuario (corto: 70–90 palabras por 40 s) y **adáptalo al habla del lugar** del cliente (en Ecuador: "carrito", "poquito", "parquear", "chamba"; sin exagerar). La voz, en este orden de preferencia:
   - **Grabada** por el cliente o el usuario con el celular, en un lugar silencioso: `reel locucion <marca/video> <voz.m4a>` (la limpia y normaliza). Es la que mejor suena y es gratis.
   - **Generada con voz humana de calidad**: si en la sesión está conectado Higgsfield (herramientas `generate_audio`, `list_voices`), genera el guion con `model: "text2speech_v2", variant: "elevenlabs"` y una voz en español (p. ej. "Juan"), avisando antes el costo en créditos (`get_cost: true`; ~1,2 créditos por 30 s). Descarga el mp3 del `result_url` y cárgalo con `reel locucion <marca/video> <archivo.mp3>`. Si el usuario tiene una API key de ElevenLabs, pídesela y úsala igual.
   - **Gratis de respaldo**: `reel locucion <marca/video> --generar "<texto o archivo.txt>" [--voz andrea|luis|dalia|jorge]` (voces neuronales edge-tts; `say` si no hay internet). Avisa que es una voz sintética y que para publicar conviene una grabada.
   Las voces del sistema (`say`) y edge-tts suenan robóticas para un cliente exigente: no las entregues como final sin decirlo.
2. El comando transcribe la locución por frase con tiempos. Con eso, en `script.json` cada segmento lleva `at` (segundo de la locución en que empieza), `clip` y `from` (segundo del clip desde el que se muestra), y `text` (lo que se dice en ese tramo, para los subtítulos). El segmento dura hasta el `at` del siguiente; el clip tiene que ser al menos así de largo (si no, el motor avisa). `sonido: 0.5` deja oír el audio propio del clip (motor, ambiente) debajo de la voz.
3. Tomas horizontales (dron): `normalizar` igual y luego `reel seguir <marca/video> <N> --caja "t:x,y,w,h" [--zoom 1.4]` rastrea un objeto (x,y = esquina superior izquierda, fracciones 0..1, medidas con la regla de `out/seguir-clipN-fuente.jpg`). Varias cajas separadas por `;` reinician el tracker en cada una (corrige la deriva): `--caja "0.9:0.45,0.6,0.14,0.16;7.5:0.54,0.51,0.21,0.27"`. Recomendado: una caja cada 6–8 s en tomas de dron. El centro se limita a 0.08…0.92; si el rastreo se pierde, se descartan los últimos 1.5 s (y saltos bruscos previos) y el encuadre se mantiene. `--cara` sigue la cara más grande (personas; necesita los modelos que baja `instalar`). `--auto` (movimiento) y `--puntos "t:x …"` quedan como alternativa. **Mira siempre** `out/seguir-clipN.jpg`; si el rastreo avisa "perdió el objeto desde t=…", parte la toma o usa `--puntos` ahí. `archivo@x` en `normalizar` queda solo para tomas estáticas.
4. El resto (overlays, estilo, color, vista, render) es igual. Para estos videos suele ir bien `cinematico` o `clasico`.

## 5. Escribir el guion (`script.json`)
Edita `proyectos/<marca>/<video>/script.json`:

```json
{
  "brand": "<slug>",
  "intencion": "vender",
  "estilo": "hormozi",
  "color": "natural",
  "captions": {},
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
| `imagen` | Foto o ilustración sobre el video (producto, dato visual, ilustración) | `segment`, `word?`, `file`, `position?` (top/bottom/centro, def. top), `size?` (0.3–0.9 del ancho, def. 0.55), `shape?` (tarjeta/redondo/libre), `seconds?` (def. hasta fin del segmento), `entrada?` (pop/deslizar). `file` puede ser ruta absoluta o relativa al proyecto; `construir` la copia a `media/` y deja solo el nombre |
| `tercio` | Tercio inferior con nombre y cargo cuando aparece una persona nueva | `segment`, `word?`, `nombre`, `cargo?`, `seconds?` (def. 4), `lado?` (izquierda/derecha). Va sobre los subtítulos (y≈1080–1200) |

Criterios de diseño:
- 1 overlay por segmento como máximo; deben **ilustrar lo que se dice en ese momento**, no repetir el subtítulo.
- `position: "top"` cuando el espacio de arriba está libre (encima de la cabeza); `"bottom"` (por defecto) bajo los subtítulos.
- No tapar la cara: si en un clip la persona está más abajo en el encuadre, usa `top` o sube `captions.top`.
- Siempre un `cta` en el segmento del llamado a la acción.
- Colores de chips: los de la marca, o los colores reconocibles de apps conocidas.
- `imagen`: usa `position: "top"` o `"bottom"` (no tapan subtítulos 1230–1530). `top` queda sobre la cabeza del hablante: con planos cerrados tapa la frente; baja `size` (0.35–0.45) o usa `bottom`/`redondo`. `centro` sí puede pisar subtítulos: solo con `seconds` cortos.
- `word` ancla la entrada a esa palabra DEL MISMO segmento; si no está en el segmento, entra al inicio del segmento.
- `tercio`: una vez por persona, al presentarla; 3–5 s. Respeta radio y mayúsculas del estilo activo.
- Un overlay por segmento: al sumar uno, quita el otro del mismo segmento.

## 4c. Lo que falta grabar
Si el material no cubre una parte del guion (no hay toma del interior, falta el cierre, un clip venía en negro), no lo inventes: usa lo que hay, dile al usuario exactamente qué toma falta y cuánto dura, y entrega igual. Un tramo sin imagen se resuelve con la skill **ilustraciones**; una frase que no se grabó no se pone en los subtítulos.

## 5b. Voz fina, música y efectos de sonido

### Voz fina
`reel audio <marca/video> <N|todos> [--eq clara|calida|radio] [--deess] [--puerta] [--auto]` reprocesa SOLO el audio del clip (el video se copia sin recodificar) y lo deja otra vez a −13 LUFS.
- `--eq clara`: más presencia y menos "caja" (voz apagada, micrófono del celular). `calida`: más cuerpo, voz fina o chillona. `radio`: voz de locutor (recorta graves y agudos, compresión).
- `--deess`: suaviza las "s" chillonas (deesser).
- `--puerta`: baja el ruido de fondo y el eco de cuarto entre frases. OJO: ffmpeg no tiene de-reverb real; esto es una aproximación (puerta de ruido + reductor FFT). Si el cuarto hace mucho eco, avisar al usuario que lo ideal es regrabar.
- `--auto`: eq clara + deess en cada clip, y puerta solo si el ruido medido en los silencios (transcripts/clipN.json → silences) supera −45 dB. Imprime una línea por clip con lo aplicado y el ruido de fondo medido.
- Se aplica siempre desde la base (`clips/clipN.base.mp4`, la comparte con `corregir`); se guarda `clips/clipN.audio.json`. `--original` vuelve al audio de la base.
- En modo locución, un clip sin voz propia (sin audio o `sonido` 0) se salta con un aviso.
- ORDEN: si se va a usar `corregir`, correrlo ANTES de `audio`. `corregir` recodifica el video desde la base y copia el audio de la base: pisaría la voz ya afinada.
- Después de cambiar el audio hay que volver a `transcribir` solo si cambió el contenido; el EQ no mueve tiempos.

### Efectos de sonido (sin acción del usuario)
`construir` genera (si faltan) `~/ReelStudio/sfx/{whoosh,pop,ding}.wav` (propios, sin licencias, −18 LUFS) y los copia a `<proyecto>/_sfx/`. El motor los dispara al entrar cada gráfico: tag/badge/cta/progress → whoosh; chips → un pop por etiqueta; steps → un ding por paso. Nada en el frame 0 ni en la placa final.

### Música

Todo video lleva música. Si la marca no tiene `music.file` en su `brand.json`:
1. Primero ofrece una pista libre de derechos sin Content ID (Pixabay) y cópiala a `~/ReelStudio/marcas/<marca>/`.
2. Si no hay, compónla: `... musica <marca> <ánimo>` según la intención: vender→energico, explicar→lofi, premium→cine, joven→trap, bienestar→calma. Deja `musica.strudel` y `musica.mp3` en la marca y actualiza `brand.json`.
3. Dile al usuario qué se compuso (ánimo, bpm, tonalidad, semilla) y ofrécele cambiar el ánimo o la semilla (`--semilla N` repite o varía la pista; `--dur` ajusta el largo).
4. Para pedidos concretos ("algo más oscuro", "con más ritmo") escribe tú un `.strudel` a mano (solo sintetizadores `sawtooth|square|triangle|sine` y ruido `s("white")`, nunca samples) y pásalo: `... musica <marca> ruta/patron.strudel`.
Requiere Google Chrome e internet (carga el motor de Strudel).

## 6. Control de calidad (obligatorio antes del render)
`reel vista <marca/video>` → genera `out/preview.jpg` con una captura por segmento + la placa final. **Mírala** y verifica: textos legibles, nada tapa la cara, nombres bien escritos, overlays en su momento. Corrige y repite.
`reel vista <marca/video> --guias` hace lo mismo pero marca en rojo lo que tapa la interfaz de Instagram Reels / TikTok (barra superior 0–220 px, columna de botones x 930–1080 entre y 700 y 1500, franja inferior 1500–1920). Si un texto cae en rojo, muévelo (`position`) o acórtalo. Los subtítulos van en y 1230–1530, así que el borde inferior de 1500 es orientativo: la descripción tapa más cuanto más larga sea. Los overlays `top` empiezan en y≈250, fuera de la barra superior.
Después de `render`, corre `reel revisar <marca/video>`: lista ✓/✗/ℹ y sale con código 1 si hay ✗. Revisa: mp4 1080x1920 a 30 fps, duración ≤ 90 s (ℹ si > 60 s), volumen −13 a −11 LUFS y true peak ≤ −1 dBTP, música audible en la placa final (últimos 2 s > −30 LUFS), primera palabra antes de 1.5 s, overlays en zonas seguras (ℹ) y `tag`/`badge` de más de 40 caracteres (✗), textos de segmentos vacíos (✗), huecos > 0.1 s entre segmentos del mismo clip (ℹ), `cta` presente si la marca tiene, estilo/color fijados, música en la marca (✗ si falta). Corrige todo ✗ antes de entregar; los ℹ son avisos a juicio.

## 7. Render y entrega
`reel render <marca/video>` → `out/<marca>-<video>.mp4` (volumen final −12 LUFS, listo para redes). Antes de entregar, mide: `ffmpeg -hide_banner -i <mp4> -af ebur128 -f null - 2>&1 | grep -o 'I: *-[0-9.]* LUFS' | tail -1` (≈ −11,5 a −12,5) y que la placa final tenga música (`-sseof -2`, mayor que −30 LUFS). Mira 3 o 4 fotogramas del mp4 final (`ffmpeg -ss <s> -frames:v 1`), no solo la vista previa.
Entrega: copia el mp4 a la carpeta del usuario (Descargas) con un nombre claro, adjúntalo en el chat si la herramienta lo permite y escribe la ruta completa. Cuenta en 5 líneas qué decidiste (orden, cortes, estilo sorteado, color, música compuesta, textos corregidos) y qué no pudiste verificar o qué falta grabar. Cierra ofreciendo cambios "con el segundo exacto".

## 7b. Publicar
Antes de subir el video, prepara el paquete de publicación (todo sale en `out/`):
1. `reel portada <marca/video> [--frame n] [--titulo "…"] [--sub "…"]` → `out/portada.png` 1080x1920. El fotograma sale de los clips de origen (sin subtítulos ni overlays; `--frame` es un frame de la línea de tiempo a 30 fps). Sin `--frame` elige, entre 5 candidatos del primer tercio, el de mayor luma. Sin `--titulo` usa el texto del primer overlay `tag` o las primeras 6 palabras del guion. Necesita Google Chrome (o `REEL_BROWSER`). Mira el PNG.
2. `reel srt <marca/video>` → `out/<marca>-<video>.srt` (mismas frases que los subtítulos, sin solapes) y `out/<marca>-<video>.txt` (guion corrido, para pegar en la descripción del post). Requiere `construir`/`render` previo.
3. `reel exportar <marca/video> --formato cuadrado|horizontal` (requiere el mp4 de `render`). `cuadrado` = 1080x1350 (4:5, feed), recorte vertical y 285–1635 (los subtítulos entran; los overlays `top` pueden quedar parcialmente cortados: el comando lo avisa). `horizontal` = 1920x1080 con el vertical centrado sobre el mismo video desenfocado y oscurecido. Mismo audio. Tarda: recodifica el video.

## 8. Cambios del usuario (iteración rápida)
Pide comentarios con el **segundo exacto** ("en 0:12…"). Cambios típicos:
- "No se escucha bien el mensaje / la voz está baja" → `reel voz <marca/video> fuerte` (sube la voz y baja la música debajo de ella; `normal` o `suave` para volver). La voz ya sale normalizada en dos pasadas a −13 LUFS y la mezcla final a −11,5; si aun así se oye baja, el problema es la grabación: pide otra toma o la locución aparte.
- "Cambia el estilo / más sobrio / más llamativo / otro" → `reel estilo <marca/video> <nombre | intención | sortear>`.
- "Se ve lavado / amarillento / los clips se ven distintos entre sí" → `reel corregir <marca/video> todos --auto` (o `--wb` / `--igualar <N>` en un clip).
- "Tiembla la imagen" → `reel corregir <marca/video> <N> --estabilizar`.
- "Se ve pixelado" → `reel corregir <marca/video> <N> --ruido --nitidez`.
- "Más color / blanco y negro / más cálido / se ve lavado" → `reel color <marca/video> <preset o json>` (`revivir` para material apagado).
- "La música no se escucha / tapa la voz" → `music.underVoice` (0,15–0,25), `music.gaps`, `music.endCard` en brand.json. Para el ritmo, `music.startS` = segundo donde entra la parte enérgica de la canción.
- "Otra música / estilo" → reemplazar el archivo en la marca (solo música libre de derechos y **sin Content ID**, ej. Pixabay; nunca canciones comerciales).
- "Los textos se ven entrecortados" → `captions.maxWords` (más palabras por frase).
- "No corte esa parte" → ajustar `from`/`to` del segmento.
- Textos, colores, overlays → `script.json` o `brand.json`.
- "Ponle imágenes / animaciones a esa parte" → skill **ilustraciones** sobre ese clip.
- "Que siga al carro / se sale del cuadro" → `reel seguir` con `--caja`/`--cara`/`--puntos` nuevos.
- "Quita las pausas / más ritmo / jump cuts" → `reel cortes <marca/video> on|<segundos>`; "muy brusco" → `off`. "Otra transición" → `"transicion"` en script.json (corte, flash, fundido, zoom).
- "Se oye apagada / como en una lata / muy aguda / con eco / ruido de fondo / las eses chillan" → `reel audio <marca/video> <N|todos> --eq clara|calida|radio / --deess / --puerta`; ver con `render`. "Dejala como estaba" → `audio … --original`.
- "Los sonidos de los gráficos son muy fuertes / no los quiero" → en `marcas/<slug>/brand.json`: `"sfx": { "enabled": false }` o `"sfx": { "volume": 0.2 }` (por defecto activados a 0.35; en estilos `calma` y `cinematico` suenan a la mitad). Luego `render`.
- "Ponle foto de producto / presenta a esta persona" → overlay `imagen` / `tercio`. "Necesito la portada / los subtítulos / versión para feed o YouTube" → sección 7b.
Luego `reel vista` → `reel render` y entrega la nueva versión con sufijo `-v2`, `-v3`. Máximo dos rondas de cambios por entrega: pide los comentarios juntos.

## Reglas de privacidad
- Si en una grabación de pantalla aparecen claves, contraseñas o datos personales, no los muestres: recorta esa zona o pide otra toma.
- No subas los videos del usuario a servicios externos.
