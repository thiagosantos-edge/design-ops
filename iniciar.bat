@echo off
REM Abre o painel visual, o Storybook da AZO Web e a sessao do Claude Code na pasta design-ops.
cd /d "%~dp0"
start "Painel design-ops" /min python scripts\dashboard.py
if exist "..\azo-telemedicina-web\node_modules" (
  start "Storybook AZO" /min cmd /c "cd /d ..\azo-telemedicina-web && npm run storybook"
)
claude
