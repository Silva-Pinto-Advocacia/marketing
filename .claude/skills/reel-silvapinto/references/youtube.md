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
| O estilo "jornal" (papel creme, serifa) feito no HyperFrames **foi recusado** | Comparado lado a lado em 04/10: "o atual está muito melhor que o novo". O mesmo vale para o Reels |

## Os seis layouts (`scripts/youtube/cenas.py`)

| Layout | O que é | Quando |
|---|---|---|
| `P(t0, t1, "L"/"R", html)` | Apresentador numa faixa de 860 px com o fundo original; do outro lado, texto sobre a foto do escritório desfocada (`img/escritorio.jpg`) | A maior parte do tempo em que ele explica; alterne o lado entre capítulos |
| `X(t0, t1, html)` | Close no rosto, tela cheia | Frase de ênfase ("Mas atenção", "Um detalhe importante"), até ~7 s: amplia a fonte 1,78x e fica mais mole |
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
2. **Quadros e rosto:** `python scripts/youtube/preparar.py fala <pasta> fala.mp4`.
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
- **Legenda .srt** completa, gerada das palavras (linhas de até 42 caracteres). A tela só traz palavras-chave.
- **Capa:** briefing em 3 opções para o teste A/B do YouTube Studio (rosto com o fundo original, 2 a 5
  palavras, brasão do órgão quando for PM ou bombeiro).
- **Cartão final** com 15 s se for usar a tela final do YouTube (os botões só entram nos últimos 5 a 20 s).
