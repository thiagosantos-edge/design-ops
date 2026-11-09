---
name: qa
description: Varre o Jira atrás de dúvidas do QA sobre telas entregues e prepara respostas. Uso /qa [projeto].
---
Argumentos: $ARGUMENTS

1. Para cada projeto em projetos.yaml (ou só o indicado), busque no Jira issues em
   `jira.status_qa` com comentários novos desde a última varredura, ou com a label
   `jira.label_duvida_qa`. A data da última varredura fica em `tarefas/.ultima-varredura-qa`.
2. Para cada pergunta encontrada sobre design: `python scripts/estado.py duvida <CHAVE> <texto>`.
   Se a tarefa não existir no design-ops, avise em vez de criar.
3. Rode o qa-responder para cada dúvida (até 3 em paralelo).
4. Apresente as respostas preparadas agrupadas, com a classificação A/B/C e o comando
   `/responder <CHAVE> <ID> [ajustes]`. NÃO poste nada.
5. Atualize `tarefas/.ultima-varredura-qa` com a data/hora atual.
