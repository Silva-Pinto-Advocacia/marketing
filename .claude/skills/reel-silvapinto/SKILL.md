---
name: reel-silvapinto
description: Edita vídeos curtos verticais (reels, shorts, stories) do Dr. Casil / Silva Pinto Advocacia a partir de uma gravação dele falando para a câmera, no estilo aprovado pelo escritório - legendas palavra a palavra, cortes de pausa, jump cuts com troca de enquadramento, zoom-hits, textos cinéticos dourados, infográficos na base e encerramento com WhatsApp. Use SEMPRE que o usuário pedir para editar, cortar, montar, legendar, "dar um trato", deixar dinâmico ou publicar um vídeo, reel, short, story ou "esse vídeo" (link do Drive, Google Photos, YouTube ou arquivo), mesmo sem dizer a palavra "reel", e também quando pedir para analisar o estilo de um vídeo de referência ou ajustar um reel já feito. Use também quando ele pedir pauta, roteiro, gancho ou ideia de vídeo, ou perguntar o que gravar, como gravar ou como publicar um reel.
---

# Reels Silva Pinto

Skill que reproduz o estilo de edição desenvolvido com o Casil (13 versões do reel PMERJ, setembro de
2026) para qualquer vídeo novo em que ele fala para a câmera. O resultado é um MP4 1080x1920 a 24 fps
(em pé, o padrão: Reels e Stories; com `"formato": "deitado"`, 1920x1080, ver `references/estilo.md`, seção 1)
com o vídeo dele em tela cheia, sem painéis nem caixas, legendas dinâmicas, cortes e zooms medidos nos
vídeos de referência que ele gosta, textos grandes dourados nos momentos-chave, infográficos
sincronizados com a fala e encerramento com o WhatsApp do escritório.

Leia antes de começar:
- `references/estilo.md`: o estilo em si, com o que ele aprovou e, sobretudo, o que rejeitou. Não
  reintroduzir nada da lista de rejeitados (barras opacas, fundo azul, rodapé, corte a cada frase,
  zoom contínuo, abertura desfocada, emenda de cabeça e tronco).
- `references/pipeline.md`: comandos, estrutura do projeto e o esquema do `config.json`.
- `references/formatos.md`: os formatos, cortes, transições e elementos gráficos dos reels que mais
  engajaram nos concorrentes. Ler antes de propor o formato de um vídeo novo.
- `references/youtube.md`: o formato do YouTube (16:9), aprovado em 04/10/2026. **Não é o reel deitado**: o
  apresentador com o fundo original em faixa ou close, alternando em cortes com imagens do assunto (licença livre,
  com crédito), documentos e infográficos. Código em `scripts/youtube/`, exemplo completo em
  `examples/youtube_pmerj2014/`. Use sempre que o pedido for vídeo para o YouTube.
- `references/atencao.md`: **o guia de pauta, gancho, título, capa, ponte judicial e chamada** (texto do
  Casil, aprovado em 05/10/2026). Vale sobre `roteiro.md` onde os dois divergirem. Ler antes de qualquer
  pauta, roteiro, gancho, título ou capa. Exemplo aplicado: `examples/guia_atencao/`.
- `references/roteiro.md`: a pauta, a estrutura de 30 a 60 s, a gravação e a publicação, com os
  números da comparação com 14 concorrentes (setembro de 2026). É o guia do Casil para gravar; use
  para conferir a pauta antes de editar e para responder pedidos de roteiro.

## Regras de pauta (valem para toda edição)

Saíram da medição dos posts do escritório e dos concorrentes; o porquê está em `roteiro.md`.

