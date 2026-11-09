---
name: nova
description: Cria uma tarefa de design a partir de notas de reunião. Uso /nova <CHAVE-JIRA> <projeto> <título> e, em seguida, as notas ou o caminho do arquivo.
---
Argumentos: $ARGUMENTS

1. Extraia CHAVE, projeto (deve existir em projetos.yaml) e título.
2. `python scripts/estado.py nova <CHAVE> <projeto> <título>`
3. Salve as notas/transcrição da reunião em `tarefas/<CHAVE>/reuniao.md`
   (se vier um caminho de arquivo, copie o conteúdo).
4. Execute o procedimento da skill `rodar`.
