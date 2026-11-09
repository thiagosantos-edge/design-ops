# design-ops

Orquestrador do fluxo de design com Claude Code: da reunião ao QA, com gates
humanos, até 3 tarefas em paralelo, painel visual e resposta rápida a dúvidas do QA.

## Pastas (Windows)

```
C:\Users\thago\Downloads\design\
├── design-ops\     ← este repositório
└── repos\          ← clones dos repositórios dos projetos (criados pelo setup)
```

## Instalação (uma vez)

1. Instale Git for Windows, Python (marcando "Add python.exe to PATH") e Node.js LTS.
2. Extraia o zip em `C:\Users\thago\Downloads\design`.
3. Confira `projetos.yaml` e `.claude\settings.json` (links e caminhos dos repositórios).
4. No PowerShell:
   ```
   cd $env:USERPROFILE\Downloads\design\design-ops
   powershell -ExecutionPolicy Bypass -File .\setup.ps1
   ```
   O setup confere os programas, instala o Claude Code se faltar, clona os repositórios,
   testa a máquina de estados e versiona a pasta. Se ele pedir para reabrir o
   PowerShell, reabra e rode de novo.
5. Dê dois cliques em `iniciar.bat`. Abre o painel no navegador e a sessão do Claude.
6. Primeira sessão: confie na pasta, aprove os servidores MCP, rode `/mcp` e faça login
   no Figma e no Atlassian. Confira com `/agents` (9 agentes).

## Uso diário

Dois cliques em `iniciar.bat`. O painel abre em http://localhost:8787 e mostra:
o que espera você (com botão para copiar o comando), onde cada tarefa está na linha
de produção, e os arquivos e o histórico de cada tarefa ao clicar nela.

| Comando no Claude | O que faz |
|---|---|
| `/nova AZO-12 projeto-a Título` + notas | Cria a tarefa e já gera as US |
| `/painel` | Estado no terminal |
| `/aprovar AZO-12 [nota]` | Aprova o gate e já dispara a próxima etapa |
| `/reprovar AZO-12 o que mudar` | Volta uma etapa com feedback e reexecuta |
| `/rodar` | Despacha tudo que está pronto (máx. 3 em paralelo) |
| `/qa` | Busca dúvidas do QA no Jira e prepara respostas |
| `/responder AZO-12 1 [ajustes]` | Posta a resposta aprovada e aplica o ajuste |

O painel é só leitura de propósito: decisões passam pelo Claude, onde você lê o
resumo e o red team antes de aprovar.

Teste com usuário: depois de aplicar, salve `tarefas\<CHAVE>\teste\resultados.md`, rode
`python scripts\estado.py retomar <CHAVE>` e depois `/rodar`. Pular o teste exige
justificativa: `python scripts\estado.py pular <CHAVE> "motivo"`.

## Como as regras são garantidas

- O estado só muda pelo `scripts\estado.py`; editar o `estado.json` direto é bloqueado.
- O painel do terminal aparece ao abrir a sessão (hook SessionStart).
- Cada tarefa tem página própria no Figma e worktree própria para protótipo em código.

## Problemas comuns

- `python` abre a Microsoft Store: desligue os aliases em Configurações → Aplicativos →
  Configurações avançadas → Aliases de execução de aplicativo.
- Claude não acha o Git Bash: em `.claude\settings.json` adicione
  `"env": { "CLAUDE_CODE_GIT_BASH_PATH": "C:\\Program Files\\Git\\bin\\bash.exe" }`.
- `/nova` não aparece: mova cada `SKILL.md` de `.claude\skills\<nome>\` para `.claude\commands\<nome>.md`.
- Painel diz "Sem conexão": a janela minimizada do painel foi fechada; rode `iniciar.bat` de novo.
- Escrever no Figma falha: é permissão do assento (precisa de Full); o agente para e avisa.
- Linux/macOS: troque `python` por `python3` nas skills e no settings.json.

## Rodando no Claude Code na nuvem (claude.ai/code) ou Linux

O projeto **azo-web** em `projetos.yaml` usa a branch **dev** de `edgebr/AZO-Telemedicina-Web`
(a `main` está desatualizada), clonada em `../azo-telemedicina-web`. O cliente da API
(`src/api/generated`) não é versionado: ele é gerado com o orval a partir do `openapi.yaml` da
branch dev de `edgebr/AZO-Telemedicina-API` (clone parcial em `../azo-telemedicina-api`).

```bash
bash setup.sh --storybook
```

Confere os programas, clona os dois repositórios na dev, cria o `.env`, roda `npm ci`, gera o
cliente da API e sobe o Storybook em http://localhost:6006.
Painel: `python3 scripts/dashboard.py --sem-navegador` → http://localhost:8787.

Na nuvem, Jira (Atlassian) e Figma vêm dos conectores da conta do claude.ai, não do
`.mcp.json`. O contêiner é temporário: tarefas em `tarefas/` só persistem se forem commitadas.

Pendências em `projetos.yaml` (marcadas `PREENCHER`): link do Chromatic (o Storybook tem o
addon, mas o repositório não tem appId nem workflow) e a biblioteca do Figma, se for separada
do Gestão master. Confirme também `jira.status_qa` (o AZOT não tem status "QA"; está como "To Review").
