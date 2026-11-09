#!/usr/bin/env python3
"""Painel visual do design-ops. Só leitura: mostra o estado, não altera nada.

Uso: python scripts/dashboard.py   (abre http://localhost:8787 no navegador)
"""
import json
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estado  # noqa: E402

PORTA = 8787
HTML = Path(__file__).resolve().parent / "dashboard.html"
CHAVE_OK = re.compile(r"^[A-Za-z0-9_-]+$")
ARQ_OK = re.compile(r"^(teste/)?[A-Za-z0-9_.-]+\.(md|txt|json)$")


def artefatos(chave):
    pasta = estado.TAREFAS / chave
    saida = []
    for p in sorted(pasta.rglob("*")):
        rel = p.relative_to(pasta).as_posix()
        if p.is_file() and rel != "estado.json" and ARQ_OK.match(rel):
            saida.append(rel)
    return saida


def payload():
    tarefas = []
    for t in estado.todas():
        t = dict(t)
        t["artefatos"] = artefatos(t["chave"])
        t["proximo"] = estado.proximo_passo(t)
        tarefas.append(t)
    return {"etapas": estado.ETAPAS, "tarefas": tarefas, "limite": 3}


class Handler(BaseHTTPRequestHandler):
    def _enviar(self, codigo, corpo, tipo):
        dados = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            self._enviar(200, HTML.read_text(encoding="utf-8"), "text/html")
        elif url.path == "/api/estado":
            self._enviar(200, json.dumps(payload(), ensure_ascii=False), "application/json")
        elif url.path == "/api/arquivo":
            q = parse_qs(url.query)
            chave, arq = q.get("k", [""])[0], q.get("f", [""])[0]
            if not (CHAVE_OK.match(chave) and ARQ_OK.match(arq)):
                return self._enviar(400, "Arquivo inválido.", "text/plain")
            p = estado.TAREFAS / chave / arq
            if not p.is_file():
                return self._enviar(404, "Arquivo não encontrado.", "text/plain")
            self._enviar(200, p.read_text(encoding="utf-8", errors="replace"), "text/plain")
        else:
            self._enviar(404, "Não encontrado.", "text/plain")

    def log_message(self, *_):
        pass  # silencioso


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    url = f"http://localhost:{PORTA}"
    print(f"Painel rodando em {url} (Ctrl+C para parar)")
    if "--sem-navegador" not in sys.argv:
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
