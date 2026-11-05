---
name: nuevo-proveedor
description: Da de alta un proveedor/negocio nuevo (un tenant) en Reel Studio de punta a punta — verifica el equipo, crea su kit de marca aislado (logo, colores, música, CTA) y deja todo listo para editar su primer video. Usar cuando el usuario diga "da de alta un cliente/proveedor nuevo", "sumá un negocio nuevo", "onboarding de un tenant", "arrancá con un proveedor nuevo", "quiero agregar otra marca" o cuando vaya a editar el primer reel de un negocio que todavía no existe en ~/ReelStudio/marcas/.
---

# Alta de un proveedor nuevo (tenant)

Reel Studio es **multitenant**: cada proveedor/negocio es un tenant con su propia carpeta aislada en
`~/ReelStudio/marcas/<slug>/` (marca y archivos) y `~/ReelStudio/proyectos/<slug>/` (sus videos).
Dar de alta un proveedor = crear ese tenant y dejarlo listo para producir.

El usuario NO es técnico: explícale en lenguaje simple qué vas haciendo, no le muestres JSON ni
comandos salvo que lo pida. Responde en su idioma.
Comandos: `node "${CLAUDE_PLUGIN_ROOT}/scripts/reel.cjs" <comando>` (abajo: `reel <comando>`).

## 1. Verificar el equipo
Ejecuta `reel doctor`. Si falta algo (motor, ffmpeg, Whisper, Python), resuélvelo con la skill
**instalar** antes de seguir. No continúes si el `doctor` no da todo en ✓.

## 2. Elegir el slug del tenant
Pide el **nombre** del negocio y derivá un `slug` en minúsculas, sin espacios ni acentos
(ej. "Memo Store" → `memostore`, "Café del Sur" → `cafedelsur`).
- Si ya existe `~/ReelStudio/marcas/<slug>/`, avisá que ese proveedor ya está dado de alta y preguntá
  si querés editarlo (skill **marca**) o usar otro slug. No lo pises sin confirmar.

## 3. Crear el kit de marca
Ejecuta `reel marca <slug>` y completá su configuración siguiendo la skill **marca** (máximo 5
preguntas): nombre exacto, logo, 2 colores HEX, llamado a la acción (canal + frase) y estilo de
música **libre de derechos y sin Content ID** (Pixabay; mostrá 2-3 opciones y descargá la elegida
con permiso). Copiá logo y música dentro de `marcas/<slug>/` y referenciá solo el nombre del archivo
en `brand.json`.

## 4. Dejar listo para producir
- Confirmá que quedó `~/ReelStudio/marcas/<slug>/brand.json` con el logo y la música adentro.
- Explicá al usuario, en simple, qué quedó configurado (nombre, colores, canal de contacto, música).
- Las carpetas de cada video (`proyectos/<slug>/<video>/`) se crean al editar, con `reel nuevo`.

## 5. (Opcional) Levantamiento previo a grabar
Si el proveedor todavía no grabó, ofrecé la skill **levantamiento** para generar el PDF de 6
preguntas (con QR a su carpeta en la nube) y las autorizaciones de imagen y voz.

## 6. Primer video
Cuando tengan los clips, pasá a la skill **flujo-edicion** para armar el primer reel del tenant.

## Reglas
- Un tenant por negocio: no mezcles marcas ni archivos entre carpetas distintas.
- Música: solo libre de derechos y sin Content ID (nunca canciones comerciales).
- No subas los archivos del proveedor a servicios externos.
