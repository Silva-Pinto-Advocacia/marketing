# Estilo misto (aprovado em 29/10/2026)

O Casil, depois de ver os dois reels de teste: "ao invés de dividir a tela, usar os b-rolls na própria tela,
alternando com o vídeo [...] Mas seria bacana ter de vez em quando a tela dividida. Tem como a gente
randomizar isso?" e, no fim, "Ótimo, gostei desse estilo". É uma opção ao lado do reel clássico
(`estilo.md`): use quando ele pedir "o estilo misto", "com b-roll", "alternando" ou "igual ao reel de teste".

Exemplo completo: `examples/misto_vsl/` (o reel de teste com trechos da VSL; o vídeo está na biblioteca,
"Reel de teste: b-roll alternado").

## O que aparece na tela

Cada trecho da fala ganha um de três layouts, sorteados (`scripts/misto/sorteio.py`):

| layout | o que é | quando pesa mais |
|---|---|---|
| **cheio** | ele em tela cheia, o texto do trecho na parte de baixo | gancho (sempre), tese |
| **broll** | imagem de apoio em tela cheia, ele só na voz, o texto por cima | prova, lista, primeira menção ao órgão |
| **dividida** | painel de cima com a imagem e o infográfico, ele num cartão embaixo | dado (números) |

Depois do último trecho vem a chamada (ele desfocado, "Toque em" e o botão) e o cartão final (logo, título,
nome e OAB, aviso do Provimento 205/2021).

**Regras do sorteio** (`REGRAS` em `sorteio.py`): o rosto dele aparece em pelo menos 55% do vídeo; no máximo 2
b-rolls seguidos e 6 s sem rosto; no máximo 2 blocos de tela dividida e 35% do tempo; nunca três "cheio"
seguidos; ao menos uma tela dividida. A **semente** fixa o resultado: o mesmo número dá o mesmo vídeo, outro número
dá outra mistura. Para fixar um trecho à mão: `plano='dividida'` (ou `'cheio'`, `'broll'`) no trecho.

Transições: corte seco; quando a tela dividida vem logo depois dele em tela cheia, a tela cheia some de cima
para baixo atrás de uma linha de luz dourada. Som: whoosh baixo nas entradas de b-roll e tela dividida e na
chamada, batida nos carimbos, voz a −14 LUFS.

Legenda: 1 a 3 palavras, cada uma aparecendo quando é dita, na altura do peito (1160 px) e, na tela dividida,
dentro do cartão (1590 px). Logo horizontal do escritório no alto, centralizado.

## Nada sobre o rosto (regra fixa)

O Casil, sobre o reel de teste: "não termos o texto tampando meu rosto no começo do vídeo" (a etiqueta
"ELIMINADO NO CONCURSO?" estava na testa dele). Agora:

- **Abertura com etiqueta**: ele desce na tela até o alto da cabeça ficar a 360 px da borda; a faixa de cima
  vira o fundo do escritório com a etiqueta (`misto.etiqueta(...)`). Não dá para subir a etiqueta só: na
  filmagem deitada recortada em pé, a cabeça dele já encosta no topo.
- **Legenda nunca acima do queixo**: na tela cheia, ela desce sozinha para baixo da barba quando precisa.
- **Conferência automática**: `render.js <projeto> conferir` passa o vídeo inteiro a cada 0,1 s e acusa qualquer
  etiqueta, texto da cena, legenda, logo ou brasão em cima do rosto, e qualquer legenda encostada no texto da
  cena. `render.js tudo` confere antes e **não renderiza** se houver colisão (sai com código 4 e grava
  `colisoes.json`). O rosto vem do `rosto.json` (Haar, suavizado por trecho da fala). Conferir a prévia de olho
  mesmo assim: o rosto pode não ser achado com ele de perfil.

## Concurso específico: brasão, infográficos e imagens da instituição (regra fixa)

O Casil: "quando falarmos de um concurso específico, termos infográficos, brasão da instituição, e b-rolls
relacionados com aquela instituição e a carreira". Em todo reel misto sobre um concurso:

1. **Brasão do órgão** (o mesmo de sempre: PNG transparente do site oficial, receita em `pipeline.md`):
   - no canto superior direito o vídeo todo, menos na chamada e no cartão final: `escrever(..., brasao=...)`;
   - **grande, com brilho dourado, na primeira vez que ele diz o nome do órgão**: um trecho
     `tipo='instituicao'` com `html=brasao_destaque(T('PMERJ'), brasao, 'PMERJ', 'Polícia Militar do Rio de Janeiro')`,
     de preferência sobre imagens da própria corporação.
