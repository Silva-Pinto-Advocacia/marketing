# Estilo de edição dos reels Silva Pinto

Guia visual e de ritmo, consolidado ao longo de 13 versões do reel PMERJ (setembro de 2026) e calibrado
por medição dos dois vídeos de referência do Casil (TJRJ e PMERJ, editados por terceiros). Tudo aqui foi
aprovado explicitamente por ele; a seção "O que foi rejeitado" é tão importante quanto o resto.

## 1. Formato e base

- 1080x1920, 24 fps, H.264 CRF 18 (master) e CRF 24 (versão para o chat, abaixo de 30 MB).
- Deitado (`"formato": "deitado"`, a pedido): 1920x1080. A "metade inferior" deste guia vira o painel da direita
  (x de 1160 a 1860): textos grandes, infográficos, faixa e brasão da abertura ficam ali, sobre uma sombra lateral que
  só aparece com eles; a legenda fica embaixo, no centro, e o rosto no meio do quadro.
- O vídeo do Casil ocupa a tela inteira, sempre. Sem painéis, sem barras, sem rodapé, sem caixas opacas.
- Enquadramento aberto: cabeça, ombros e tronco. Ele rejeitou enquadramento fechado ("só a cabeça, metade
  do frame vazio"). Zoom de reenquadramento máximo 1,15x sobre a filmagem original.
- Leve correção de cor: `contrast(1.07) saturate(1.1) brightness(1.03)` e vinheta radial suave.
- Degradê de legibilidade no rodapé (grafite, 820 px de altura: transparente no topo, 0,5 a 32%, 0,8 a 62% e 0,9 na
  base; reforçado em 02/10/2026 porque o dourado sumia sobre o terno bege) é o único escurecimento permitido. Nunca azulado: ele pediu tom de cinza. Ele o aceitou porque os números dourados não se leem sobre a camiseta
  branca sem isso. Nada de retângulos.
- Desfoque progressivo dos 20% inferiores da imagem (sigma 20, pena de 110 px) lê como profundidade de campo
  e é onde os infográficos assentam. Usar mesmo em filmagem bruta: ajuda a legibilidade e ficou aprovado.

## 2. Marca

- Canto superior esquerdo: monograma SP (`assets/brand/logo_mono.png`, 92 px) com "SILVA PINTO" em
  Fraunces 300, 36 px, tracking 0,16 em, cor #EDE9DD, e "ADVOCACIA" em Manrope 600, 15 px, tracking
  0,42 em, dourado. Ele pediu a logo COM o nome do escritório. A versão empilhada oficial ainda não chegou
  como arquivo; se um dia chegar (PNG/SVG), substituir esse bloco por ela.
- Canto superior direito: logo ou brasão do órgão do concurso (PMERJ, IASES, TJRJ...), 200 px de largura
  (160-180 quando o rosto chega perto do canto), estático, não acompanha o zoom. Ele pediu "menor"
  quando estava com 435 px e pediu que a logo do órgão esteja SEMPRE presente (IASES, set/2026). A mesma
  imagem entra como insert de ~1,3 s sobre o vídeo desfocado na primeira menção ao órgão.
- Barra de progresso dourada de 6 px no topo.
- Abertura opcional com brasão central (`abertura_brasao`, out/2026): o brasão entra grande na metade
  inferior, com halo dourado suave, kicker e título em dourado e dois fios que se abrem; aos 2,4 s voa para o
  canto e vira a logo fixa do órgão. Diz o concurso no primeiro segundo sem tirar o rosto de cena. Em pé, o brasão é grande (380 px; 330 com título em duas
  linhas), centralizado na metade inferior, e a legenda some enquanto ele está lá (02/10/2026). Veio da
  análise do Pedro Auar (brasão grande com pílula azul e setas), refeita na nossa identidade. Abertura e
  legenda são sorteadas por padrão entre as variantes aprovadas (out/2026, pedido do Casil); ele fixa a
  que quiser.
- Encerramento: fundo do vídeo desfocado e escurecido, monograma, "FALE COM A GENTE PELO WHATSAPP." em
  Bebas Neue 190 px com "WhatsApp" em dourado, pílula verde #25D366 com o link, linha de marca em mono e o
  aviso do Provimento 205/2021 da OAB em 22 px. Dura ~3,6 s, com whoosh na entrada.

## 3. Paleta e tipografia

| token   | valor   | uso |
|---------|---------|-----|
| grafite | #17181B | tints, halos, degradê do rodapé, encerramento (era navy #0B1220; ele pediu cinza para casar com a identidade cream/grafite/dourado do escritório, set/2026) |
| gold    | #F0CF86 | palavra ativa da legenda, kickers, pílulas de checklist |
| gold2   | #DDB363 | base dos degradês |
| gold3   | #FFF0CC | topo dos degradês |
| white   | #FFFFFF | legendas, números pequenos |
| wa      | #25D366 | pílula do WhatsApp |

Degradê dourado das manchetes: `linear-gradient(180deg,#FFF3D6 0%,#F4D692 55%,#EBC776 100%)` com
`background-clip:text`. Ele achou o dourado anterior (#D9B778 → #B08A48) "muito escuro"; o atual foi aprovado.

Fontes (em `assets/fonts`, carregadas localmente): Bebas Neue (manchetes e números grandes), Manrope 800
(legendas), Manrope 600 (textos de apoio), JetBrains Mono (kickers em caixa alta com tracking 0,28 em),
Fraunces 300 (nome do escritório na logo).

Armadilhas de renderização que já custaram versões:
- `background-clip:text` não pinta acentos que saem da caixa do elemento. Dar `padding-top:.14em` (ou
  `.22em` nas palavras animadas) aos elementos dourados.
- `text-shadow` herdado de um contêiner é pintado POR CIMA do preenchimento em degradê quando o texto é
  transparente, escurecendo o dourado. Desligar `text-shadow` em todo `.goldtxt` e usar `filter:drop-shadow`.
- `background-clip:text` não funciona em um pai cujos filhos têm `transform`. Aplicar a classe nos spans
  animados, não no contêiner.

## 4. Legendas

- Palavra a palavra, grupos de 2 a 3 palavras (até 22 caracteres), quebrando em pontuação, nunca uma palavra
  curta sozinha. Palavra falada em dourado com leve escala 1,07; palavras já ditas em branco; por vir em
  branco a 55%.
- Manrope 800, 78 px, centralizadas no peito (topo em 1160 px), com sombra forte. Nunca sobre o rosto: o build acha o
  rosto e desce a legenda para baixo do queixo quando preciso (até 1200 px).
- Halo escuro em cápsula que ACOMPANHA a largura do texto (`radial-gradient` num `inline-block` com
  `padding:22px 54px`). Ele rejeitou o halo de largura fixa: "passa muito do texto, fica um espaço em branco".
- Cada grupo entra com um pop de escala 0,92 → 1 em 0,16 s.
- Ficam ocultas durante os textos grandes e o encerramento.
- Variante `legenda: "caixa"` (out/2026): caixa em degradê dourado atrás da palavra falada, deslizando de
  uma palavra para a outra em 0,14 s; a palavra fica em grafite e o resto segue as regras acima.

## 5. Infográficos (cena inferior, y 1440-1880, largura total)

**A metade inferior é o nosso diferencial.** Nenhum dos 14 concorrentes analisados usa infográfico
sincronizado com a fala; o Casil pediu (out/2026) que ela trabalhe o vídeo inteiro, como no modelo PMERJ.
Fora da abertura, dos textos grandes e do encerramento, sempre há uma cena embaixo; o `build_timeline.py`
avisa quando passa de 2 s vazia. Uma versão que concentrou os elementos no alto foi recusada: "está
faltando explorar a metade inferior".

Um por trecho de fala, sincronizado com a palavra exata (âncoras no config). Entram deslizando da direita
(120 px, 0,45 s) e saem pela esquerda. Tipos disponíveis em `comp_reel.html`:

- `counter`: kicker + número Bebas 240 px que conta de zero ao valor em 1 s + unidade + frase de apoio.
- `list`: até 3 itens com quadradinhos numerados que acendem em dourado, cada um na sua palavra (`stagger`).
- `timeline`: 4 nós numa linha que se preenche, rótulos em Manrope + mono.
- `sum`: parcelas em Bebas 100 px que aparecem uma a uma, "=" e resultado em 190 px contando.
- `text`: manchete Bebas dourada 122 px em até 2 linhas + frase de apoio 38 px. Ele pediu "mais destaque"
  para frases como "Direito subjetivo à nomeação"; foi assim que ficou.
- `cta`: manchete + frase + pílula verde do WhatsApp.
- `faixa`: a faixa de decisão, com cara de notícia mas na nossa identidade: caixa grafite, fio dourado
  vertical que se desenha, kicker mono ("DECISÃO FAVORÁVEL · IASES") e manchete Manrope 800 56 px entrando
  palavra a palavra. Usar no trecho em que ele anuncia a decisão. Não é a faixa branca com etiqueta azul do
  concorrente, que ele pediu para não copiar.

Kicker sempre presente: mono 24 px, caixa alta, com traço dourado à esquerda.

## 6. Textos grandes (antigas "cartelas")

Não existem mais cartelas com fundo. São textos cinéticos diretos sobre o vídeo, na faixa do peito
(y 1120-1760), com halo radial suave: kicker, título Bebas 150-190 px em degradê dourado entrando
palavra a palavra de baixo para cima com stagger de 0,07 s, varredura de luz dourada e flash de 0,14 s.
Entrada com zoom de 20% e desfoque de 16 px no vídeo em 0,3 s; saída com zoom de 10% e desfoque de 12 px.
Usar 3 ou 4 por vídeo: abertura (gancho em 2 partes) e os dois maiores momentos.

Rejeitado duas vezes, não voltar: fundo azul opaco, fundo do vídeo desfocado com tint azul,
cantoneiras e granulação.

## 7. Câmera (o coração do estilo, medido nos vídeos de referência)

Medição por detector facial a 15 fps nos vídeos TJRJ (48 s) e PMERJ (60 s):
- PMERJ tem 6 cortes em 60 s; planos de 6 a 15 s. TJRJ: planos de fala de 5 a 10 s.
- Três enquadramentos fixos: base, ~1,2x e 1,35-1,5x. Troca por corte seco. Volta ao base com frequência.
- Um zoom-hit sem corte: fecha até 1,8x e volta em 1,7 s, sobre uma palavra forte.
- Deriva lenta dentro dos planos fechados: 7 a 10% ao longo de 10 s.
- Desfoque com flash só na entrada de inserts e cartelas, nunca nos cortes de fala.
- Inserts de 0,5 a 1,5 s com imagem de apoio (prédio do tribunal, documento).

Como está implementado (`build_timeline.py` + `comp_reel.html`):
- Planos com mínimo de 6,5 s, fronteiras nos inícios de frase; toda emenda de pausa removida vira fronteira.
  Nenhum plano com menos de 3,5 s.
- Níveis 1,0 / 1,13 / 1,26 (menores que a referência porque a filmagem editada já vinha ampliada; com
  filmagem bruta pode subir para 1,0 / 1,2 / 1,4). Pivô do zoom em 50% 38% (rosto).
- Corte seco entre planos, com 2 quadros de desfoque leve nas emendas de pausa.
- Deriva senoidal de 6% nos planos fechados e 3,5% no base.
- Zoom-hits de 1,2x com 1,1 s nas palavras-chave do config (`hits`).
- Um insert do brasão sobre o vídeo desfocado e escurecido quando o órgão é citado.

Rejeitado: corte a cada frase com enquadramento aleatório (v4, "horrível"); zoom suave contínuo sem trocas
de plano (v6-v8, "não é o estilo"); transição de zoom pequena demais nos cortes.

## 8. Ritmo e áudio

- Pausas acima de 0,55 s são cortadas (0,14 s antes da fala, 0,22 s depois). Casil fala sem pausas; costuma
  remover só 3 s.
- Áudio original, loudness -15 LUFS, cortes com fade de 12 ms.
- Whoosh de ruído rosa (0,7 s, -9 dB) 0,25 s antes de cada texto grande, do insert e do encerramento.
- Sem trilha musical até segunda ordem.

## 9. Abertura

Os primeiros 5 a 6 s precisam mostrar o Casil nítido e em sincronia. Ele rejeitou abertura desfocada
("muito tempo sem ver o interlocutor, atrapalha a retenção") e rejeitou composições com emenda entre
cabeça e tronco de momentos diferentes ("distorce", mesmo alinhada quadro a quadro). Com filmagem bruta
o problema não existe. Com filmagem já editada que tenha cartela gravada sobre o tronco, a única saída
aceitável foi usar um trecho limpo da mesma tomada (`frame_replace`), assumindo a boca fora de sincronia.
Melhor ainda: pedir a regravação da primeira frase.

## 10. Texto e conformidade

Seguir o eixo comercial da skill `post-blog-silvapinto`: o recurso administrativo não é a solução, a via
judicial continua aberta, isso não se faz sozinho. Usar "pode ser possível", "em muitos casos". Nunca
prometer resultado. Aviso do Provimento 205/2021 no encerramento. Dados fixos: Dr. Casil da Silva Pinto,
OAB/RJ 189.781, WhatsApp wa.me/5521993996262, @silvapinto.adv.

## 11. Visual dinâmico (`estilo.visual: "dinamico"`, aprovado em 02/10/2026)

O Casil pediu algo menos formal ("me agrada muito, porém eu gostaria de tentar algo diferente") e aprovou o
teste no vídeo da Polícia Penal RS ("ficou muito bom"). É um segundo visual, escolhido, nunca sorteado; o formal
continua o padrão da skill. Mesmos dados (cenas, textos grandes, título), outra encenação:

- **Abertura com texto por trás da pessoa.** O assunto em letras gigantes douradas (Bebas, até 350 px, encolhe
  para caber), uma palavra de cada vez, nos primeiros 3 s, passando POR TRÁS da cabeça. O `recortar.py` recorta a
  pessoa do fundo (rembg) e a composição a põe por cima do texto. Sem o recorte, a abertura fica só com o selo.
- **Selo do brasão:** o brasão do órgão grande (430 px), solto, sobre um brilho dourado com raios girando, que
  salta com mola na metade inferior, com o kicker numa etiqueta grafite inclinada; a legenda some enquanto ele
  está na tela; some aos ~2,7 s e o brasão aparece no canto com mola. Era um disco branco de 300 px com o brasão
  de 210 px dentro: "a logo da instituição está muito pequena" (Casil, 02/10/2026; aprovado na v3 do CFSd 2014).
- **Documento com movimento** (v3 do CFSd 2014): a câmera para em cada trecho citado (`paradas`, moldura dourada
  numerada), etiquetas grandes pulam com a fala (`chamadas`) e o rosto dele fica numa bolha no canto, para a parte
  "em que aparece só o Diário Oficial" não ficar parada.
- **Texto letra a letra** (`letra`): cada letra é um span com o mesmo dourado; antes de 03/10/2026 as letras
  saíam transparentes e o texto por trás nunca aparecia.
- **Legenda que pula:** caixa alta, 94 px, entra com mola e um leve giro; cada palavra aparece quando é falada;
  as palavras-chave (números e palavras dos textos grandes, das cenas e do título, ou `palavras_chave`) ganham
  marca-texto dourado inclinado.
- **Um plano por frase (2,2 s no mínimo), com transição:** chicote lateral com borrão de movimento (na entrada de
  cada cena), corte seco com tremor de câmera e soco de zoom, alternados. Diferente do v4 recusado ("corte a cada
  frase com enquadramento aleatório"): lá o corte era seco e sem motivo; aqui cada troca tem movimento e som, e os
  enquadramentos seguem o rosto medido.
- **Adesivos:** os infográficos `text` e `cta` viram cartões brancos inclinados com contorno dourado e etiqueta
  grafite, que entram com mola e giro e saem encolhendo. No `counter`, o número ganha um círculo dourado
  desenhado à mão e uma explosão de raios.
- **Textos grandes caem:** cada palavra cai de cima (escala 2,6 → 1) com tremor.
- **Clarões de luz quente** nas trocas em chicote e na entrada das cenas; tremor nos zoom-hits.
- **Efeitos sonoros por evento:** estalo nas entradas, chicote nas transições, tique nos cortes secos, impacto
  grave no número e na última palavra que cai.
- **Varia a cada vídeo** ("varie os motion graphs sempre pra não ficar tudo igual", 02/10/2026). O build sorteia,
  com a semente da fala (o mesmo vídeo sai sempre igual):
  - marca-texto da legenda: caixa dourada, sublinhado desenhado ou a palavra em dourado;
  - entrada do texto por trás: subindo, em zoom com desfoque ou letra a letra;
  - adesivos: brancos, grafite ou dourados;
  - o número: círculo desenhado, sublinhado ou raios;
  - os textos grandes: caem, sobem com desfoque ou giram;
  - cada adesivo entra de um jeito (mola, queda, lateral ou carimbo), nunca igual ao anterior, com a inclinação
    alternando de lado; a sequência de transições é embaralhada, sem repetir a anterior.
  Para fixar algo, `dinamico_var` no config (ex. `{"tema": "grafite", "marca": "cor"}`).

## 12. Cenas de tela cheia: `prova` e `ranking` (valem nos dois visuais)

Do estudo do plugin edit-labs-ai (out/2026): "mostrar uma prova, apontar o detalhe, concluir". Para o escritório,
a prova é o documento.

- **`prova`:** a folha da questão (print REAL do caderno, `img`) entra girando em tela cheia sobre o vídeo
  desfocado, com um clarão; a câmera se aproxima; o marca-texto passa no trecho `destaque`; um círculo vermelho e
  uma seta se desenham em volta do `alvo` (a alternativa ou o trecho em discussão); o carimbo
  (`carimbo_texto`, padrão "PASSÍVEL DE ANULAÇÃO") cai com impacto e tremor; uma etiqueta (`etiqueta`, ex.
  "11 questões") salta no canto; um clarão branco devolve para o rosto. Cada ação na palavra dita. Dura 3 a 4,5 s.
  A legenda desce para 1580 px e o título some enquanto ela está na tela.
  **Nunca uma questão inventada num vídeo publicado.** A folha-modelo (`"simulacao": true`, marca d'água
  SIMULAÇÃO) é só para teste.
- **`documento`** (mesma cena, para decisão judicial, edital, gabarito): o dono anexa o arquivo no Redes com uma
  descrição ("decisão judicial favorável"). A câmera vai até o trecho (`alvo`), até ele ocupar a largura da tela;
  `tarjas` cobre de preto nomes, CPF, número de processo e o que mais identificar alguém, do primeiro ao último
  quadro; o carimbo tem a cor do tom (`carimbo_cor`: `verde` para decisão favorável, `vermelho` padrão para erro
  da banca, `dourado` neutro). Uma faixa escura embaixo mantém a legenda legível sobre a folha branca.
- **`ranking`:** adesivo branco com uma lista de candidatos sem nomes nem números; o "VOCÊ" dourado sobe da última
  posição para o topo na palavra `sobe` (ex. "classificação"), com uma seta verde desenhando. Sem número de
  posição: ele não foi dito.

