---
name: levantamiento
description: Genera el PDF de levantamiento express previo a una grabación (6 preguntas clave en una hoja, con QR a la carpeta en la nube) y las hojas de autorización de imagen y voz para adultos y menores. Usar cuando el usuario diga "prepara el levantamiento", "formulario para el cliente", "autorizaciones de imagen", "qué le pregunto al cliente antes de grabar" o planifique un rodaje.
---

# Levantamiento express + autorizaciones

Comando:
```
node "${CLAUDE_PLUGIN_ROOT}/scripts/reel.cjs" levantamiento "<Proyecto · Lugar>" "<link carpeta>" "<carpeta salida>"
```
- El link (Google Drive u otra nube) es opcional: si existe, se imprime como código QR para que el cliente suba logo, colores y recursos.
- Salida por defecto: `~/Downloads`. Genera:
  - `Levantamiento_Express_<Proyecto>.pdf` (1 hoja): logo/colores/tipografía + QR, nombres y frase de cierre, música, formato de cámara (vertical 9:16 u horizontal 4K para recortar, fps), autorizaciones y aprobador/plazo.
  - `Autorizaciones_Imagen_<Proyecto>.pdf` (2 hojas): planilla de mayores de edad y de menores con firma del representante.

Al entregar:
- Recuerda que las autorizaciones son una **plantilla referencial** y deben validarse con asesoría legal (protección de datos y, si aplica, normativa electoral).
- Sugiere que el cliente comente cada versión del video indicando el **segundo exacto** y que haya máximo 2 rondas de cambios.
- Las respuestas del levantamiento alimentan la skill **marca** (logo, colores, CTA, música).
