---
name: rodar
description: Despacha todas as tarefas prontas e dúvidas de QA, respeitando o limite de 3 em paralelo. Use após /nova, /aprovar, /reprovar ou quando o painel mostrar tarefas prontas.
---
Argumentos opcionais (chaves específicas): $ARGUMENTS

1. `python scripts/estado.py fila`
2. Respeite o limite de 3 subagentes simultâneos (conte RODANDO_AGORA).
   Prioridade: linhas DUVIDA > linhas PRONTA (na ordem listada).
3. Para cada PRONTA escolhida: `python scripts/estado.py iniciar <CHAVE>` e chame o
   subagente indicado, em paralelo com os outros, passando chave, pasta da tarefa,
   bloco do projeto em projetos.yaml e o feedback.
   Para cada DUVIDA: chame o qa-responder (não use iniciar; dúvida não muda etapa).
4. Quando cada subagente terminar:
   - resposta começa com `AGUARDANDO_HUMANO` → `estado.py aguardar <CHAVE> "<motivo>"`
   - erro → `estado.py aguardar <CHAVE> "erro: <o que o humano precisa fazer>"`
   - sucesso → `estado.py concluir <CHAVE>`
5. Se a saída do concluir pedir red-team: rode o `red-team` e apresente o Resumo de
   Aprovação (formato no CLAUDE.md).
6. Se a tarefa entrou em QA: mova a issue no Jira para `jira.status_qa` do projeto.
7. Se abriu vaga no limite de 3 e ainda há fila, repita a partir do passo 1.
8. Termine com `estado.py painel` e a caixa de aprovação (todas as pendentes juntas).
