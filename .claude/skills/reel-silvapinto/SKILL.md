---
name: reel-silvapinto
description: Edita vídeos curtos verticais (reels, shorts, stories) do Dr. Casil / Silva Pinto Advocacia a partir de uma gravação dele falando para a câmera, no estilo aprovado pelo escritório - legendas palavra a palavra, cortes de pausa, jump cuts com troca de enquadramento, zoom-hits, textos cinéticos dourados, infográficos na base e encerramento com WhatsApp. Use SEMPRE que o usuário pedir para editar, cortar, montar, legendar, "dar um trato", deixar dinâmico ou publicar um vídeo, reel, short, story ou "esse vídeo" (link do Drive, Google Photos, YouTube ou arquivo), mesmo sem dizer a palavra "reel", e também quando pedir para analisar o estilo de um vídeo de referência ou ajustar um reel já feito. Use também quando ele pedir pauta, roteiro, gancho ou ideia de vídeo, ou perguntar o que gravar, como gravar ou como publicar um reel.
---

# Reels Silva Pinto

Skill que reproduz o estilo de edição desenvolvido com o Casil (13 versões do reel PMERJ, setembro de
2026) para qualquer vídeo novo em que ele fala para a câmera. O resultado é um MP4 1080x1920 a 24 fps
com o vídeo dele em tela cheia, sem painéis nem caixas, legendas dinâmicas, cortes e zooms medidos nos
vídeos de referência que ele gosta, textos grandes dourados nos momentos-chave, infográficos
sincronizados com a fala e encerramento com o WhatsApp do escritório.

Leia antes de começar:
- `references/estilo.md`: o estilo em si, com o que ele aprovou e, sobretudo, o que rejeitou. Não
  reintroduzir nada da lista de rejeitados (barras opacas, fundo azul, rodapé, corte a cada frase,
  zoom contínuo, abertura desfocada, emenda de cabeça e tronco).
- `references/pipeline.md`: comandos, estrutura do projeto e o esquema do `config.json`.
- `references/roteiro.md`: a pauta, a estrutura de 30 a 60 s, a gravação e a publicação, com os
  números da comparação com 14 concorrentes (setembro de 2026). É o guia do Casil para gravar; use
  para conferir a pauta antes de editar e para responder pedidos de roteiro.

## Regras de pauta (valem para toda edição)

Saíram da medição dos posts do escritório e dos concorrentes; o porquê está em `roteiro.md`.

- **Até 60 segundos.** Se a gravação passar disso, editar a versão pedida e oferecer também um corte
  de até 60 s (os reels curtos renderam mais em 5 de 7 perfis). Não cortar sem avisar: o PMERJ de
  93 s foi aprovado assim.
- **Gancho nos 3 primeiros segundos com número, órgão ou pessoa afetada.** Se a fala não abre assim,
  o primeiro texto grande dourado faz esse papel ("9 QUESTÕES / ILEGAIS"), tirado do que ele diz
  mais adiante.
- **Aviso de data não é pauta.** Se o vídeo só anuncia um prazo ou resultado ("amanhã sai…"), sugerir
  reescrever o gancho para o que o candidato perde ou pode recuperar (exemplos em `roteiro.md`); os
  posts assim tiveram zero interações.
- **Prova na tela.** Decisão, edital, gabarito ou trecho de sentença entram como `insert`. Se ele
  citar um documento que não veio junto, pedir o arquivo.
- **Chamada que pede comentário** ("comente o seu cargo") no `cta`, além do WhatsApp.
- **Entregar pronto para publicar**: o reel do IASES foi ao ar sem a edição. Na entrega, lembrar que
  é o `reel_web.mp4` que deve subir, com a primeira linha da legenda igual ao gancho.

## Fluxo

1. **Obter o vídeo.** Drive: `curl` em duas etapas (ver pipeline.md). Google Photos: seguir o link
   curto, pegar a URL `lh3.googleusercontent.com/pw/...` do HTML e baixar com o sufixo `=dv`.
   Conferir com ffprobe se é filmagem bruta (ideal) ou uma exportação já editada com legendas e
   brasão gravados (aí entram `delogo`, `crop`, `frame_replace`, ver pipeline.md).
   **Obter a logo do órgão do concurso** (ele quer sempre a logo da instituição que oferece as
   vagas: PMERJ, IASES, TJRJ...). Buscar no site oficial do órgão um PNG com fundo transparente;
   recortar para símbolo + sigla, e se a grafia for escura acrescentar um brilho branco suave atrás
   (receita em pipeline.md). Ela entra como `badge` (canto superior direito) e como `insert` na
   primeira vez que ele cita o órgão. Se não achar, pedir o arquivo antes de renderizar.
2. **Transcrever e extrair quadros** com `scripts/transcribe.py` e `scripts/extract_frames.py`.
   Olhar uma folha de contatos dos quadros: onde está o rosto, o que aparece embaixo (é onde ficam
   os infográficos), se há gestos.
3. **Roteirizar a edição** lendo a transcrição: escolher 3 ou 4 frases para texto grande (gancho da
   abertura em duas partes e os maiores momentos), um infográfico por trecho de argumento (números
   viram `counter` ou `sum`, passos viram `list`, prazos viram `timeline`, frases de efeito viram
   `text`, fechamento vira `cta`), e as palavras fortes que recebem zoom-hit. Escrever o `config.json`
   com âncoras por palavra, usando `examples/pmerj/config.json` como modelo. Filmagem bruta pode usar
   `"framings": [1.0, 1.2, 1.0, 1.4, ...]`; se o rosto já ocupa boa parte do quadro (selfie no
   carro, celular perto), ficar em 1.0/1.1/1.2 para não cair no "só a cabeça" que ele rejeitou.
4. **Montar e conferir prévias** com `build_timeline.py` e `render_reel.js ... preview`. Verificar:
   acentos inteiros nos textos dourados, halo da legenda colado no texto, infográfico sem cobrir o
   rosto, brasão pequeno, nada opaco.
5. **Render completo em segundo plano**, depois `assemble.py`. Extrair folha de contatos do MP4 e
   conferir de novo antes de entregar.
6. **Entregar** `reel_web.mp4` pelo chat, dizer o que ficou como paliativo e o que a filmagem
   resolveria, oferecer subir o master no Drive.

## Texto dos overlays

Português do Brasil, tom do escritório (ver `post-blog-silvapinto`): "pode ser possível", "em
muitos casos", nunca promessa de resultado. Títulos em caixa alta curtos (2 linhas de até 12
caracteres cada em Bebas 190 px; até 16 em `size: "small"`). Kickers em minúsculas, 2 a 5 palavras.
Dados fixos: WhatsApp `wa.me/5521993996262`, OAB/RJ 189.781, aviso do Provimento 205/2021 no
encerramento (já embutido em `comp_reel.html`).

## Quando o pedido é outro

- "Me dá uma pauta / um roteiro / o que eu gravo": responder com a estrutura de `roteiro.md`
  (gancho, quem é afetado, prova, o que fazer, chamada), com as falas prontas e o tempo de cada
  bloco, a partir da notícia ou do caso que ele trouxer.

- "Analisa o estilo desse vídeo": `scripts/analyze_ref.py` (ver pipeline.md) e atualizar
  `references/estilo.md` com os números medidos.
- "Muda só X no reel": editar o `config.json` do projeto, rodar `build_timeline.py` e renderizar só o
  intervalo afetado com `render_reel.js ... frames "t0,t1"`, depois `assemble.py`.
- Logo empilhada oficial em arquivo: substituir o bloco `.logo` em `comp_reel.html` por uma `<img>`.
