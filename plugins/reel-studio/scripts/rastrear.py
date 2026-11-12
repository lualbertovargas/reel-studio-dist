"""
Rastreo de cara u objeto para el reencuadre (reel seguir --cara / --caja).

Uso:
  python rastrear.py <video> --cara [--fps 4]
  python rastrear.py <video> --caja "t0,x,y,w,h[;t0,x,y,w,h…]" [--fps 4]   (x,y = esquina superior izquierda de la caja)

Salida (stdout): {"fps":4,"puntos":[[t,cx,cy,w,h],...]} con fracciones 0..1 del cuadro fuente.
En --caja los puntos pueden llevar un sexto valor true cuando el tracker perdió el objeto
(también se agrega la lista "perdido_desde" con el primer instante perdido).
Hacia atrás de t0 (si t0 > 0) se repite la caja inicial: no se rastrea en reversa.
"""
import json
import math
import os
import statistics
import sys
import time

WORK_W = 640        # ancho de trabajo (reescalado) para ir rápido
MAX_SPEED = 0.45    # fracción del ancho por segundo
TRACK_FPS = 10      # el tracker avanza a esta frecuencia (los saltos pequeños lo mantienen estable)


def fail(msg, code=2):
    sys.stderr.write(msg + "\n")
    sys.exit(code)


try:
    import cv2
    import numpy as np  # noqa: F401
except ImportError:
    fail("falta OpenCV: node reel.cjs instalar")


def cascade(name):
    here = os.path.dirname(os.path.abspath(__file__))
    cands = []
    data = getattr(getattr(cv2, "data", None), "haarcascades", None)
    if data:
        cands.append(os.path.join(data, name))
    cands.append(os.path.join(here, "modelos", name))
    home = os.environ.get("REEL_STUDIO_HOME") or os.path.expanduser("~/ReelStudio")
    cands.append(os.path.join(home, "modelos", name))
    for c in cands:
        if os.path.isfile(c):
            cc = cv2.CascadeClassifier(c)
            if not cc.empty():
                return cc
    return None


def abrir(video):
    cap = cv2.VideoCapture(video)
    if not cap.isOpened():
        fail(f"no pude abrir el video: {video}")
    nfps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if nfps < 1 or nfps > 240:
        nfps = 30.0
    return cap, nfps


def escalar(fr):
    h, w = fr.shape[:2]
    if w > WORK_W:
        fr = cv2.resize(fr, (WORK_W, round(h * WORK_W / w)), interpolation=cv2.INTER_AREA)
    return fr


