"""Renderiza o vídeo do YouTube a partir de <pasta>/scenes.json (feito com cenas.py).

    python render_youtube.py <pasta> <fala_cortada.mp4> teste 2.0 11.8 45.5   → <pasta>/teste/t*.jpg
    python render_youtube.py <pasta> <fala_cortada.mp4> [workers=4]            → <pasta>/youtube.mp4 e youtube_web.mp4

Olhe os quadros de teste ANTES do render inteiro (≈ 20 min para 3 min 30 s com 4 workers). Os quadros
já gerados em <pasta>/out/ são reaproveitados: apague a pasta depois de mudar uma cena.
Som: a voz da fala (normalizada a −14 LUFS) + whoosh na entrada de cada imagem/documento/infográfico
e um "pop" baixo em cada elemento animado com "pop". Sem música (decisão: nenhuma trilha sem licença).
"""
import asyncio
import glob
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

AQUI = pathlib.Path(__file__).resolve().parent
ASSETS = "file://" + str((AQUI / ".." / ".." / "assets").resolve())
FPS = 24


def ffmpeg_bin():
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


FF = ffmpeg_bin()


def preparar_html(pasta):
    S = json.loads(open(pasta / "scenes.json").read().replace("__ASSETS__", ASSETS))
    html = (AQUI / "comp_youtube.html").read_text().replace("__ASSETS__", ASSETS)
    (pasta / "comp_youtube.built.html").write_text(html)
    icons = {p.stem: re.sub(r'\s(width|height)="24"', "", p.read_text()) for p in pathlib.Path(ASSETS[7:], "icons").glob("*.svg")}
    return S, icons


async def _abrir(br, pasta, S, icons):
    pg = await br.new_page(viewport={"width": 1920, "height": 1080})
    await pg.goto(f"file://{pasta}/comp_youtube.built.html")
    await pg.wait_for_timeout(500)
    await pg.evaluate("([d,i])=>init(d,i)", [S, icons])
    await pg.evaluate("document.fonts.ready")
    return pg


async def quadros(pasta, S, icons, teste=None, workers=4):
    from playwright.async_api import async_playwright
    exe = next(iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))[-1:]), None)
    async with async_playwright() as p:
        br = await p.chromium.launch(executable_path=exe, args=["--no-sandbox", "--allow-file-access-from-files"])
        if teste:
            (pasta / "teste").mkdir(exist_ok=True)
            pg = await _abrir(br, pasta, S, icons)
            for t in teste:
                await pg.evaluate("t=>render(t)", t)
                await pg.screenshot(path=str(pasta / "teste" / f"t{t:07.2f}.jpg"), type="jpeg", quality=85)
        else:
            out = pasta / "out"
            out.mkdir(exist_ok=True)
            n = int(round(S["total"] * FPS))
            todo = [f for f in range(n) if not (out / f"o{f + 1:05d}.jpg").exists()]

            async def worker(fr):
                pg = await _abrir(br, pasta, S, icons)
                for f in fr:
                    await pg.evaluate("t=>render(t)", f / FPS)
                    await pg.screenshot(path=str(out / f"o{f + 1:05d}.jpg"), type="jpeg", quality=93)
            await asyncio.gather(*[worker(todo[k::workers]) for k in range(workers)])
        await br.close()


def montar(pasta, S, fala):
    wh, pop = pasta / "whoosh.wav", pasta / "pop.wav"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anoisesrc=d=0.7:c=pink:a=0.6:r=48000", "-af",
                    "highpass=f=250,lowpass=f=2600,afade=t=in:d=0.28:curve=esin,afade=t=out:st=0.3:d=0.4,aformat=channel_layouts=stereo", str(wh)], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=880:d=0.09:r=48000", "-af",
                    "afade=t=out:st=0.02:d=0.07,aformat=channel_layouts=stereo", str(pop)], check=True)
    ev = []
    for c in S["scenes"]:
        if c["layout"] in "BDIO" and c["t0"] > 0:
            ev.append((c["t0"] - 0.12, wh, 0.22))
        ev += [(float(t), pop, 0.12) for t in re.findall(r'data-at="([\d.]+)" data-a="pop"', c.get("html", ""))]
    ev.sort(key=lambda e: e[0])
    fil = []
    for e in ev:
        if fil and e[1] == fil[-1][1] and e[0] - fil[-1][0] < 0.35:
            continue
        fil.append(e)
    T = S["total"]
    inp, fc = ["-i", str(fala)], ["[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
                                  f"apad=whole_dur={T}[v0]"]
    for k, (t, f, v) in enumerate(fil):
        inp += ["-i", str(f)]
        ms = int(max(0, t) * 1000)
        fc.append(f"[{k + 1}:a]volume={v},adelay={ms}|{ms}[e{k}]")
    fc.append("[v0]" + "".join(f"[e{k}]" for k in range(len(fil))) + f"amix=inputs={len(fil) + 1}:normalize=0:duration=first,atrim=0:{T}[a]")
    subprocess.run([FF, "-y", "-loglevel", "error", *inp, "-filter_complex", ";".join(fc), "-map", "[a]", "-ar", "48000", str(pasta / "audio.wav")], check=True)
    mestre, web = pasta / "youtube.mp4", pasta / "youtube_web.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(pasta / "out" / "o%05d.jpg"), "-i", str(pasta / "audio.wav"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", str(mestre)], check=True)
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", str(mestre), "-c:v", "libx264", "-preset", "slow", "-crf", "27", "-maxrate", "1.1M",
                    "-bufsize", "2.2M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(web)], check=True)
    print("pronto:", mestre, "e", web)


if __name__ == "__main__":
    pasta = pathlib.Path(sys.argv[1]).resolve()
    fala = pathlib.Path(sys.argv[2]).resolve()
    S, icons = preparar_html(pasta)
    if len(sys.argv) > 3 and sys.argv[3] == "teste":
        asyncio.run(quadros(pasta, S, icons, teste=[float(x) for x in sys.argv[4:]]))
    else:
        asyncio.run(quadros(pasta, S, icons, workers=int(sys.argv[3]) if len(sys.argv) > 3 else 4))
        montar(pasta, S, fala)
