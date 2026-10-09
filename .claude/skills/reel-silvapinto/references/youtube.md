# YouTube (16:9): o formato aprovado

Aprovado pelo dono em 04/10/2026 no vídeo "PMERJ 2014: por que candidatos estão sendo convocados 12 anos
depois?" ("Adorei. Ficou ótimo."). O código está em `scripts/youtube/` e o vídeo inteiro está escrito em
`examples/youtube_pmerj2014/cenas_pmerj2014.py`, que é o modelo para os próximos.

O YouTube **não é o reel deitado**. Quem assiste no YouTube está mais concentrado e boa parte assiste na
TV, então a tela precisa estar sempre cheia e conectada ao assunto, sem pressa de reel.

## O que o dono decidiu (não reabrir sem ele pedir)

| Decisão | Por quê |
|---|---|
| O apresentador aparece **sempre com o fundo original** da gravação (mármore do clone, ou o cenário real) | "Não aprovo o uso da minha imagem sem fundo." Recorte, fundo trocado e legenda atrás do corpo estão fora |
| **Sem laterais desfocadas** em volta do vídeo vertical | Foi a primeira versão e ele pediu para "preencher melhor a tela" |
| **Sem fundo ampliado artificialmente** | Testado em 04/10: o mármore estendido ficou bom, mas o ombro encosta na emenda em ~80% do tempo. A saída definitiva é gravar o clone em 16:9 |
| **Imagens conectadas ao assunto**: corporação, viaturas, prova, tribunal, Diário Oficial | Pedido dele: "vou falar da PM, preciso ter imagens da corporação, de policiais, de viaturas" |
| **Ícones, infográficos e elementos animados** no grafite e dourado da marca | Mesmo pedido |
| **Sem gravação, o apresentador é o clone do HeyGen em 16:9 com o fundo do escritório** (a foto que o dono enviou: madeira, logo SILVA PINTO, estante iluminada), de camisa ou de terno. Hoje: camisa branca `b1b7e81275e7441fa5a26ad2d45c5f32` (padrão; testado em 08/10, 1920x1080) e `e1c1cd6cf9094597ba7872984d134a0d` (mais perto) | "Para YouTube, padrão: os nossos avatares tendo como fundo aquela imagem do escritório" (08/10/2026). Os looks de terno no escritório (`fd4a1c47…`, `aa9ab1ac…`) têm "PRÁTICA JURÍDICA" e "RECURSO EM CONCURSOS" gravados na imagem, e o `32b6f70f…` tem a logo espelhada: fora até haver um look de terno sem texto |
| **No app do HeyGen, o YouTube sai DEITADO: Landscape (16:9) com o "Professional in white shirt"** | "Quando eu fizer YouTube, no formato horizontal" (09/10/2026). Configuração completa em SKILL.md, "Quando o dono gera o clone no app do HeyGen" |
| Os **cortes para a figura dele** vêm desse clone, já em 16:9, alternando com vídeos e imagens do assunto | "Quando tivermos os cortes para a minha figura, usar um daqueles avatares já no formato para YouTube que tem a imagem do meu escritório no fundo" (08/10) |
| O avatar **sentado olhando para o lado** (`f20c93aa…`, "Terno Bege -- 9", estante) é só para **formato de entrevista** | "Esse sentado sem olhar para a câmera é um formato de entrevista que eu quero fazer um uso específico" (08/10) |
| O estilo "jornal" (papel creme, serifa) feito no HyperFrames **foi recusado** | Comparado lado a lado em 04/10: "o atual está muito melhor que o novo". O mesmo vale para o Reels |

## Roteiro, título e capa

