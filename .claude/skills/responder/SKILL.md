---
name: responder
description: Posta no Jira a resposta aprovada para uma dúvida do QA e aplica o ajuste. Uso /responder <CHAVE> <ID> [ajustes na resposta].
---
Argumentos: $ARGUMENTS

1. Leia a seção da dúvida <ID> em `tarefas/<CHAVE>/qa.md` e aplique os ajustes indicados.
2. Se for classificação C (mudança de escopo): NÃO responda como resolvido. Avise o
   humano que a tarefa precisa voltar ao gate3 e pare.
3. Se for B: aplique o ajuste no Figma (página `<CHAVE> · Alta`) e registre em alta.md.
4. Poste a resposta como comentário na issue <CHAVE> no Jira, com link do frame.
5. `python scripts/estado.py responder <CHAVE> <ID> <resumo de uma linha>`
