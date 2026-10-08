"""Cortes de contexto (B-roll) dentro da fala, antes da edição do reel.

Pedido do dono (08/10/2026): "alguns segundinhos de vídeos ... mostrando a atividade da corporação, os
policiais militares em serviço, fotos deles fardados, desde que não identifique as pessoas". O corte cobre o
quadro inteiro por 2 a 3 s enquanto a fala continua; a edição (legenda, título, infográficos, cartão final)
entra por cima depois, como em qualquer reel, porque ela trabalha sobre este vídeo.

Só material com licença livre (domínio público, CC0, CC BY) e o crédito curto aparece no rodapé enquanto o
corte está na tela (references/youtube.md, "Direitos de imagem"). Nunca no gancho nem na chamada: ali quem
aparece é o advogado.

    python broll.py fala.mp4 broll.json saida.mp4

broll.json: [{"t": 9.2, "dur": 2.6, "clip": "prontos/formatura.mp4", "credito": "Vídeo: Fulano / Governo do RJ · CC BY 2.0"}]
O clipe já vem em 9:16 (foto vira MP4 com Ken Burns antes); `t` é o segundo da fala em que o corte entra.
O áudio sai igual ao da fala, então a transcrição feita antes continua valendo.
"""
import json
import os
import subprocess
import sys
import tempfile

FONTES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
          "/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf"]
ENTRA = 0.15   # o corte entra e sai num fundido curto: corte seco sobre a fala parece erro de edição


def _medir(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                        "-of", "json", video], capture_output=True, text=True, check=True)
    s = json.loads(r.stdout)["streams"][0]
    n, d = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(n) / float(d or 1)


def _credito_png(texto, w, h, destino):
    """O crédito numa camada transparente do tamanho do quadro, pequeno, no rodapé, legível sobre qualquer imagem."""
    from PIL import Image, ImageDraw, ImageFont

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fonte = next((f for f in FONTES if os.path.exists(f)), None)
    tam = max(18, round(w * 0.024))
    f = ImageFont.truetype(fonte, tam) if fonte else ImageFont.load_default()
    x, y = round(w * 0.04), round(h * 0.958)
    caixa = d.textbbox((x, y), texto, font=f)
    d.rounded_rectangle((caixa[0] - 10, caixa[1] - 6, caixa[2] + 10, caixa[3] + 6), radius=8, fill=(0, 0, 0, 120))
    d.text((x, y), texto, font=f, fill=(255, 255, 255, 215))
    im.save(destino)


def montar(fala, cortes, saida):
    w, h, fps = _medir(fala)
    cortes = sorted(cortes, key=lambda c: float(c["t"]))
    with tempfile.TemporaryDirectory() as tmp:
        args = ["ffmpeg", "-v", "error", "-y", "-i", fala]
        for c in cortes:
            args += ["-i", c["clip"]]
        for i, c in enumerate(cortes):
            png = os.path.join(tmp, f"credito_{i}.png")
            _credito_png(c.get("credito") or "", w, h, png)
            args += ["-loop", "1", "-i", png]
        n = len(cortes)
        filtros, base = [], "[0:v]"
        for i, c in enumerate(cortes):
            t, dur = float(c["t"]), float(c["dur"])
            fim = t + dur
            filtros.append(
                f"[{i + 1}:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps},"
                f"tpad=stop_mode=clone:stop_duration={dur},trim=0:{dur},setpts=PTS-STARTPTS+{t}/TB,format=yuva420p,"
                f"fade=t=in:st={t}:d={ENTRA}:alpha=1,fade=t=out:st={fim - ENTRA}:d={ENTRA}:alpha=1[b{i}]")
            filtros.append(f"{base}[b{i}]overlay=0:0:eof_action=pass:enable='between(t,{t},{fim})'[v{i}a]")
            filtros.append(f"[v{i}a][{n + i + 1}:v]overlay=0:0:shortest=0:enable='between(t,{t + ENTRA},{fim - ENTRA})'[v{i}]")
            base = f"[v{i}]"
        args += ["-filter_complex", ";".join(filtros), "-map", base, "-map", "0:a?", "-c:v", "libx264", "-preset", "medium",
                 "-crf", "16", "-pix_fmt", "yuv420p", "-c:a", "copy", "-t", _duracao(fala), "-movflags", "+faststart", saida]
        subprocess.run(args, check=True)
    return saida


def _duracao(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                       capture_output=True, text=True, check=True)
    return r.stdout.strip()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    base_json = os.path.dirname(os.path.abspath(sys.argv[2]))
    lista = json.load(open(sys.argv[2], encoding="utf-8"))
    for c in lista:  # caminho relativo ao broll.json
        if not os.path.isabs(c["clip"]):
            c["clip"] = os.path.join(base_json, c["clip"])
    print("pronto:", montar(sys.argv[1], lista, sys.argv[3]))
