# Configuracao inicial do design-ops (rode uma vez).
# Uso, dentro da pasta design-ops:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$falhou = $false

function Passo($texto) { Write-Host "`n== $texto" -ForegroundColor Cyan }
function Ok($texto) { Write-Host "   OK  $texto" -ForegroundColor Green }
function Falta($texto) { Write-Host "   FALTA  $texto" -ForegroundColor Yellow; $script:falhou = $true }

Passo "Verificando programas"
foreach ($p in @(
    @{ cmd = "git";    nome = "Git for Windows"; link = "https://git-scm.com/downloads/win" },
    @{ cmd = "python"; nome = "Python (marque 'Add python.exe to PATH')"; link = "https://www.python.org/downloads/" },
    @{ cmd = "node";   nome = "Node.js LTS"; link = "https://nodejs.org/" }
)) {
    if (Get-Command $p.cmd -ErrorAction SilentlyContinue) { Ok $p.nome } else { Falta "$($p.nome): instale em $($p.link)" }
}

if (Get-Command claude -ErrorAction SilentlyContinue) {
    Ok "Claude Code"
} else {
    Write-Host "   Instalando o Claude Code..." -ForegroundColor Yellow
    Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    Write-Host "   Instalado. Feche e abra o PowerShell e rode este setup de novo." -ForegroundColor Yellow
    exit 0
}

if ($falhou) {
    Write-Host "`nInstale o que falta, feche e abra o PowerShell e rode o setup de novo." -ForegroundColor Yellow
    exit 1
}

Passo "Clonando os repositorios listados em projetos.yaml"
$url = $null
foreach ($linha in Get-Content projetos.yaml -Encoding UTF8) {
    if ($linha -match '^\s*-\s*url:\s*"([^"]+)"') { $url = $Matches[1]; $branch = $null; $sparse = $null; continue }
    if ($url -and $linha -match '^\s*branch:\s*"([^"]+)"') { $branch = $Matches[1]; continue }
    if ($url -and $linha -match '^\s*sparse:\s*"([^"]+)"') { $sparse = $Matches[1]; continue }
    if ($url -and $linha -match '^\s*caminho_local:\s*"([^"]+)"') {
        $destino = Join-Path $PSScriptRoot $Matches[1]
        if ($url -match "ORG/REPO") {
            Falta "projetos.yaml ainda tem o link de exemplo (ORG/REPO). Preencha antes."
        } elseif (Test-Path $destino) {
            Ok "Ja existe: $destino"
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path $destino) | Out-Null
            $args_clone = @("clone")
            if ($branch) { $args_clone += @("--branch", $branch) }
            if ($sparse) { $args_clone += @("--depth", "1", "--filter=blob:none", "--sparse") }
            git @args_clone $url $destino
            if ($LASTEXITCODE -eq 0 -and $sparse) { git -C $destino sparse-checkout set --no-cone $sparse }
            if ($LASTEXITCODE -eq 0) { Ok "Clonado: $destino" } else { Falta "Nao consegui clonar $url (confira acesso ao repo)" }
        }
        $url = $null
    }
}

Passo "Preparando o Storybook da AZO Web"
$web = Join-Path $PSScriptRoot "..\azo-telemedicina-web"
$openapi = Join-Path $PSScriptRoot "..\azo-telemedicina-api\openapi.yaml"
if (-not (Test-Path $web)) {
    Falta "Repositorio web nao encontrado em $web"
} elseif (-not (Test-Path $openapi)) {
    Falta "openapi.yaml nao encontrado em $openapi (precisa de leitura em edgebr/AZO-Telemedicina-API)"
} else {
    Push-Location $web
    if (-not (Test-Path .env)) {
        $caminhoApi = (Resolve-Path $openapi).Path -replace '\\', '/'
        (Get-Content .env.example) -replace '^OPENAPI_FILE_PATH=.*', "OPENAPI_FILE_PATH=$caminhoApi" | Set-Content .env -Encoding UTF8
        Ok ".env criado"
    } else { Ok ".env ja existe" }
    if (-not (Test-Path node_modules)) {
        Write-Host "   Instalando dependencias (npm ci, pode levar alguns minutos)..."
        npm ci --ignore-scripts --no-audit --no-fund | Out-Null
        if ($LASTEXITCODE -eq 0) { Ok "npm ci" } else { Falta "npm ci falhou" }
    } else { Ok "Dependencias ja instaladas" }
    npx orval --config ./orval.config.ts | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "Cliente da API gerado (src/api/generated)" } else { Falta "orval falhou" }
    Pop-Location
}

Passo "Testando a maquina de estados"
python scripts\estado.py painel
if ($LASTEXITCODE -eq 0) { Ok "estado.py funcionando" } else { Falta "estado.py falhou" }

Passo "Versionando o design-ops"
if (-not (Test-Path .git)) {
    git init | Out-Null
    git add . | Out-Null
    git commit -m "setup design-ops" | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "Repositorio criado" } else { Falta "Commit falhou. Rode: git config --global user.name 'Seu Nome' e git config --global user.email 'voce@email.com'" }
} else { Ok "Ja versionado" }

if ($falhou) {
    Write-Host "`nQuase la. Resolva os itens FALTA acima e rode o setup de novo." -ForegroundColor Yellow
} else {
    Write-Host "`nTudo pronto. De dois cliques em iniciar.bat (ou rode .\iniciar.bat)." -ForegroundColor Green
    Write-Host "Na primeira sessao: confie na pasta, aprove os MCPs e rode /mcp para logar no Figma e no Atlassian." -ForegroundColor Green
}
