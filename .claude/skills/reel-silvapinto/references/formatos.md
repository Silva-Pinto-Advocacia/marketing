# Os formatos que mais engajam nos concorrentes

Análise quadro a quadro dos 12 reels de maior engajamento relativo (interações divididas pela mediana
do próprio perfil) entre os 97 reels baixados de 14 concorrentes, em setembro de 2026. Serve para
escolher o formato antes de gravar; o roteiro de cada bloco está em `roteiro.md`.

## A conclusão que muda a forma de trabalhar

**Os vídeos que mais engajam quase não têm edição.** Dos 12, dez têm de 0 a 2 transições por minuto,
todas cortes secos ou fusões simples; nenhum usa zoom de impacto, flash ou efeito de transição como
recurso principal. A exceção é a JS Advocacia (27 transições por minuto), que tem material real para
cortar: a cerimônia de posse dos clientes. Quem engaja ganha no **assunto** e no **título**, não na
montagem.

| Transições por minuto (mesmo detector) | Valor |
|---|---|
| Mediana dos 12 reels que mais engajaram | 0,9 |
| JS Advocacia, posse na Polícia Penal | 26,7 |
| Referência TJRJ (produção de terceiros para o escritório) | 11,1 |
| Nosso IASES editado | 8,1 |
| Nosso PMERJ v13 | 6,4 |

Consequência: a edição da skill continua sendo o nosso acabamento, mas não compensa pauta fraca. Pauta
forte com edição simples bate pauta fraca com edição caprichada.

## Os cinco formatos que apareceram no topo

| Formato | Exemplo (múltiplo da mediana do perfil) | Como é feito | Dá para fazermos? |
|---|---|---|---|
| **Emoção de conquista** | Safe & Lima: "Quando a vitória chega… mas o corpo ainda está cansado da guerra" e "Homem que voltou a estudar aos 35 passa em 2º lugar" (os dois maiores do estudo) | Cena de comemoração, sem fala, título fixo em cima, logo embaixo, faixas pretas | Sim, com vídeo **de cliente e com autorização por escrito**. Cena tirada da internet tem dono: não usar |
| **Caso real com nome** | Marcus Peterson: tela dividida, a candidata Flávia Medeiros em cima, ele comentando embaixo, título "Caso Flávia Medeiros: abre precedente?" (13 vezes) | Reação a um vídeo público da própria pessoa, com título fixo | Sim, com caso público ou cliente que autorize |
| **Humor sobre a vida do concurseiro** | Daniel Assunção: "Quando eu assumir cargo público vou continuar humilde. Eu no primeiro dia:" (36 vezes) e o "advogado gordinho dos concursos" na academia (52 vezes); JS: 6.894 interações, o maior do estudo | Meme: cabeçalho de texto branco em cima, trecho curto embaixo | Sim, 1 por mês, sem ridicularizar ninguém e sem trecho de TV de terceiros |
| **Prova na tela** | Daniel: "Trecho da sustentação oral" com o texto da sentença (25 vezes); reportagem de TV sobre cliente com TEA aprovado para juiz (9 vezes) | Título fixo, trecho da peça ou decisão em texto, advogado falando | Sim, é o que a skill já faz com `inserts`; falta o título fixo |
| **Chamada para a legenda** | Daniel: "CBMDF / Cotistas com nota suficiente para ampla concorrência devem liberar vagas de cotas / Explico na legenda 👇" (7 vezes) | Sigla grande, uma frase, bastidor sem fala, e o texto inteiro na legenda | **Sim, e é o formato que mais aproveita a nossa copy** |

## Os elementos gráficos que se repetem

1. **Título fixo no alto do começo ao fim** (9 dos 12): diz o assunto ou o grupo afetado ("Servidor de
   UF ou IF. Precisa trocar de lotação?"). Quem chega no meio do vídeo entende do que se trata. Na
   skill: campo `titulo` do `config.json`.
2. **Chamada escrita** ("Explico na legenda 👇", "Assista até o final"): manda a pessoa para a legenda
   ou segura até o fim. Na skill: `titulo.chamada`.
3. **Legenda falada** de uma linha em caixa simples (Daniel, JS): a nossa, palavra a palavra, é mais
   trabalhada; manter.
4. **Logo do escritório discreto** embaixo ou no canto: o nosso já está no canto.
5. **Tela dividida** para reagir a um caso: ainda não existe na skill; se entrar, é um campo novo.

## O que isso muda no nosso estilo

- **Manter** a edição rápida, a legenda palavra a palavra, a logo do órgão e o grafite e dourado. É o
  nosso acabamento e nenhum concorrente tem igual.
- **Acrescentar** o título fixo em todo reel, com o assunto ou o grupo afetado.
- **Reduzir** os textos grandes na abertura quando houver título fixo: um gancho basta, o resto da
  informação já está no título.
- **Não gastar edição onde a cena fala sozinha**: comemoração, depoimento e trecho de decisão pedem
  menos corte, não mais.