def frames(cap, nfps, paso_fps, t_ini=0.0):
    """Genera (t, frame_reescalado) cada 1/paso_fps s a partir de t_ini."""
    step = max(1, round(nfps / paso_fps))
    i = 0
    if t_ini > 0:
        i = int(round(t_ini * nfps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    while True:
        if (i - int(round(t_ini * nfps))) % step == 0:
            ok, fr = cap.read()
            if not ok:
                return
            yield i / nfps, escalar(fr)
        else:
            if not cap.grab():
                return
        i += 1


def suavizar(pts, fps):
    """No causal: mediana de ventana 5 + media móvil centrada de 7 muestras (sin EMA);
    en cx,cy el desplazamiento entre muestras se recorta a MAX_SPEED * dt."""
    if not pts:
        return pts
    out = [list(p) for p in pts]
    n = len(pts)
    for k in range(1, 5):
        col = [p[k] for p in pts]
        med = [statistics.median(col[max(0, i - 2): i + 3]) for i in range(n)]
        ma = [sum(med[max(0, i - 3): i + 4]) / len(med[max(0, i - 3): i + 4]) for i in range(n)]
        if k <= 2:
            cur = ma[0]
            res = [cur]
            for i in range(1, n):
                lim = MAX_SPEED * max(1e-6, pts[i][0] - pts[i - 1][0])
                cur += max(-lim, min(lim, ma[i] - ma[i - 1]))
                res.append(cur)
            ma = res
        for i, v in enumerate(ma):
            out[i][k] = v
    return out


def redondear(pts):
    r = []
    for p in pts:
        q = [round(p[0], 3)] + [round(min(1.0, max(0.0, v)), 4) for v in p[1:5]]
        if len(p) > 5 and p[5]:
            q.append(True)
        r.append(q)
    return r


def cara(video, fps):
    front = cascade("haarcascade_frontalface_default.xml")
    perfil = cascade("haarcascade_profileface.xml")
    if front is None:
        fail("no hay detector de caras (haarcascade_frontalface_default.xml): esta build de OpenCV no trae "
             "los modelos Haar. Copiá el XML a scripts/modelos/ o a $REEL_STUDIO_HOME/modelos/. "
             "Para seguir un objeto sin detector usá --caja.")
    cap, nfps = abrir(video)
    muestras = []
    for t, fr in frames(cap, nfps, fps):
        H, W = fr.shape[:2]
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        mn = (max(24, W // 24),) * 2
        mx = (int(W * 0.7), int(W * 0.7))
        det = list(front.detectMultiScale(g, 1.1, 5, minSize=mn, maxSize=mx))
        if len(det) == 0 and perfil is not None:
            det = list(perfil.detectMultiScale(g, 1.1, 5, minSize=mn, maxSize=mx))
            if len(det) == 0:  # perfil del otro lado
                det = [(W - x - w, y, w, h) for (x, y, w, h) in perfil.detectMultiScale(cv2.flip(g, 1), 1.1, 5, minSize=mn, maxSize=mx)]
        # detecciones como [cx, cy, w, h] en fracciones
        muestras.append((t, [[(x + w / 2) / W, (y + h / 2) / H, w / W, h / H] for (x, y, w, h) in det]))
    cap.release()
    # inicial validada: la detección de las 3 primeras muestras con vecinas (centros a < 0.1) en >= 2 de las 3
    ini = None
    primeras = muestras[:3]
    mejor = None
    for k, (_, ds) in enumerate(primeras):
        for d in ds:
            hits = sum(1 for j, (_, es) in enumerate(primeras)
                       if j == k or any(math.hypot(d[0] - e[0], d[1] - e[1]) < 0.1 for e in es))
            if hits >= 2 and (mejor is None or d[2] * d[3] > mejor[2] * mejor[3]):
                mejor = d
    if mejor is None and primeras and primeras[0][1]:
        mejor = max(primeras[0][1], key=lambda d: d[2] * d[3])
    ini = mejor
    pts = []
    prev = list(ini) if ini else None
    for t, ds in muestras:
        if ds:
            if prev is None:
                prev = max(ds, key=lambda d: d[2] * d[3])
            else:
                cand = ds
                if len(cand) > 1:
                    ok = [d for d in cand if 0.5 <= d[2] / prev[2] <= 2.0]
                    cand = ok or cand
                prev = min(cand, key=lambda d: math.hypot(d[0] - prev[0], d[1] - prev[1]))
        if prev is not None:
            pts.append([t] + list(prev))
    cap.release()
    if not pts:
        fail("no detecté ninguna cara en el video. Probá --caja t:x,y,w,h")
    # las muestras iniciales sin cara toman la primera detección (ya están rellenas hacia adelante)
    return pts


def caja(video, spec, fps):
    """spec: una o varias cajas 't0,x,y,w,h' separadas por ';'. El tracker se reinicia en cada caja
    y avanza hasta la siguiente. Antes de la primera caja se repite la inicial (no hay rastreo en reversa)."""
    try:
        cajas = sorted([[float(v) for v in c.split(",")] for c in spec.split(";") if c.strip()])
        assert cajas and all(len(c) == 5 and c[3] > 0 and c[4] > 0 for c in cajas)
    except (ValueError, AssertionError):
        fail('--caja espera "t0,x,y,w,h[;t0,x,y,w,h…]" (segundos y fracciones 0..1 del cuadro; w y h > 0)')
    cap, nfps = abrir(video)
    seq = list(frames(cap, nfps, TRACK_FPS))
    cap.release()
    if not seq:
        fail("el video no tiene fotogramas legibles")
    H, W = seq[0][1].shape[:2]
    make = getattr(cv2, "TrackerCSRT_create", None) or cv2.legacy.TrackerCSRT_create
    ks = [min(range(len(seq)), key=lambda i: abs(seq[i][0] - c[0])) for c in cajas]
    pts = []
    perdido_t = None
    for n, (c, k0) in enumerate(zip(cajas, ks)):
        k1 = ks[n + 1] if n + 1 < len(cajas) else len(seq)
        if k1 <= k0:
            continue
        _, x, y, w, h = c
        # x,y = esquina superior izquierda; los puntos salen como centro
        ini = [seq[k0][0], x + w / 2, y + h / 2, w, h]
        if n == 0:
            pts += [[seq[i][0]] + ini[1:] for i in range(k0)]
        bx = [x * W, y * H, w * W, h * H]
        if w < 0.10:  # CSRT pierde objetos chicos: caja agrandada 30 % alrededor del centro
            cx, cy = bx[0] + bx[2] / 2, bx[1] + bx[3] / 2
            bx = [max(0, cx - bx[2] * 0.65), max(0, cy - bx[3] * 0.65), bx[2] * 1.3, bx[3] * 1.3]
        tr = make()
        tr.init(seq[k0][1], tuple(int(round(v)) for v in bx))
        seg = [ini]
        perdido = False
        for i in range(k0 + 1, k1):
            t, fr = seq[i]
            ok, b = tr.update(fr)
            if ok and b[2] > 2 and b[3] > 2:
                seg.append([t, (b[0] + b[2] / 2) / W, (b[1] + b[3] / 2) / H, b[2] / W, b[3] / H])
                continue
            perdido = True
            tp = t
            if perdido_t is None or n == len(cajas) - 1:
                perdido_t = tp
            # se descarta la deriva de los últimos 1.5 s antes de perderse: se mantiene el último punto previo
            corte = tp - 1.5
            for j in range(1, len(seg)):  # deriva previa: salto brusco (> 0.2 en 0.5 s) en los últimos 4 s
                if seg[j][0] >= tp - 4 and j >= 5 and abs(seg[j][1] - seg[j - 5][1]) > 0.2:
                    corte = min(corte, seg[j - 5][0])
                    break
            keep = [p for p in seg if p[0] < corte] or [seg[0]]
            hold = keep[-1]
            seg = keep + [[p[0]] + hold[1:] for p in seg[len(keep):]]
            seg += [[seq[j][0]] + hold[1:] + [True] for j in range(i, k1)]
            break
        pts += seg
    return pts, perdido_t


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("--"):
        fail(__doc__)
    video = a[0]
    fps = 4.0
    modo = None
    spec = None
    i = 1
    while i < len(a):
        if a[i] == "--cara":
            modo = "cara"
        elif a[i] == "--caja":
            modo = "caja"
            i += 1
            spec = a[i] if i < len(a) else ""
        elif a[i] == "--fps":
            i += 1
            fps = float(a[i])
        else:
            fail(f"opción desconocida {a[i]}\n{__doc__}")
        i += 1
    if not modo:
        fail(__doc__)
    t_ini = time.time()
    perdido_t = None
    if modo == "cara":
        pts = cara(video, fps)
    else:
        pts, perdido_t = caja(video, spec, fps)
    pts = suavizar(pts, fps)
    for p in pts:  # el centro nunca llega al borde de la fuente
        p[1] = min(0.92, max(0.08, p[1]))
        p[2] = min(0.92, max(0.08, p[2]))
    # a la frecuencia de salida: la muestra más cercana a cada k/fps
    sal, k = [], 0
    while k / fps <= pts[-1][0] + 1e-6:
        sal.append(min(pts, key=lambda p: abs(p[0] - k / fps)))
        k += 1
    sal = [p for i, p in enumerate(sal) if i == 0 or p is not sal[i - 1]]
    res = {"fps": fps, "puntos": redondear(sal)}
    if perdido_t is not None:
        res["perdido_desde"] = round(perdido_t, 3)
    sys.stderr.write(f"rastrear.py: {len(sal)} puntos en {time.time() - t_ini:.1f} s\n")
    print(json.dumps(res))


if __name__ == "__main__":
    main()
