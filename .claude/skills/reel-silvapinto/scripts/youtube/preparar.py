"""Prepara a pasta de um vídeo do YouTube: quadros da fala, posição do rosto e trechos de apoio.

    python preparar.py fala <pasta> <fala_cortada.mp4>
        → <pasta>/fr/f00001.jpg… (24 fps, vertical 1080x1920) e <pasta>/rosto.json (cx, cy, fw por quadro)
    python preparar.py apoio <pasta> <nome> <video> <inicio_s> <duracao_s> [crop=w:h:x:y]
        → <pasta>/clips/<nome>/c0001.jpg… em 1920x1080, 24 fps (crop antes de escalar, para tirar
          tarja, intérprete de Libras ou logo de emissora do vídeo de terceiro)

A fala chega já cortada (pausas e erros fora): o mesmo corte do reel (assemble.py / EDL do
timeline.json) ou o vídeo do HeyGen inteiro. Os tempos das cenas são contados nessa fala.
"""
import json
import os
import shutil
import subprocess
import sys


def ffmpeg_bin():
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FF = ffmpeg_bin()


def fala(pasta, video):
    os.makedirs(f"{pasta}/fr", exist_ok=True)
    subprocess.run([FF, "-loglevel", "error", "-y", "-i", video, "-vf", "fps=24", "-q:v", "2", f"{pasta}/fr/f%05d.jpg"], check=True)
    import cv2
    import numpy as np
    fs = sorted(os.listdir(f"{pasta}/fr"))
    n = len(fs)
    cc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    pts = {}
    for i in range(0, n, 4):                      # um a cada 4 quadros, interpolado e suavizado
        im = cv2.imread(f"{pasta}/fr/{fs[i]}", 0)
        h, w = im.shape
        sm = cv2.resize(im, (w // 2, h // 2))
        f = cc.detectMultiScale(sm, 1.1, 5, minSize=(120, 120))
        if len(f):
            x, y, fw, fh = max(f, key=lambda r: r[2] * r[3])
            pts[i] = (2 * (x + fw / 2), 2 * (y + fh / 2), 2 * fw)
    ks = sorted(pts)
    arr = np.array([pts[k] for k in ks])
    k = np.ones(25) / 25
    sm = lambda v: np.convolve(np.pad(np.interp(range(n), ks, v), 12, mode="edge"), k, "valid")
    cx, cy, fw = sm(arr[:, 0]), sm(arr[:, 1]), sm(arr[:, 2])
    json.dump({"cx": cx.round(1).tolist(), "cy": cy.round(1).tolist(), "fw": fw.round(1).tolist()}, open(f"{pasta}/rosto.json", "w"))
    print(n, "quadros;", len(ks), "rostos detectados")


def apoio(pasta, nome, video, ini, dur, crop=None):
    os.makedirs(f"{pasta}/clips/{nome}", exist_ok=True)
    vf = (f"crop={crop}," if crop else "") + "scale=1920:1080:flags=lanczos,fps=24"
    subprocess.run([FF, "-loglevel", "error", "-y", "-ss", str(ini), "-t", str(dur), "-i", video, "-vf", vf, "-q:v", "3",
                    f"{pasta}/clips/{nome}/c%04d.jpg"], check=True)
    print(nome, len(os.listdir(f"{pasta}/clips/{nome}")), "quadros")


if __name__ == "__main__":
    if sys.argv[1] == "fala":
        fala(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "apoio":
        crop = next((x.split("=", 1)[1] for x in sys.argv[7:] if x.startswith("crop=")), None)
        apoio(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], crop)