- **Sempre até 60 segundos, com o cartão final** (decisão de 05/10/2026: "corte para encaixar sempre os
  reels nos 60s"). O `build_timeline.py` aperta as pausas sozinho; se ainda passar, para com o código 3 e
  diz quanto tirar. Aí, liste em `remover` (config.json) a frase de explicação que sai, nunca o gancho, a
  ponte judicial nem a chamada, e avise o Casil do que foi cortado.
- **Gancho nos 3 primeiros segundos: a dor do candidato com o fato e a lacuna** ("Foi considerado inapto
  no psicotécnico? Antes de aceitar esse resultado, confira 3 pontos."). O candidato vem antes da
  instituição (`atencao.md`, §0 a §2). Se a fala não abre assim, o primeiro texto grande dourado faz esse
  papel, com a dor ou o número no título ("INAPTO?", "9 QUESTÕES / ILEGAIS").
- **Ponte judicial quando houver fundamento**: limite da via administrativa → a ilegalidade não some → o
  Judiciário pode controlar a legalidade → análise individual. Só com as frases aprovadas de `atencao.md`
  §5; nunca "só a Justiça resolve" nem promessa de resultado.
- **Aviso de data não é pauta.** Se o vídeo só anuncia um prazo ou resultado ("amanhã sai…"), sugerir
  reescrever o gancho para o que o candidato perde ou pode recuperar (exemplos em `roteiro.md`); os
  posts assim tiveram zero interações.
- **Decisão judicial: de quem é?** (08/10/2026, `atencao.md`, decisões 5 a 8) De cliente nosso, destaque muito grande para
  a vitória judicial do escritório, sem identificar o cliente. De terceiro, notícia com muita esperança para quem não
  ajuizou ("pode estar na mesma situação"), sem promessa. E **nunca** dizer que liminar ou decisão pode cair: tom
  sempre animador, que convence a contratar.
- **Sem gravação, o clone do HeyGen grava**, sempre de frente para a câmera. Reels: "Terno Bege" (`5938d6e63b6d487b842d3832a5bf5eed`,
  terno bege, mármore) é o padrão; também servem "Terno Bege -- 8" (camisa e gravata) e "-- 6" (blazer). YouTube: o
  fundo do escritório (`references/youtube.md`). O sentado olhando para o lado (`f20c93aa…`, "-- 9") é só para entrevista,
  e o "-- 7" tem legenda gravada no vídeo ("pode aderir ao TAC"): fora.
- **Cortes de contexto (08/10/2026).** De 2 a 4 cortes de 2 a 3 s com vídeo ou foto da corporação (tropa em formatura,
  policiais em serviço de longe, viaturas, farda e boina em detalhe), sem rosto identificável, nunca no gancho nem na
  chamada. Só licença PD, CC0 ou CC BY, com o crédito no rodapé (`references/youtube.md`, "Direitos de imagem").
  `scripts/broll.py` encaixa os cortes na fala ANTES da edição; a legenda e os infográficos vêm por cima.
- **Nome do concurso como o candidato fala** (08/10/2026): "PMERJ 2014", nunca "CFSd 2014". A sigla do curso só
  aparece no documento oficial, quando ele estiver na tela.
- **Prova na tela.** Decisão, edital, gabarito ou trecho de sentença entram como `insert`; a questão do
  caderno entra como cena `prova` em tela cheia (marca-texto, círculo, seta e carimbo na palavra dita, ver
  estilo.md §12). Se ele citar um documento que não veio junto, pedir o arquivo. Nunca questão inventada
  num vídeo publicado: a folha-modelo é só para teste.
- **Título fixo em todo reel** (`titulo` no `config.json`): o assunto ou o grupo afetado, visível do
  início ao encerramento. Com ele, um texto grande de gancho basta na abertura.
- **Copy primeiro.** Se ele mandar a legenda do post, o roteiro do vídeo sai dela (título com virada vira
  o `titulo`, os números viram textos e infográficos). Se o assunto for técnico demais para 60 s,
  propor o formato "Explico na legenda": vídeo de 15 a 30 s com `titulo.chamada` e a copy inteira na
  legenda. Ver `roteiro.md`, seção 0, e `formatos.md`.
- **Estilo sorteado por padrão.** A abertura (texto grande ou brasão central) e a legenda (dourada ou
  caixa dourada) são sorteadas a cada vídeo; o build imprime o que saiu. Se o Casil pedir uma variante
  ("abre com o brasão", "legenda com caixa"), fixar em `estilo` no `config.json` (ver `pipeline.md`). A
  faixa de decisão não é sorteada: entra sempre que o vídeo anuncia uma decisão.
- **Dois visuais: formal (padrão) e dinâmico** (`estilo.visual`, estilo.md §11): o dinâmico tem texto
  por trás da pessoa na abertura, legenda que pula com marca-texto, um plano por frase com chicote, adesivos,
  palavras que caem, clarões e efeitos sonoros. Usar quando o Casil pedir ("mais dinâmico", "menos formal")
  ou quando o Redes mandar; rodar o `recortar.py` antes do build.
- **Nada sobre o rosto.** O build acha o rosto e tira o título de cima da cabeça e a legenda de cima do
  queixo (imprime o que mudou). Conferir na prévia: a etiqueta "Explico na legenda" na testa foi
  reclamação do Casil (02/10/2026).
- **Logo grande no primeiro segundo** quando a abertura é com brasão: ele entra grande no centro da
  metade inferior e só depois voa para o canto.
- **A metade inferior sempre ocupada.** Os infográficos sincronizados com a fala são o diferencial do
  escritório (nenhum concorrente usa). Planejar uma cena para cada trecho de argumento, inclusive a
  `faixa` de decisão quando houver decisão, e não deixar a parte de baixo vazia por mais de 2 s fora da
  abertura, dos textos grandes e do encerramento (o build avisa).
- **Em pé por padrão.** Deitado só quando o Casil pedir (o teleprompter do Redes tem a opção): mesmos
  elementos, com o rosto no centro, a legenda embaixo e textos grandes, infográficos e o brasão da
  abertura no painel da direita.
- **Um CTA principal por vídeo, escolhido pelo objetivo** (`atencao.md` §8): alcance ("manda para quem fez a
  prova com você"), autoridade ("salva"), lead ("comenta PSICOTÉCNICO e eu te envio os 3 pontos por escrito",
  só com material que exista) ou tráfego pago. Nunca dois no mesmo fechamento. O cartão final com o WhatsApp
  fica sempre, como assinatura (decisão de 05/10/2026).
- **Logo do escritório é sempre a arte oficial** (`assets/brand/logo_lockup.png`: brasão SP + SILVA PINTO na
  letra da marca + ADVOCACIA), no canto e no cartão final. Nunca o nome digitado em outra fonte.
- **Brasão do órgão em tudo**: canto, abertura e capa (decisão de 05/10/2026), sem fazer a peça parecer
  comunicação oficial.
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

- "Me dá uma pauta / um roteiro / o que eu gravo": responder na ordem de `atencao.md` (dor → fato →
  lacuna → explicação → limite administrativo → ponte judicial → um CTA), com as falas prontas, o tempo
  de cada bloco (o Reels inteiro em até 60 s), o título, a sugestão de capa (emoção, metáfora, carreira,
  brasão) e o filtro editorial (§12) conferido. Modelo: `examples/guia_atencao/pacote_psicotecnico_pmerj2014.md`.

- "Analisa o estilo desse vídeo": `scripts/analyze_ref.py` (ver pipeline.md) e atualizar
  `references/estilo.md` com os números medidos.
- "Muda só X no reel": editar o `config.json` do projeto, rodar `build_timeline.py` e renderizar só o
  intervalo afetado com `render_reel.js ... frames "t0,t1"`, depois `assemble.py`.
- Logo empilhada oficial em arquivo: substituir o bloco `.logo` em `comp_reel.html` por uma `<img>`.
