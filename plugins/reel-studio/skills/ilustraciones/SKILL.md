---
name: ilustraciones
description: Dibuja ilustraciones planas a medida (SVG → PNG) y arma con ellas un clip vertical con movimiento lento de cámara para los tramos de un reel que no tienen imagen (audio en negro, locución sin tomas, explicaciones abstractas). Usar cuando un clip venga en negro o sea solo audio, cuando el usuario pida "ponle imágenes", "animaciones", "dibujos de lo que hablan", o cuando falte una toma y no se pueda volver a grabar. No necesita servicios pagos ni internet.
---

# Ilustraciones para tramos sin imagen

Se dibujan a mano como SVG (formas simples), se renderizan a PNG con el Chrome del equipo y se montan sobre el audio con zoom lento. Resultado: un `.mp4` que se normaliza como cualquier clip en el flujo de **flujo-edicion**.

## 1. Qué dibujar
- Escucha o transcribe el audio del tramo (`reel transcribir` sobre un normalizado provisorio) y divide en ideas (2 a 4 por cada 15 s). Una ilustración por idea, y solo de lo que se dice: si el audio habla de distracción y de propósito, no dibujes "comidas y dormir".
- Estilo "explainer" plano: fondo claro, una forma grande de color atrás para dar profundidad, personajes estilizados (cabeza circular, cuerpo, sin rasgos detallados), objetos reconocibles (celular, reloj, cama, mesa, libro). Sin texto dentro de la imagen.
- Paleta: los dos colores de la marca (`brand.json` → `colors.accent`, `colors.keyword`) más un oscuro (#0F172A) y un crema (#F8FAFC).
- Márgenes libres: 160 px arriba y 420 px abajo, que es donde van las etiquetas y los subtítulos.

## 2. Dibujar y renderizar
Carpeta: `~/ReelStudio/proyectos/<marca>/<video>/raw/`. Por cada idea `i`:
1. Escribe `ilus-i.svg` de 1080×1920 (`viewBox="0 0 1080 1920"`) y un `ilus-i.html` mínimo: `<body style="margin:0;background:#F8FAFC">` con el SVG inline.
2. Render: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --window-size=1080,1920 --screenshot=<ruta>/ilus-i.png file://<ruta>/ilus-i.html` (en Linux, `google-chrome` o `chromium`).
3. Verifica el tamaño (`sips -g pixelWidth -g pixelHeight` o `ffprobe`) y **mira el PNG**. Corrige proporciones, superposiciones y elementos fuera de cuadro hasta que la escena se entienda a simple vista.

## 3. Montar el clip con el audio
Con los tiempos de cada idea (t0 < t1 < … < fin) y el archivo original del audio:
1. Un tramo por ilustración, alternando acercar y alejar:
   - acercar: `ffmpeg -y -loop 1 -framerate 30 -i raw/ilus-i.png -filter_complex "[0]scale=1080:1920,zoompan=z='min(1+0.0008*on,1.12)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30" -t <dur_i> -c:v libx264 -crf 18 -pix_fmt yuv420p raw/ilus-i.mp4`
   - alejar: igual con `z='max(1.12-0.0008*on,1)'`.
2. Concatena (`-f concat -safe 0 -i lista.txt`) y agrega el audio original (`-i <audio> -map 0:v -map 1:a -shortest`) → `raw/clipN-visual.mp4`. Verifica duración ≈ la del audio y mira un fotograma de cada tramo.
3. Normaliza ese archivo en el lugar del clip original (`reel normalizar …`) y sigue el flujo normal. En ese tramo no hay cara: los overlays pueden ir grandes y arriba (`steps` si son consejos, `chips` o `badge` para ideas), y los subtítulos siguen abajo.

## 4. Si hay crédito para imágenes generadas
Si el usuario tiene un plan pago de Higgsfield u otro generador conectado en la sesión, puedes generar las imágenes con un prompt (vertical 9:16, estilo plano, sin texto) en vez de dibujarlas; avisa el costo antes. El montaje (paso 3) es el mismo. En plan gratuito la generación de imágenes está bloqueada: dibuja.
