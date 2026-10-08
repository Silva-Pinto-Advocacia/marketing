# Pipeline técnico

Tudo roda local, sem crédito de serviço externo: ffmpeg (via `imageio-ffmpeg`), faster-whisper (CPU),
Chromium (Playwright) para renderizar a composição HTML quadro a quadro. Um vídeo de 95 s leva ~15 min.

## Preparação do ambiente (uma vez por sessão)

```bash
pip install -q imageio-ffmpeg faster-whisper pillow "opencv-python-headless==4.10.0.84"
pip install -q rembg onnxruntime                     # só para o visual dinâmico (texto por trás da pessoa)
npm i -q playwright@1.56.1 --no-audit --no-fund      # o Chromium já está em /opt/pw-browsers
```

`render_reel.js` usa o Chrome de `CHROMIUM_PATH`, quando definida, e senão
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`; sem nenhum dos dois, o que o Playwright baixou. Se a
versão do diretório mudar, ajustar. O botão "Editar com a identidade do escritório" do Redes roda esta skill
no GitHub Actions do motor-conteudo (cópia em `reel/skill` de lá, ver `reel/ORIGEM.md`): mudou aqui, copie para lá. O módulo `playwright` é procurado no diretório atual (`cwd/node_modules`) e nos
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
python3 $SK/extract_frames.py projeto        # 24 fps, 1080x1920 (1920x1080 deitado), limpeza e reenquadramento conforme config
python3 $SK/recortar.py projeto              # só no visual dinâmico: recorta a pessoa nos 3 s da abertura (~1 min; pip install rembg onnxruntime)
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
| `formato` | `"em_pe"` (padrão, 1080x1920, Reels e Stories) ou `"deitado"` (1920x1080). Deitado, a fonte já deve vir em 16:9 (o motor recorta o centro); `bottom_blur` em `{"y": 700, "h": 380}`. O que este guia chama de metade inferior vira o painel da direita |
| `crop`, `delogo`, `blur_patches`, `bottom_blur`, `sharpen`, `frame_replace` | limpeza e reenquadramento; ver abaixo |
| `remover` | trechos da fala que saem do reel para caber nos 60 s: `[[ini, fim], ...]` em segundos do vídeo original. As palavras dentro deles somem e o corte de pausa fecha o buraco; cenas que ficarem com menos de 0,4 s saem. Use frases inteiras de explicação, nunca o gancho, a ponte judicial ou a chamada |
| `limite_s` | duração máxima do reel com o cartão final, padrão 60 (decisão de 05/10/2026). Passou: o build aperta as pausas em dois níveis e, se não couber, sai com o código 3 dizendo quantos segundos tirar. Não mude sem o Casil pedir |
| `brand.lockup` | a logo oficial (padrão `assets/brand/logo_lockup.png`), usada no canto e no cartão final |
| `titulo` | título fixo no alto, do início ao encerramento: `{"texto": "IASES: candidato <b>volta ao concurso</b>", "chamada": "Explico na legenda ↓", "de": 0.6}` (ou só a string). `<b>` pinta de dourado; `chamada` é a etiqueta dourada embaixo (opcional); `de` é a âncora de entrada (padrão: fim dos textos de abertura). Some sozinho enquanto há texto grande na tela e no encerramento. Até ~40 caracteres em 2 linhas. Use seta "↓" e não emoji: o Chromium do render não tem fonte de emoji. **Posição automática**: o build acha o rosto (OpenCV, com o zoom máximo dos planos); se em 300 px o título cobriria a cabeça, ele sobe para a barra do alto, entre a logo do escritório e a do órgão, compacto, e a `chamada` sai se ainda não couber. `topo` (px) e `alinhar` (`esquerda` ou `barra`) fixam à mão |
| `badge`, `badge_width` | PNG da logo/brasão do órgão do concurso, canto superior direito, OBRIGATÓRIO (o Casil pediu sempre a logo da instituição); largura em px, padrão 200, usar 160-180 quando o rosto chega perto do canto |
| `estilo` | as variantes visuais, **sorteadas por padrão**: `{"abertura": "sorteio" \| "texto" \| "brasao", "legenda": "sorteio" \| "dourada" \| "caixa"}`. Omitido ou `"sorteio"`, o build sorteia e imprime o resultado (`estilo: abertura=brasao (sorteio), legenda=dourada (escolhido)`), que também fica em `timeline.json`. A semente sai da própria fala: o mesmo vídeo sai sempre igual ao renderizar de novo; `semente` (número) força outro sorteio. Quando o Casil pedir uma variante, fixe-a aqui. `abertura: brasao` sem `badge` volta para texto |
| `abertura_brasao` | textos e ajustes da abertura com brasão (quando ela sai, sorteada ou escolhida): o brasão entra grande no centro da metade inferior, com `kicker` e `titulo` em dourado embaixo, e aos `dur` segundos (padrão 2,4) voa para o canto, onde vira a logo fixa (`badge`). Sem este campo, usa o kicker e o título do texto grande de abertura, que ele substitui. Opcionais: `img` (padrão: o `badge`), `de`, `dur`, `largura` (em pé, 380; 330 com título em duas linhas, reduzida se o brasão for alto demais para a metade inferior; deitado, 220/180) e `y`. Em pé, a legenda some enquanto o brasão está no centro, como acontece com os textos grandes. O texto grande seguinte é empurrado para depois do pouso |
| `legenda` | campo antigo, equivale a `estilo.legenda` fixo |
| `estilo.visual` | `"formal"` (padrão) ou `"dinamico"` (estilo.md §11): texto por trás da pessoa e selo na abertura, legenda que pula com marca-texto, um plano por frase com chicote, corte seco e soco de zoom, adesivos, palavras que caem, clarões e efeitos sonoros. Só em pé. Rodar o `recortar.py` antes do build para ter o texto por trás |
| `abertura_atras` | dinâmico: as 1 ou 2 palavras gigantes da abertura (padrão: as duas primeiras do texto grande de abertura) |
| `dinamico_var` | dinâmico: fixa variações que o build sorteia por vídeo: `marca` (caixa, sublinhado, cor), `atras` (sobe, zoom, letra), `tema` (branco, grafite, dourado), `numero` (circulo, sublinhado, raios), `queda` (queda, sobe, giro) |
| `palavras_chave` | dinâmico: as palavras com marca-texto na legenda (padrão: números e palavras dos textos grandes, das cenas e do título) |
| `legenda_gratuidade` | `true` deixa a legenda escrever gratuidade. Padrão: "gratuito(a)", "de graça" e "sem custo" saem da legenda (Provimento 205/2021); o áudio continua como foi falado |
| (legenda) | também automática: se o queixo desce abaixo de ~1220 px, a legenda desce junto (até 1200 px, logo acima dos infográficos, que começam em 1440) |
| `max_vazio` | segundos que a metade inferior (deitado, o painel da direita) pode ficar vazia antes de o build avisar (padrão 2) |
| `brand` | `mono`, `name`, `sub`, `whatsapp`, `outroLine` |
| `intro_end` | instante em que os textos de abertura terminam |
| `cards` | textos grandes: `at`, `dur`, `kicker`, `title` (com `<br>`), `size` ("small" ou ""), `white`, `sub` |
| `scenes` | infográficos: `from`, `to` ("next", "outro" ou âncora), `type` e campos do tipo |
| `hits` | âncoras dos zoom-hits |
| `inserts` | `{at, img, dur}` |

Cortes de contexto em tela cheia (B-roll) não são campo do `config.json`: entram no vídeo da fala antes de tudo,
com `python scripts/broll.py fala.mp4 broll.json fala_com_cortes.mp4` (`broll.json`: `[{t, dur, clip, credito}]`, o
clipe já em 9:16). O áudio não muda, então a transcrição feita antes continua valendo.
| `outro` | `{at}`; nas edições aprovadas entra logo depois da última palavra (`{"word": <última>, "after": ..., "offset": 0.3}`), com `tail` 3 a 4; pode cobrir a última frase, mas ela some atrás do WhatsApp |
| `tail` | segundos mantidos depois da última palavra (padrão 1,2; usar 3 a 4 quando o encerramento entra sobre o fim da fala: o último quadro congela e o áudio é preenchido) |
| `silence_gap`, `min_shot`, `framings` | ajustes finos do ritmo (padrões 0.55 s, 6.5 s, [1,1.13,1,1.26,...]). Sem `framings`, o build mede o rosto: se ele ocupa mais de 32% da altura, usa [1, 1.12, 1, 1.22] e zoom-hit 1.12; acima de 42%, [1, 1.08, 1, 1.15] e 1.1 (os valores das edições manuais de out/2026; rosto grande com zoom forte vira "só a cabeça") |
| `transicao`, `entrada_zoom` | `"zoom"` troca o corte seco entre planos por um zoom rápido de 0,2 s com desfoque; `entrada_zoom` (ex.: 1.5) abre o vídeo perto e recua em 0,5 s. Do reel na frente da PMERJ que o Casil aprovou; o motor liga os dois por padrão |
| `pivot`, `hit_scale`, `hit_dur` | centro do zoom em % da tela (sem `pivot`, a altura do rosto medida; sem rosto, [50, 38]; subir para ~[50, 24] quando o rosto já ocupa o alto do quadro, senão o zoom corta a cabeça), escala e duração do zoom-hit (padrões 1.2 e 1.1 s) |

Campos por tipo de cena: `counter` (`prefix`, `value`, `unit`, `sub`), `list` (`items`, `stagger`),
`timeline` (`nodes` [{b,l}], `sub`), `sum` (`terms`, `value`, `unit`), `text` (`head`, `text`),
`cta` (`head`, `text`, `pill`), `prova` (tela cheia, ver estilo.md §12: `img` = print real da questão, `alvo` e
`destaque` = [x, y, largura, altura] em pixels do print, âncoras `marca` (marca-texto e etiqueta), `circulo` (círculo e
seta) e `carimbo`, `carimbo_texto`, `etiqueta` (HTML curto, ex. `"11<small>QUESTÕES</small>"`); sem `img` só com
`"simulacao": true`, para teste), `documento` (a mesma cena para decisão, edital, gabarito: `img`, `alvo`, `destaque`,
`tarjas` = lista de [x, y, largura, altura] cobertas de preto (dados pessoais), `carimbo_cor` = `verde`, `vermelho` ou
`dourado`; o motor preenche tudo a partir do anexo do Redes; com movimento, aprovado na v3 do CFSd 2014 em 04/10/2026: `paradas` = lista de `{at, alvo, etiqueta?}` em que a câmera para em cada trecho citado, com moldura dourada e número; `chamadas` = lista de `{at, texto, lado?: esq|dir}`, etiquetas grandes que pulam com a fala; `bolha: false` tira a bolha com o rosto dele no canto, que no dinâmico entra sozinha), `ranking` (`head`, `sobe` = âncora da subida do VOCÊ), `faixa` (`head`: a manchete da decisão, até ~60 caracteres; caixa grafite com fio
dourado que se desenha, kicker e manchete entrando palavra a palavra). Todos aceitam `kicker`. As cenas nunca se sobrepõem a um texto grande:
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
