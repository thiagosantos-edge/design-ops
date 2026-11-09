@echo off
REM Abre o painel visual e a sessao do Claude Code na pasta design-ops.
cd /d "%~dp0"
start "Painel design-ops" /min python scripts\dashboard.py
claude