Seguem `atencao.md` (texto do Casil, 05/10/2026): dor → fato → lacuna nos primeiros 15 a 30 s, explicação por
capítulos, limite administrativo, ponte judicial ("o que acontece se você não estiver no TAC"), resumo
("Então guarda isso…") e **um CTA só** (no YouTube, "o contato está na descrição"; nada de somar inscreva-se,
manda e comenta). Fatos com a classificação de origem de `atencao.md` §6: o que é análise do escritório
aparece separado do que é fonte oficial (no vídeo de teste, a frase "uma solução coletiva para um grupo
específico" entrou num quadro "Na prática", fora da etiqueta "segundo o MPRJ"). Exemplo completo:
`examples/guia_atencao/pacote_psicotecnico_pmerj2014.md`.

## Os sete layouts (`scripts/youtube/cenas.py`)

| Layout | O que é | Quando |
|---|---|---|
| `W(t0, t1, html, lado="R"/"L"/"B")` | **Só com a fala deitada** (o clone do escritório, 1920x1080): ele em tela cheia, com o escritório inteiro, e o texto num lado escurecido (`R` sobre a estante, `L` sobre a parede, `B` terço inferior). Sem html, plano limpo | O plano principal do apresentador desde 09/10/2026 ("quero aquele visual em que estou no escritório, para youtube. ele preenche bem a tela widescreen"). Alterne com `P` e `X` para não ficar parado |
| `P(t0, t1, "L"/"R", html)` | Apresentador numa faixa de 860 px com o fundo original; do outro lado, texto sobre a foto do escritório desfocada (`img/escritorio.jpg`) | A maior parte do tempo em que ele explica; alterne o lado entre capítulos |
| `X(t0, t1, html)` | Close no rosto, tela cheia | Frase de ênfase ("Mas atenção", "Um detalhe importante"), até ~7 s: amplia a fonte 1,78x no vertical e 1,45x no deitado, e fica mais mole |
| `B(t0, t1, html, photo= / clips=)` | Imagem de apoio em tela cheia: foto com movimento lento ou trechos de vídeo | No começo de cada capítulo e quando a fala cita um lugar, órgão ou cena |
| `D(t0, t1, html, doc)` | Documento real com câmera e marca-texto nas frases ditas | Diário Oficial (com dados pessoais tarjados), comunicado oficial, decisão, edital |
| `I(t0, t1, html)` | Infográfico em tela cheia: comparação, critérios, fluxo, pessoas | Quando a fala explica uma regra ou um contraste |
| `final(t0)` | Cartão com o logo (entra sozinho no fim) | Sempre |

O ritmo que funcionou (medido no vídeo aprovado): 29 cenas em 3 min 23 s, de 3 a 14 s cada (mediana
6,4 s); rosto em tela **48%** do tempo; o maior trecho seguido sem ele, 25 s (documento + imagens). Elementos entram no tempo exato da
palavra (`a(t)`, com `t` tirado das palavras transcritas).

## Fluxo

1. **Fala.** Grave ou gere no HeyGen; corte pausas como no reel (`transcribe.py`, `build_timeline.py`,
   EDL do `timeline.json`) e exporte a fala cortada (`fala.mp4`). As palavras do `timeline.json` são o
   relógio das cenas.
2. **Quadros e rosto:** `python scripts/youtube/preparar.py fala <pasta> fala.mp4`. Vale para a fala vertical e
   para a deitada; o `rosto.json` guarda o tamanho do quadro e `P`, `X` e `W` se ajustam a ele (no deitado, a
   faixa do `P` é um recorte de 860 px centrado no rosto).
   **Fundo desfocado (`img/escritorio.jpg`)** para o lado do texto no `P`, o `I` e o cartão final: com o clone
   do escritório, `preparar.py fundo <pasta> fala.mp4` o monta de um quadro da fala sem o apresentador (a parede
   de madeira e a estante, emendadas). Apagar o apresentador e preencher o buraco (inpaint) deixa uma mancha que
   aparece mesmo desfocada (testado em 09/10/2026).
3. **Imagens:** `python scripts/youtube/busca_commons.py lista "<termo>" ...` e `baixa <pasta>/img "File:..."`;
   vídeo de apoio com `preparar.py apoio <pasta> <nome> <video> <início> <duração> [crop=...]`.
   Também entram: `escritorio.jpg` (projeto do escritório, só desfocado), brasão do órgão, página do
   Diário Oficial tarjada (da pauta automática), print do comunicado oficial.
4. **Cenas:** copie `examples/youtube_pmerj2014/cenas_pmerj2014.py`, troque as cenas, rode na pasta.
5. **Teste:** `python scripts/youtube/render_youtube.py <pasta> fala.mp4 teste 6 52 130` e olhe os quadros.
6. **Render:** `python scripts/youtube/render_youtube.py <pasta> fala.mp4` → `youtube.mp4` (mestre) e
   `youtube_web.mp4`. Voz a −14 LUFS, whoosh nas entradas de imagem e um pop baixo nos destaques.

## Direitos de imagem (sempre)

- Só licença que permite uso com crédito: domínio público, CC0, CC BY. **Nada de SA, ND ou NC.**
  Foto de portal de notícia ou do Instagram de órgão: não (Lei 9.610/98).
- Crédito curto na tela enquanto a imagem aparece (`credit=`) e a lista completa na descrição.
- Atos oficiais (Diário Oficial, comunicado, decisão) não têm proteção autoral (art. 8º da Lei 9.610/98),
  mas dado pessoal sai tarjado.
- Evite rosto de pessoa em destaque, político, operação policial e caso criminal real. A frase dita e a
  imagem precisam combinar: na revisão de 04/10, a fachada do TJRJ embaixo de "segundo o Ministério
  Público" foi apontada como erro.
- Nenhuma cena realista gerada por IA (o YouTube exige rótulo e o dono não quer rótulo).

## Junto com o vídeo

- **Descrição:** capítulos com tempo (o YouTube exige o primeiro em 0:00 e pelo menos três), fontes,
  créditos de imagem e o WhatsApp com mensagem pronta (`wa.me/5521993996262?text=Vim%20do%20YouTube%20(<tema>)`)
  para saber de onde veio o contato.
- **Legenda .srt** completa, gerada das palavras (linhas de até 42 caracteres) com `scripts/youtube/legenda_srt.py`.
  Antes, compare a transcrição com o roteiro (difflib) e passe o que o reconhecimento errou em `--corrige`: na
  PCMG, "prescrição 5º Enaldo Decreto" era "quinquenal do". Vídeo em partes: uma entrada por parte, com o
  deslocamento da emenda. A tela só traz palavras-chave.
- **Capa:** briefing em 3 opções para o teste A/B do YouTube Studio, pelo método de `atencao.md` §11
  (emoção, metáfora visual, ambiente da carreira, rosto com o fundo original, 2 a 5 palavras que completam
  o título) e **sempre com o brasão do órgão** (decisão de 05/10/2026), sem parecer comunicação oficial.
- **Cartão final:** a logo oficial (`logo_lockup.png`), nunca o nome digitado (`final()` em `cenas.py`).
- **Cartão final** com 15 s se for usar a tela final do YouTube (os botões só entram nos últimos 5 a 20 s).
