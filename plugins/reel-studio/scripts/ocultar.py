"""
Ocultar zonas que se mueven dentro de un clip (placas, caras de terceros, teléfonos…) para `reel ocultar`.

Uso:
  python ocultar.py aplicar <entrada.mp4> <salida.mp4> --caja "x,y,w,h@t[;x,y,w,h@t…]" [--modo blur|pixel]
                    [--margen 0.25] [--desde s] [--hasta s] --traza <traza.json>
  python ocultar.py ver <video.mp4> <hoja.jpg> [--tiempos t1,t2,…] [--traza traza.json] [--detalle detalle.jpg]
  python ocultar.py rastrear <video.mp4> --caja "…" --traza <traza.json>

Las coordenadas están en píxeles del video. Cada caja "x,y,w,h@t" (x,y = esquina superior izquierda) es la zona
correcta en el segundo t; el tracker CSRT se reinicia en cada una. Desde la primera caja se rastrea hacia
adelante y también hacia atrás hasta el segundo 0.
La traza (JSON) guarda, por cuadro, el centro y tamaño de la zona rastreada ya suavizada: [cx, cy, w, h] en px.
"""
import json
import statistics
import subprocess
import sys
import time

WORK_W = 540          # ancho de trabajo del tracker (reescalado)
SMALL_PX = 70         # cajas más chicas (en px de trabajo) se agrandan para el tracker (CSRT pierde lo muy chico)


def fail(msg, code=2):
    sys.stderr.write(msg + "\n")
    sys.exit(code)


try:
    import cv2
    import numpy as np
except ImportError:
    fail("falta OpenCV: node reel.cjs instalar")


# ── utilidades de video ─────────────────────────────────────────────────────
def info(video):
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        fail(f"no pude abrir el video: {video}")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    fps_txt = "30"
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=r_frame_rate", "-of", "csv=p=0", video], capture_output=True, text=True)
        if r.stdout.strip() and "/" in r.stdout.strip():
            a, b = r.stdout.strip().split("/")
            if float(b) > 0 and float(a) > 0:
                fps_txt = f"{a}/{b}"
        elif r.stdout.strip():
            fps_txt = r.stdout.strip()
    except OSError:
        pass
    if "/" in fps_txt:
        a, b = fps_txt.split("/")
        fps = float(a) / float(b)
    else:
        fps = float(fps_txt)
    return W, H, fps, fps_txt


def parse_cajas(spec, W, H):
    out = []
    try:
        for c in spec.split(";"):
            c = c.strip()
            if not c:
                continue
            geo, _, t = c.partition("@")
            x, y, w, h = [float(v) for v in geo.split(",")]
            out.append((float(t) if t else 0.0, x, y, w, h))
        assert out and all(w > 1 and h > 1 for _, _, _, w, h in out)
    except (ValueError, AssertionError):
        fail('--caja espera "x,y,w,h@t[;x,y,w,h@t…]" (píxeles del clip y segundos; w y h > 1)')
    out.sort()
    return out


def make_tracker():
    f = getattr(cv2, "TrackerCSRT_create", None) or getattr(getattr(cv2, "legacy", None), "TrackerCSRT_create", None)
    if f is None:
        fail("esta build de OpenCV no trae el tracker CSRT (hace falta opencv-contrib-python): node reel.cjs instalar")
    return f()


# ── rastreo ─────────────────────────────────────────────────────────────────
def seguir_segmento(tr, frames, box_w):
    """frames[0] ya inicializó el tracker; devuelve una caja (cx,cy,w,h) por cada frame de frames[1:].
    Si el tracker pierde el objeto se mantiene la última caja buena (mejor tapar de más)."""
    res = []
    last = None
    perdido = None
    for k, fr in enumerate(frames):
        ok, b = tr.update(fr)
        if ok and b[2] > 2 and b[3] > 2:
            last = [b[0] + b[2] / 2, b[1] + b[3] / 2, b[2], b[3]]
        elif perdido is None:
            perdido = k
        res.append(list(last) if last else None)
    return res, perdido


