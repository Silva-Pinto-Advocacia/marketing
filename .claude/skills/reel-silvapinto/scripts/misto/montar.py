"""Estilo misto, passo 4: áudio (fala a -14 LUFS, whoosh nas trocas para b-roll/tela dividida e na chamada,
batida nos carimbos) e o MP4 final, mais a cópia de 720p para a biblioteca de vídeos.

    python3 montar.py <projeto> <saida.mp4>
"""
import json, os, re, subprocess, sys

P = os.path.abspath(sys.argv[1]); SAIDA = os.path.abspath(sys.argv[2])
S = json.load(open(f'{P}/cenas.json')); T = S['total']
ff = lambda *a: subprocess.run(['ffmpeg', '-y', '-v', 'error', *a], check=True)
html = json.dumps(S['scenes'])
stamps = [float(x) for x in re.findall(r'data-at=\\"([\d.]+)\\" data-a=\\"stamp\\"', html)]
cta = [s['t0'] for s in S['scenes'] if s['layout'] == 'cta'][0]
wh = ([S['sticker']['t1']] if S.get('sticker') else []) + [cta - 0.1] + \
     [s['t0'] - 0.12 for s in S['scenes'] if s['layout'] in ('broll', 'split') and s['t0'] > 0]
ff('-f', 'lavfi', '-i', 'anoisesrc=d=0.7:c=pink:a=0.6:r=48000', '-af',
   'highpass=f=250,lowpass=f=2600,afade=t=in:d=0.28:curve=esin,afade=t=out:st=0.3:d=0.4,aformat=channel_layouts=stereo', f'{P}/whoosh.wav')
ff('-f', 'lavfi', '-i', 'sine=f=140:d=0.12:r=48000', '-af', 'afade=t=out:st=0.02:d=0.1,aformat=channel_layouts=stereo', f'{P}/batida.wav')
inp = ['-i', f'{P}/fala.mov']
fc = [f'[0:a]aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,apad=whole_dur={T}[v0]']
ev = [(t, 'whoosh', 0.22) for t in wh] + [(t, 'batida', 0.5) for t in stamps]
for k, (t, f, v) in enumerate(ev):
    inp += ['-i', f'{P}/{f}.wav']; ms = int(max(t, 0) * 1000); fc.append(f'[{k + 1}:a]volume={v},adelay={ms}|{ms}[e{k}]')
fc.append('[v0]' + ''.join(f'[e{k}]' for k in range(len(ev))) + f'amix=inputs={len(ev) + 1}:normalize=0:duration=first,atrim=0:{T}[a]')
ff(*inp, '-filter_complex', ';'.join(fc), '-map', '[a]', '-ar', '48000', f'{P}/audio.wav')
os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
ff('-framerate', '30', '-i', f'{P}/out/o%05d.jpg', '-i', f'{P}/audio.wav', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18',
   '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
   '-vf', 'scale=out_color_matrix=bt709:out_range=tv', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', SAIDA)
p720 = re.sub(r'\.mp4$', '_720p.mp4', SAIDA)
ff('-i', SAIDA, '-vf', 'scale=720:1280:flags=lanczos', '-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-c:a', 'aac', '-b:a', '128k',
   '-movflags', '+faststart', p720)
print('ok', SAIDA, f'{os.path.getsize(SAIDA) / 1e6:.1f} MB;', p720, f'{os.path.getsize(p720) / 1e6:.1f} MB (biblioteca)')
