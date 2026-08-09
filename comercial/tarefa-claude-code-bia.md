# Tarefa para colar no Claude Code

Copie tudo abaixo da linha e cole numa sessão do Claude Code.

---

Preciso substituir o prompt de proposta de honorários da Bia no sistema
comercial. O escritório fechou uma nova estrutura de três níveis e o texto atual
não serve mais.

## O que fazer

**1. Anexe e clone o repositório**, se ele ainda não estiver na sessão:
`Silva-Pinto-Advocacia/silvapinto-comercial` (use `add_repo` e depois o clone
que ele indicar; dê timeout generoso, uns 10 minutos).

**2. Pegue o texto novo.** Ele está em outro repositório do escritório:
`Silva-Pinto-Advocacia/marketing`, branch `claude/estrategia-honorarios-un17h4`,
arquivo `comercial/bia-adendo-proposta.py`.

Nesse arquivo há duas coisas:
- a constante `ADENDO_PROPOSTA` — é o texto que vai para o código;
- a constante `VALOR_FAIXA_1_SEIS_FASES` — é texto de banco, **não vai para o
  código**. Ignore-a nesta tarefa; eu cadastro à mão pela tela.

**3. Faça a substituição** em `app/routes/sentinela_ops.py` do
`silvapinto-comercial`:

Substitua o bloco inteiro que começa em `ADENDO_PROPOSTA = """` (por volta da
linha 9534) e termina no `"""` de fechamento — aquele que vem logo depois da
linha `=== FIM DO MODO PROPOSTA ===`. Troque pelo `ADENDO_PROPOSTA` do arquivo
`bia-adendo-proposta.py`, exatamente como está, sem reescrever, sem resumir e
sem "melhorar" o texto.

## O que NÃO pode ser tocado

Nada mais no arquivo muda. Em especial, deixe intactos:

- `_pode_apresentar_valor()` — é o portão que segura o preço até as quatro
  etapas do checklist fecharem
- `ADENDO_ANTES_DA_PROPOSTA`
- `ADENDO_CHECKLIST_SEMPRE`
- `ADENDO_CONDUZIR`
- `CHECKLIST_VENDA`, `CHECKLIST_ETAPAS`, `CHECKLIST_CURTO`
- `_honorario_do_numero()`
- as duas chamadas `ADENDO_PROPOSTA.replace("{honorario}", ...)` por volta das
  linhas 10534 e 10538

## Verificações antes de publicar

1. `python3 -c "import ast; ast.parse(open('app/routes/sentinela_ops.py').read())"`
   tem de passar.
2. O texto novo precisa conter o marcador `{honorario}` exatamente uma vez — é
   ele que as duas chamadas `.replace()` procuram. Sem o marcador, a Bia perde o
   acesso aos valores e não fala preço nenhum.
3. Confira que `=== FIM DO MODO PROPOSTA ===` continua sendo a última linha do
   bloco, e que não sobrou nenhum pedaço do texto antigo depois dele — em
   especial as menções a "Lei Estadual 10.516", "três questões já anuladas" e
   "março de 2026", que eram de um concurso só e precisam sumir.
4. `grep -c 'ADENDO_PROPOSTA' app/routes/sentinela_ops.py` tem de continuar
   devolvendo 3.

## Como publicar

Use a skill `deploy-silvapinto`. Resumindo o fluxo dela: gere `base64 -w0` e
`sha256sum` do arquivo, monte o payload com a mensagem de commit, injete a
caixinha de deploy na página do app, e me avise — eu colo o `ADMIN_DEPLOY_TOKEN`
e clico em Deploy. Não tente subir por outro caminho e não me peça o token.

Mensagem de commit sugerida:
`Novo ADENDO_PROPOSTA: escada de tres niveis, ancoragem e escada de concessoes`

Depois do deploy, confirme que o Render ficou Live e que `GET /health` responde
`status: ok`.

## Contexto, caso ajude a entender o texto

O escritório passou a vender três níveis em vez de um preço só: Básico (uma fase
do concurso), Blindado (todas as fases) e Carreira (este concurso e o próximo
edital do mesmo cargo). Os três cobrem todas as instâncias. Não existe mais
honorário de êxito.

O prompt novo faz a Bia apresentar os três juntos, do mais caro para o mais
barato, depois de uma âncora que é a conta de contratar fase por fase, e fechar
recomendando o do meio com o incremento mensal. Ele também proíbe expressamente
que ela faça qualquer conta: todo número que ela disser tem de estar escrito no
texto que vem do banco.
