# Pipeline técnico

Tudo roda local, sem crédito de serviço externo: ffmpeg (via `imageio-ffmpeg`), faster-whisper (CPU),
Chromium (Playwright) para renderizar a composição HTML quadro a quadro. Um vídeo de 95 s leva ~15 min.

## Preparação do ambiente (uma vez por sessão)

```bash
pip install -q imageio-ffmpeg faster-whisper pillow "opencv-python-headless==4.10.0.84"
npm i -q playwright@1.56.1 --no-audit --no-fund      # o Chromium já está em /opt/pw-browsers
```

`render_reel.js` usa `executablePath: /opt/pw-browsers/chromium-1194/chrome-linux/chrome`. Se a versão do
diretório mudar, ajustar. O módulo `playwright` é procurado no diretório atual (`cwd/node_modules`) e nos
módulos globais do Node; rodar o `npm i` na pasta de trabalho, não na skill.

Obter o vídeo:
- Google Drive: `curl` em duas etapas (`uc?export=download&id=...` e depois
  `drive.usercontent.google.com/download?...confirm=t`); o arquivo precisa estar compartilhado com a conta
  ou por link.
- Google Photos (`photos.app.goo.gl/...`): `curl -L` no link curto, extrair do HTML a primeira URL
  `https://lh3.googleusercontent.com/pw/<id>` e baixar `<id>=dv` (vídeo original). Celulares gravam em
  HEVC 1920x1080 com `displaymatrix` de -90°; o ffmpeg já gira ao extrair os quadros.

## Estrutura de um projeto

```
projeto/
  config.json        # ver abaixo
  fonte.mp4          # vídeo do Casil
  badge_xxx.png      # brasão do órgão (opcional)
  words.json, sents.json   # gerados por transcribe.py
  src_frames/        # gerados por extract_frames.py
  timeline.json      # gerado por build_timeline.py
  out_frames/        # gerados por render_reel.js
  reel.mp4, reel_web.mp4   # gerados por assemble.py
```

## Passos

```bash
SK=<caminho da skill>/scripts
python3 $SK/transcribe.py projeto            # words.json + sents.json (modelo medium, ~1 min por min de áudio)
python3 $SK/extract_frames.py projeto        # 24 fps, 1080x1920, limpeza e reenquadramento conforme config
python3 $SK/build_timeline.py projeto        # timeline.json (EDL, legendas, planos, cenas, hits)
node $SK/render_reel.js projeto/timeline.json preview "1.5,14,30,66,84"   # PNGs em projeto/preview
node $SK/render_reel.js projeto/timeline.json frames                       # todos os quadros (~8 min)
node $SK/render_reel.js projeto/timeline.json frames "27,31"               # só um intervalo, para retoques
python3 $SK/assemble.py projeto reel.mp4     # master CRF 18 + reel_web.mp4 CRF 24
```

Atenção: o `after` das âncoras é em segundos da linha do tempo de SAÍDA (depois dos cortes de pausa),
não do vídeo original. Se `build_timeline.py` reclamar de âncora não encontrada, baixar o `after`.

Sempre olhar as prévias antes do render completo: montar uma folha de contatos com PIL e conferir
enquadramento, legibilidade e posição dos infográficos. Depois do render, extrair uma folha de contatos
do MP4 (`-vf "fps=1/4.5,scale=216:384,tile=11x2"`) e conferir de novo. O render completo deve rodar em
segundo plano (`run_in_background`), porque passa dos 10 minutos de limite.

## config.json

Campos e significado. Âncoras de tempo aceitam número (segundos na linha do tempo de SAÍDA, já sem as
pausas) ou objeto `{"word": "anulação", "after": 24, "nth": 0, "offset": -0.1}` resolvido contra a
transcrição retimada, ou `{"src": 5.65}` para um instante do vídeo original.