def rastrear(video, cajas, W, H, fps):
    s = WORK_W / W if W > WORK_W else 1.0
    sz = (round(W * s), round(H * s))
    cap = cv2.VideoCapture(video)
    ks = []  # índice de cuadro de cada caja

    def idx(t):
        return max(0, int(round(t * fps)))

    ks = [idx(c[0]) for c in cajas]
    k0 = ks[0]
    # cuadros 0..k0 en memoria (para ir hacia atrás); el resto se lee en flujo
    head = []
    for _ in range(k0 + 1):
        ok, fr = cap.read()
        if not ok:
            break
        head.append(cv2.resize(fr, sz, interpolation=cv2.INTER_AREA) if s != 1.0 else fr)
    if len(head) <= k0:
        fail("la primera caja cae fuera del clip (t mayor a la duración)")
    boxes = {}   # índice de cuadro -> [cx,cy,w,h] en px de trabajo
    perdidos = []

    def init_tracker(fr, c):
        _, x, y, w, h = c
        bx = [x * s, y * s, w * s, h * s]
        grow = 1.0
        if max(bx[2], bx[3]) < SMALL_PX:
            grow = min(2.0, SMALL_PX / max(bx[2], bx[3]) if max(bx[2], bx[3]) else 2.0)
            grow = max(grow, 1.3)
            cx, cy = bx[0] + bx[2] / 2, bx[1] + bx[3] / 2
            bx = [max(0, cx - bx[2] * grow / 2), max(0, cy - bx[3] * grow / 2), bx[2] * grow, bx[3] * grow]
        tr = make_tracker()
        tr.init(fr, tuple(int(round(v)) for v in bx))
        return tr, grow

    def reduce(b, grow):
        return [b[0], b[1], b[2] / grow, b[3] / grow]

    # hacia atrás desde la primera caja
    c0 = cajas[0]
    boxes[k0] = [(c0[1] + c0[3] / 2) * s, (c0[2] + c0[4] / 2) * s, c0[3] * s, c0[4] * s]
    if k0 > 0:
        tr, grow = init_tracker(head[k0], c0)
        back, perd = seguir_segmento(tr, [head[i] for i in range(k0 - 1, -1, -1)], c0[3] * s)
        fallback = boxes[k0]
        for j, b in enumerate(back):
            boxes[k0 - 1 - j] = reduce(b, grow) if b else fallback
        if perd is not None:
            perdidos.append(("atrás", (k0 - 1 - perd) / fps))
    # hacia adelante, caja por caja
    i = k0
    fr = head[k0]
    head = None
    cur_box = 0
    perdido_seg = False
    last_good = boxes[k0]
    tr, grow = init_tracker(fr, cajas[0])
    ended = False
    while not ended:
        ok, fr = cap.read()
        if not ok:
            break
        i += 1
        fr = cv2.resize(fr, sz, interpolation=cv2.INTER_AREA) if s != 1.0 else fr
        if cur_box + 1 < len(cajas) and i >= ks[cur_box + 1]:
            cur_box += 1
            c = cajas[cur_box]
            tr, grow = init_tracker(fr, c)
            last_good = [(c[1] + c[3] / 2) * s, (c[2] + c[4] / 2) * s, c[3] * s, c[4] * s]
            boxes[i] = last_good
            perdido_seg = False
            continue
        if perdido_seg:
            boxes[i] = last_good
            continue
        ok, b = tr.update(fr)
        if ok and b[2] > 2 and b[3] > 2:
            last_good = reduce([b[0] + b[2] / 2, b[1] + b[3] / 2, b[2], b[3]], grow)
            boxes[i] = last_good
        else:
            perdido_seg = True
            perdidos.append(("adelante", i / fps))
            boxes[i] = last_good
    cap.release()
    # índices posteriores a la caja k0 que no llegaron a leerse se rellenan con la última caja buena
    total = max(boxes) + 1
    serie = [[v / s for v in boxes[j]] for j in range(total)]
    return serie, perdidos


def suavizar(serie):
    """Mediana de ventana 5 + media móvil centrada de 5 muestras, por componente (cx, cy, w, h)."""
    n = len(serie)
    out = [list(p) for p in serie]
    for k in range(4):
        col = [p[k] for p in serie]
        med = [statistics.median(col[max(0, i - 2): i + 3]) for i in range(n)]
        ma = [sum(med[max(0, i - 2): i + 3]) / len(med[max(0, i - 2): i + 3]) for i in range(n)]
        for i, v in enumerate(ma):
            out[i][k] = v
    return out


# ── difuminado ──────────────────────────────────────────────────────────────
def expandir(caja, margen, W, H):
    cx, cy, w, h = caja
    m = max(6.0, margen * max(w, h))
    x0 = cx - w / 2 - m
    y0 = cy - h / 2 - m
    x1 = cx + w / 2 + m
    y1 = cy + h / 2 + m
    return x0, y0, x1, y1


