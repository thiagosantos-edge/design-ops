---
name: aprovar
description: Aprova o gate atual de uma tarefa e já dispara a próxima etapa. Uso /aprovar <CHAVE> [nota].
---
Argumentos: $ARGUMENTS

1. `python scripts/estado.py aprovar <CHAVE> <nota>`
2. Se houver nota, trate-a como instrução adicional para o próximo subagente.
3. Execute o procedimento da skill `rodar` imediatamente (sem esperar confirmação).