| campo | uso |
|---|---|
| `video` | arquivo fonte |
| `crop`, `delogo`, `blur_patches`, `bottom_blur`, `sharpen`, `frame_replace` | limpeza e reenquadramento; ver abaixo |
| `badge`, `badge_width` | PNG da logo/brasão do órgão do concurso, canto superior direito, OBRIGATÓRIO (o Casil pediu sempre a logo da instituição); largura em px, padrão 200, usar 160-180 quando o rosto chega perto do canto |
| `brand` | `mono`, `name`, `sub`, `whatsapp`, `outroLine` |
| `intro_end` | instante em que os textos de abertura terminam |
| `cards` | textos grandes: `at`, `dur`, `kicker`, `title` (com `<br>`), `size` ("small" ou ""), `white`, `sub` |
| `scenes` | infográficos: `from`, `to` ("next", "outro" ou âncora), `type` e campos do tipo |
| `hits` | âncoras dos zoom-hits |
| `inserts` | `{at, img, dur}` |
| `outro` | `{at}`; o encerramento dura 3,6 s e pode cobrir a última frase falada |
| `tail` | segundos mantidos depois da última palavra (padrão 1,2; usar 3 a 4 quando o encerramento entra sobre o fim da fala: o último quadro congela e o áudio é preenchido) |
| `silence_gap`, `min_shot`, `framings` | ajustes finos do ritmo (padrões 0.55 s, 6.5 s, [1,1.13,1,1.26,...]) |
| `pivot`, `hit_scale`, `hit_dur` | centro do zoom em % da tela (padrão [50, 38]; subir para ~[50, 24] quando o rosto já ocupa o alto do quadro, senão o zoom corta a cabeça), escala e duração do zoom-hit (padrões 1.2 e 1.1 s) |

Campos por tipo de cena: `counter` (`prefix`, `value`, `unit`, `sub`), `list` (`items`, `stagger`),
`timeline` (`nodes` [{b,l}], `sub`), `sum` (`terms`, `value`, `unit`), `text` (`head`, `text`),
`cta` (`head`, `text`, `pill`). Todos aceitam `kicker`. As cenas nunca se sobrepõem a um texto grande:
`build_timeline.py` apara automaticamente.

Exemplos: `examples/pmerj/config.json` (vídeo já editado, com limpeza de elementos gravados) e
`examples/iases/config.json` (filmagem bruta, selfie no carro, o caso simples).

## Vídeo já editado (legendas, brasão ou cartela gravados)

Foi o caso do PMERJ. Os passos que funcionaram:

1. Medir as caixas dos elementos gravados com PIL/numpy (linhas com pixels claros para legendas; saturação
   laranja para o brasão). Verificar com um scan de quadros se a cabeça entra na caixa.
2. `delogo` interpola bem sobre parede lisa (brasão) e mal sobre roupa (legendas). Para o brasão, aplicar
   depois um `blur_patches` interno (sigma 14) que esconde a faixa da interpolação. Para as legendas,
   apagar por `delogo` e cobrir com o `bottom_blur`, que já faz parte do estilo.
3. Recortar o brasão original em PNG com alfa (máscara por saturação + fechamento morfológico) e recolocar
   menor via `badge`.
4. Reenquadrar com `crop` para tirar de quadro o que sobrar embaixo. 1,15x foi o teto aprovado.
5. Cartela gravada sobre o tronco na abertura: `frame_replace` com um trecho limpo da mesma tomada. Escolher
   o trecho comparando a região dos olhos com `cv2.matchTemplate` (o de 18,3 s deu score 0,90). Não tentar
   emendar cabeça de um momento com tronco de outro: rejeitado.

## Logo do órgão do concurso

Sempre presente. Procurar no site oficial (`curl` na home e listar `src=...png|svg`; costuma haver uma
versão "fundo transparente" na pasta de logomarca). Com PIL: recortar para símbolo + sigla (a linha longa
com o nome por extenso não se lê a 200 px), `thumbnail` para ~900 px, e se houver grafia escura,
acrescentar um brilho branco atrás (dilatar o alfa com `MaxFilter(9)`, `GaussianBlur(10)`, branco a 85%,
compor por baixo). Salvar como `badge_<orgao>.png` no projeto e usar em `badge` e no `insert` da primeira
menção. Exemplo pronto: `examples/iases/badge_iases.png`. Brasão gravado num vídeo já editado: recortar
com máscara por saturação (caso PMERJ).

## Analisar novos vídeos de referência

`analyze_ref.py <nome>` espera `an_<nome>/f%05d.jpg` a 15 fps e 360x640 e imprime: cortes, largura do
rosto ao longo do tempo (nível de zoom), quedas de nitidez (transições com desfoque) e picos de brilho
(flashes). Foi assim que os parâmetros de câmera do estilo foram extraídos. Repetir quando o Casil mandar
um novo exemplo que goste.

## Entrega

Enviar `reel_web.mp4` pelo chat (limite 30 MiB). O master fica no projeto para subir no Drive quando ele
indicar a pasta. Sempre dizer o que ficou como paliativo (boca fora de sincronia, marca residual na parede)
e o que a filmagem bruta resolveria.