2. **Infográficos com os dados do concurso**, um por trecho que tenha número: `numero()` (vagas, nota de corte,
   candidatos: o número conta até o valor, com ponto de milhar), `barras()` (nota × corte, antes × depois),
   `item()` (lista falada: "situação 2 de 5"). Só dado conferido no edital ou no Diário Oficial; se ele citar um
   número que não está na pauta, pedir a fonte.
3. **B-roll da instituição e da carreira**, nessa ordem de preferência:
   - acervo do escritório (pasta do Drive do Redes) e o que o Casil gravar;
   - Wikimedia Commons da corporação (`scripts/youtube/busca_commons.py lista "Polícia Militar do Rio de Janeiro"`):
     tropa em formatura, viaturas, fachada, farda e boina em detalhe, sem rosto identificável;
   - genéricos da carreira (tabela abaixo) para completar.
   Nunca imagem de operação policial, caso criminal real, político ou rosto em destaque. A imagem combina com a
   frase dita.

## Catálogo de b-roll

Fontes: **Mixkit** (`https://assets.mixkit.co/videos/<id>/<id>-720.mp4`, licença livre para uso comercial, sem
crédito obrigatório, só 720p) e **Wikimedia Commons** (só PD, CC0 ou CC BY, com `credito` no `broll.json`, que
aparece pequeno no canto enquanto a imagem está na tela). Pexels e Pixabay recusam o download daqui (403).
720p esticado para a tela inteira fica macio; o `preparar.py` aplica um pouco de nitidez. Para a tela cheia, o
ideal é vídeo em pé ou 4K (pedir ao Redes quando houver gravação própria).

Já testados no reel de teste (Mixkit; `x`/`x9` em `examples/misto_vsl/broll.json`):

| tema | id | serve para |
|---|---|---|
| gabarito / folha de respostas | 20468 | resultado, nota, prova objetiva |
| estudante estudando | 8810 | candidato, preparação, "seus sonhos" |
| balança da justiça | 12315 | Judiciário, direito, ilegalidade |
| prova sendo feita | 20235 | questão anulada, gabarito |
| lupa em documento | 46977 | nota recalculada, conferência, edital |
| corrida / atletismo | 32813 | TAF |
| médico com paciente | 6562 | exame de saúde, inaptidão médica |
| juiz e martelo | 47687 | decisão, "o Judiciário só anula o ilegal" |

Por carreira (termos para buscar; conferir licença e rosto antes de usar):

| carreira | Commons (corporação) | genéricos |
|---|---|---|
| Polícia Militar | "Polícia Militar do <estado>", "formatura", "viatura" | farda, boina, continência de longe, corrida em grupo |
| Polícia Civil / PF / PRF | "Polícia Civil do <estado>", "Polícia Federal", "viatura PRF" | distintivo, documento, investigação em mesa |
| Bombeiros | "Corpo de Bombeiros Militar do <estado>" | caminhão, mangueira, treino de resgate |
| Tribunais (TJ, TRF, TRT) | "Tribunal de Justiça do <estado>", fachada | martelo, processo, biblioteca jurídica |
| Saúde / exames | — | consultório, exame médico, laudo |
| Psicotécnico | — | teste em papel, entrevista, relógio |
| Heteroidentificação | — | comissão em mesa, documento (sem rostos) |

## Comandos

Projeto = uma pasta com `fala.mov` (a fala já cortada, 1920x1080, 30 fps), `palavras.json` (como o
`reel.json` do exemplo: `total`, `trechos` com `nome` e `t0`, `palavras` com `w`, `s`, `e` no tempo da fala
cortada) e `broll.json` (nome → `arquivo`, `ini`, `dur`, `x`, `x9`, `credito`).

```bash
M=.claude/skills/reel-silvapinto/scripts/misto
python3 $M/preparar.py <projeto>                 # quadros, rosto.json, recortes do b-roll e folha_broll.jpg
cp .claude/skills/reel-silvapinto/examples/misto_vsl/cenas.py <projeto>/   # trocar os trechos
python3 <projeto>/cenas.py <projeto> 7           # sorteia (semente 7) e grava cenas.json; imprime o plano
node $M/render.js <projeto> teste 0.5 3 10 25    # prévias em <projeto>/teste/
node $M/render.js <projeto> conferir             # rosto livre?
node $M/render.js <projeto> tudo 4               # quadros (4 abas do Chromium); para se houver colisão
python3 $M/montar.py <projeto> /home/user/VIDEOS/<data>_<nome>/reel.mp4   # + reel_720p.mp4 para a biblioteca
```

Se o plano sorteado não agradar, outra semente. Se o Casil pedir "mais tela dividida" ou "menos b-roll",
mexer nos `PESOS` do tipo (e registrar aqui a decisão com a data).