def aplicar_cuadro(fr, caja, modo, margen):
    H, W = fr.shape[:2]
    x0, y0, x1, y1 = expandir(caja, margen, W, H)
    bw, bh = x1 - x0, y1 - y0
    f = max(4.0, 0.15 * min(bw, bh))        # ancho del borde suave (fuera de la caja agrandada)
    pad = int(3 * f) + 2
    X0, Y0 = max(0, int(x0) - pad), max(0, int(y0) - pad)
    X1, Y1 = min(W, int(x1) + pad + 1), min(H, int(y1) + pad + 1)
    if X1 - X0 < 4 or Y1 - Y0 < 4:
        return fr
    roi = fr[Y0:Y1, X0:X1]
    rh, rw = roi.shape[:2]
    if modo == "pixel":
        cell = max(6.0, min(bw, bh) / 3.0)
        sm = cv2.resize(roi, (max(1, int(rw / cell)), max(1, int(rh / cell))), interpolation=cv2.INTER_AREA)
        fx = cv2.resize(sm, (rw, rh), interpolation=cv2.INTER_NEAREST)
    else:
        sigma = max(14.0, 1.0 * min(bw, bh))
        d = max(1, int(sigma // 3))
        sm = cv2.resize(roi, (max(2, rw // d), max(2, rh // d)), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), sigma / d)
        sm = cv2.GaussianBlur(sm, (0, 0), sigma / d)
        fx = cv2.resize(sm, (rw, rh), interpolation=cv2.INTER_LINEAR)
    # máscara: rectángulo agrandado en f por cada lado y suavizado (a la altura de la caja agrandada pesa ~1)
    mask = np.zeros((rh, rw), np.float32)
    ax0, ay0 = int(round(x0 - f - X0)), int(round(y0 - f - Y0))
    ax1, ay1 = int(round(x1 + f - X0)), int(round(y1 + f - Y0))
    # lo que se sale del recorte (borde del cuadro) se extiende para que no haya borde suave contra el límite
    ax0 = -5 if ax0 <= 0 else ax0
    ay0 = -5 if ay0 <= 0 else ay0
    ax1 = rw + 5 if ax1 >= rw else ax1
    ay1 = rh + 5 if ay1 >= rh else ay1
    cv2.rectangle(mask, (ax0, ay0), (ax1, ay1), 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), f / 2.0)[..., None]
    fr[Y0:Y1, X0:X1] = (roi * (1 - mask) + fx * mask).astype(np.uint8)
    return fr


# ── comandos ────────────────────────────────────────────────────────────────
def opts(a, start):
    o = {"modo": "blur", "margen": 0.25, "desde": None, "hasta": None, "caja": None, "traza": None,
         "tiempos": None, "detalle": None}
    i = start
    while i < len(a):
        k = a[i]
        if k in ("--modo", "--margen", "--desde", "--hasta", "--caja", "--traza", "--tiempos", "--detalle"):
            i += 1
            if i >= len(a):
                fail(f"falta el valor de {k}")
            v = a[i]
            key = k[2:]
            o[key] = float(v) if key in ("margen", "desde", "hasta") else v
        else:
            fail(f"opción desconocida {k}\n{__doc__}")
        i += 1
    if o["modo"] not in ("blur", "pixel"):
        fail("--modo debe ser blur o pixel")
    return o


def cmd_rastrear(video, o):
    W, H, fps, _ = info(video)
    cajas = parse_cajas(o["caja"] or "", W, H)
    t0 = time.time()
    serie, perdidos = rastrear(video, cajas, W, H, fps)
    serie = suavizar(serie)
    traza = [[round(v, 1) for v in p] for p in serie]
    res = {"w": W, "h": H, "fps": fps, "traza": traza}
    if perdidos:
        res["perdido_desde"] = round(min(t for _, t in perdidos), 3)
        sys.stderr.write(f"aviso: el tracker perdió el objeto (desde {res['perdido_desde']:.1f} s); se mantuvo la última caja buena\n")
    sys.stderr.write(f"ocultar.py: {len(traza)} cuadros rastreados en {time.time() - t0:.1f} s\n")
    return res


def cmd_aplicar(src, dst, o):
    if not o["caja"] or not o["traza"]:
        fail("aplicar necesita --caja y --traza")
    W, H, fps, fps_txt = info(src)
    res = cmd_rastrear(src, o)
    with open(o["traza"], "w") as fh:
        json.dump(res, fh)
    traza = res["traza"]
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", fps_txt, "-i", "-",
           "-i", src, "-map", "0:v:0", "-map", "1:a:0?", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
           "-pix_fmt", "yuv420p", "-r", fps_txt, "-c:a", "copy", "-shortest", "-movflags", "+faststart", dst]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cap = cv2.VideoCapture(src)
    i = 0
    try:
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            t = i / fps
            if (o["desde"] is None or t >= o["desde"]) and (o["hasta"] is None or t <= o["hasta"]):
                fr = aplicar_cuadro(fr, traza[min(i, len(traza) - 1)], o["modo"], o["margen"])
            p.stdin.write(fr.tobytes())
            i += 1
        p.stdin.close()
    except BrokenPipeError:
        pass
    cap.release()
    if p.wait() != 0:
        fail("ffmpeg falló al escribir el clip")
    sys.stderr.write(f"ocultar.py: {i} cuadros escritos\n")


def tiempos_default(dur):
    return [round(dur * (k + 0.5) / 8, 2) for k in range(8)]


def cmd_ver(video, out, o):
    W, H, fps, _ = info(video)
    cap = cv2.VideoCapture(video)
    nfr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    dur = nfr / fps if nfr else 10.0
    ts = [float(v) for v in o["tiempos"].split(",") if v.strip()] if o["tiempos"] else tiempos_default(dur)
    traza = None
    if o["traza"]:
        with open(o["traza"]) as fh:
            traza = json.load(fh)["traza"]
    TW = 480
    sc = TW / W
    tiles, dets = [], []
    for t in ts:
        i = max(0, min(int(round(t * fps)), max(nfr - 1, 0)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, fr = cap.read()
        if not ok:
            fr = np.zeros((H, W, 3), np.uint8)
        big = fr.copy()
        caja = None
        if traza:
            caja = traza[min(i, len(traza) - 1)]
            cx, cy, w, h = caja
            cv2.rectangle(big, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), (0, 0, 255), max(2, W // 400))
        tile = cv2.resize(big, (TW, round(H * sc)), interpolation=cv2.INTER_AREA)
        # regla en píxeles del clip cada 100 px (marcas en los bordes con su número)
        step = 100 if W <= 1500 else 200
        for gx in range(0, W, step):
            X = int(gx * sc)
            cv2.line(tile, (X, 0), (X, 6), (0, 255, 255), 1)
            if gx:
                cv2.putText(tile, str(gx), (X + 1, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 255, 255), 1, cv2.LINE_AA)
        for gy in range(0, H, step):
            Y = int(gy * sc)
            cv2.line(tile, (0, Y), (6, Y), (0, 255, 255), 1)
            if gy:
                cv2.putText(tile, str(gy), (8, Y + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (0, 255, 255), 1, cv2.LINE_AA)
        cv2.rectangle(tile, (TW - 78, tile.shape[0] - 20), (TW, tile.shape[0]), (0, 0, 0), -1)
        cv2.putText(tile, f"t={t:g}s", (TW - 74, tile.shape[0] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        tiles.append(tile)
        if caja:
            dets.append((fr, caja, t))
    cap.release()
    cols = min(4, len(tiles))
    rows = [tiles[k:k + cols] for k in range(0, len(tiles), cols)]
    blank = np.zeros_like(tiles[0])
    img = np.vstack([np.hstack(r + [blank] * (cols - len(r))) for r in rows])
    cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if o["detalle"] and dets:
        crops = []
        for fr, (cx, cy, w, h), t in dets:
            half = max(w, h) * 1.1
            x0, y0 = int(max(0, cx - half)), int(max(0, cy - half * 0.7))
            x1, y1 = int(min(W, cx + half)), int(min(H, cy + half * 0.7))
            c = fr[y0:y1, x0:x1]
            if c.size == 0:
                continue
            c = cv2.resize(c, (480, max(1, round(480 * c.shape[0] / c.shape[1]))), interpolation=cv2.INTER_CUBIC)
            cv2.putText(c, f"t={t:g}s", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1, cv2.LINE_AA)
            crops.append(c)
        if crops:
            hmax = max(c.shape[0] for c in crops)
            crops = [cv2.copyMakeBorder(c, 0, hmax - c.shape[0], 0, 0, cv2.BORDER_CONSTANT) for c in crops]
            cols = min(4, len(crops))
            rows = [crops[k:k + cols] for k in range(0, len(crops), cols)]
            blank = np.zeros_like(crops[0])
            cv2.imwrite(o["detalle"], np.vstack([np.hstack(r + [blank] * (cols - len(r))) for r in rows]), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"{W}x{H} {fps:g}fps {dur:.2f}s")


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        fail(__doc__)
    if a[0] == "aplicar" and len(a) >= 3:
        cmd_aplicar(a[1], a[2], opts(a, 3))
    elif a[0] == "ver" and len(a) >= 3:
        cmd_ver(a[1], a[2], opts(a, 3))
    elif a[0] == "rastrear":
        o = opts(a, 2)
        res = cmd_rastrear(a[1], o)
        with open(o["traza"], "w") as fh:
            json.dump(res, fh)
    else:
        fail(__doc__)


if __name__ == "__main__":
    main()
