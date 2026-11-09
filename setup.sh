#!/usr/bin/env bash
# Configuração do design-ops em Linux/macOS ou numa sessão do Claude Code na nuvem.
# Uso, dentro da pasta design-ops:  bash setup.sh [--storybook]
#   --storybook  também instala as dependências (pnpm) e sobe o Storybook em segundo plano.
set -u
cd "$(dirname "$0")"
falhou=0
ok()    { printf '   OK  %s\n' "$1"; }
falta() { printf '   FALTA  %s\n' "$1"; falhou=1; }

echo "== Verificando programas"
for p in git python3 node; do command -v "$p" >/dev/null && ok "$p" || falta "$p"; done
command -v pnpm >/dev/null || { echo "   Instalando pnpm..."; npm install -g pnpm@9 >/dev/null 2>&1; }
command -v pnpm >/dev/null && ok "pnpm" || falta "pnpm (npm install -g pnpm@9)"

echo "== Clonando os repositórios listados em projetos.yaml"
url=""
while IFS= read -r linha; do
  if [[ $linha =~ ^[[:space:]]*-[[:space:]]*url:[[:space:]]*\"([^\"]+)\" ]]; then url="${BASH_REMATCH[1]}"; continue; fi
  if [[ -n $url && $linha =~ ^[[:space:]]*caminho_local:[[:space:]]*\"([^\"]+)\" ]]; then
    destino="${BASH_REMATCH[1]}"
    if [[ $url == *ORG/REPO* ]]; then falta "projetos.yaml ainda tem o link de exemplo"
    elif git -C "$destino" rev-parse HEAD >/dev/null 2>&1; then ok "Já existe: $destino"
    elif git clone --depth 1 "$url" "$destino"; then ok "Clonado: $destino"
    else falta "Não consegui clonar $url (confira o acesso ao repositório)"; fi
    url=""
  fi
done < projetos.yaml

echo "== Testando a máquina de estados"
python3 scripts/estado.py painel >/dev/null && ok "estado.py funcionando" || falta "estado.py falhou"

if [[ ${1:-} == "--storybook" ]]; then
  repo="../azo-telemedicina-web"
  echo "== Instalando dependências do $repo (pnpm install)"
  (cd "$repo" && pnpm install --frozen-lockfile >/tmp/pnpm-install.log 2>&1) && ok "pnpm install" || falta "pnpm install (veja /tmp/pnpm-install.log)"
  echo "== Subindo o Storybook em http://localhost:6006"
  (cd "$repo" && setsid nohup pnpm --filter @docs/storybook storybook --ci </dev/null >/tmp/storybook.log 2>&1 &)
  ok "Storybook iniciando (log em /tmp/storybook.log)"
fi

if [[ $falhou == 1 ]]; then echo; echo "Resolva os itens FALTA acima e rode de novo."; exit 1; fi
echo; echo "Tudo pronto. Painel: python3 scripts/dashboard.py --sem-navegador  (http://localhost:8787)"
