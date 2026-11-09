#!/usr/bin/env bash
# Configuração do design-ops em Linux/macOS ou numa sessão do Claude Code na nuvem.
# Uso, dentro da pasta design-ops:  bash setup.sh [--storybook]
#   --storybook  também instala as dependências, gera o cliente da API e sobe o Storybook.
set -u
cd "$(dirname "$0")"
falhou=0
ok()    { printf '   OK  %s\n' "$1"; }
falta() { printf '   FALTA  %s\n' "$1"; falhou=1; }

WEB="../azo-telemedicina-web"
API="../azo-telemedicina-api"
BRANCH="dev"

echo "== Verificando programas"
for p in git python3 node npm; do command -v "$p" >/dev/null && ok "$p" || falta "$p"; done

echo "== Repositório web ($BRANCH)"
if ! git -C "$WEB" rev-parse HEAD >/dev/null 2>&1; then
  git clone --depth 1 --branch "$BRANCH" https://github.com/edgebr/AZO-Telemedicina-Web.git "$WEB" || falta "clonar AZO-Telemedicina-Web"
fi
if git -C "$WEB" rev-parse HEAD >/dev/null 2>&1; then
  if [[ $(git -C "$WEB" branch --show-current) != "$BRANCH" ]]; then
    git -C "$WEB" fetch --depth 1 origin "$BRANCH:refs/remotes/origin/$BRANCH" && git -C "$WEB" checkout -B "$BRANCH" "origin/$BRANCH"
  fi
  ok "$WEB na branch $(git -C "$WEB" branch --show-current) ($(git -C "$WEB" rev-parse --short HEAD))"
fi

echo "== openapi.yaml da API ($BRANCH)"
if ! [[ -f $API/openapi.yaml ]]; then
  git clone --depth 1 --branch "$BRANCH" --filter=blob:none --sparse https://github.com/edgebr/AZO-Telemedicina-API.git "$API" \
    && git -C "$API" sparse-checkout set --no-cone /openapi.yaml
fi
[[ -f $API/openapi.yaml ]] && ok "$API/openapi.yaml" || falta "openapi.yaml (precisa de leitura em edgebr/AZO-Telemedicina-API)"

echo "== Testando a máquina de estados"
python3 scripts/estado.py painel >/dev/null && ok "estado.py funcionando" || falta "estado.py falhou"

if [[ ${1:-} == "--storybook" ]]; then
  echo "== Preparando o Storybook"
  if [[ ! -f $WEB/.env ]]; then
    sed "s#^OPENAPI_FILE_PATH=.*#OPENAPI_FILE_PATH=$(cd "$API" 2>/dev/null && pwd)/openapi.yaml#" "$WEB/.env.example" > "$WEB/.env"
  fi
  (cd "$WEB" && npm ci --ignore-scripts --no-audit --no-fund >/tmp/npm-install.log 2>&1) && ok "npm ci" || falta "npm ci (veja /tmp/npm-install.log)"
  (cd "$WEB" && npx orval --config ./orval.config.ts >/tmp/orval.log 2>&1) && ok "cliente da API gerado" || falta "orval (veja /tmp/orval.log)"
  (cd "$WEB" && setsid nohup npm run storybook -- --ci --no-open </dev/null >/tmp/storybook.log 2>&1 &)
  ok "Storybook iniciando em http://localhost:6006 (log em /tmp/storybook.log)"
fi

if [[ $falhou == 1 ]]; then echo; echo "Resolva os itens FALTA acima e rode de novo."; exit 1; fi
echo; echo "Tudo pronto. Painel: python3 scripts/dashboard.py --sem-navegador  (http://localhost:8787)"
