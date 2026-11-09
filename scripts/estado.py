#!/usr/bin/env python
"""Máquina de estados das tarefas de design.

É a ÚNICA forma de alterar tarefas/<CHAVE>/estado.json (o settings.json
bloqueia edição direta). Isso garante que nenhum agente pule um gate.

Uso:
  estado.py nova <CHAVE> <projeto> <titulo...>
  estado.py painel
  estado.py fila
  estado.py iniciar <CHAVE>
  estado.py concluir <CHAVE>
  estado.py aguardar <CHAVE> <motivo...>
  estado.py retomar <CHAVE>
  estado.py aprovar <CHAVE> [nota...]
  estado.py reprovar <CHAVE> <nota...>
  estado.py pular <CHAVE> <justificativa...>      (só etapa "teste")
  estado.py duvida <CHAVE> <texto...>
  estado.py responder <CHAVE> <ID> <resumo...>
"""
import datetime
import json
import os
import sys
import time
from pathlib import Path

# Windows: garante acentos e setas na saída mesmo quando capturada pelo Claude
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = Path(__file__).resolve().parent.parent
TAREFAS = RAIZ / "tarefas"
TRAVA = TAREFAS / ".lock"

ETAPAS = [
    {"id": "us", "curto": "US", "nome": "Histórias de usuário", "agente": "analista-us"},
    {"id": "fluxo", "curto": "Fluxo", "nome": "Flowchart", "agente": "ux-fluxos"},
    {"id": "gate1", "curto": "Gate 1", "nome": "Aprovação: US + fluxo", "gate": True},
    {"id": "wireframe", "curto": "Wireframe", "nome": "Wireframe", "agente": "ux-wireframe"},
    {"id": "teste", "curto": "Teste", "nome": "Teste com usuário", "agente": "pesquisador-teste", "pulavel": True},
    {"id": "gate2", "curto": "Gate 2", "nome": "Aprovação: wireframe + teste", "gate": True},
    {"id": "alta", "curto": "Alta", "nome": "Alta fidelidade", "agente": "ui-alta"},
    {"id": "gate3", "curto": "Gate 3", "nome": "Aprovação: telas", "gate": True},
    {"id": "handoff", "curto": "Handoff", "nome": "Handoff + Jira", "agente": "handoff"},
    {"id": "prototipo", "curto": "Protótipo", "nome": "Protótipo navegável", "agente": "prototipo"},
    {"id": "qa", "curto": "QA", "nome": "Em QA", "final": True},
]
IDX = {e["id"]: i for i, e in enumerate(ETAPAS)}


def agora():
    return datetime.datetime.now().isoformat(timespec="minutes")


class Trava:
    """Trava portátil (Linux, macOS, Windows) para subagentes em paralelo."""

    def __enter__(self):
        TAREFAS.mkdir(exist_ok=True)
        for _ in range(100):
            try:
                self.fd = os.open(TRAVA, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                time.sleep(0.1)
        sys.exit("ERRO: estado travado. Se nada estiver rodando, apague tarefas/.lock")

    def __exit__(self, *_):
        os.close(self.fd)
        os.remove(TRAVA)


def caminho(chave):
    return TAREFAS / chave / "estado.json"


def ler(chave):
    p = caminho(chave)
    if not p.exists():
        sys.exit(f"ERRO: tarefa {chave} não existe. Use: estado.py nova")
    return json.loads(p.read_text(encoding="utf-8"))


def salvar(t, evento):
    t["historico"].append({"quando": agora(), "evento": evento})
    t["atualizado"] = agora()
    caminho(t["chave"]).write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8")


def etapa(t):
    return ETAPAS[IDX[t["etapa"]]]


def avancar(t):
    """Vai para a próxima etapa e define o status correto."""
    prox = ETAPAS[IDX[t["etapa"]] + 1]
    t["etapa"] = prox["id"]
    t["feedback"] = None
    if prox.get("gate"):
        t["status"] = "aguardando_aprovacao"
    elif prox.get("final"):
        t["status"] = "em_qa"
    else:
        t["status"] = "pronto"
    return prox


def exigir(cond, msg):
    if not cond:
        sys.exit(f"ERRO: {msg}")


def proximo_passo(t):
    e = etapa(t)
    s = t["status"]
    abertas = [d for d in t["duvidas"] if d["status"] == "aberta"]
    if abertas:
        return f"responder {len(abertas)} dúvida(s) de QA (qa-responder)"
    return {
        "pronto": f"rodar subagente {e.get('agente')}",
        "rodando": f"{e.get('agente')} trabalhando",
        "aguardando_aprovacao": "VOCÊ: /aprovar ou /reprovar",
        "aguardando_humano": f"VOCÊ: {t.get('motivo') or 'ação manual'}",
        "em_qa": "nada (com QA)",
    }.get(s, "?")


# ---------------- comandos ----------------

def cmd_nova(chave, projeto, *titulo):
    exigir(not caminho(chave).exists(), f"{chave} já existe")
    (TAREFAS / chave).mkdir(parents=True, exist_ok=True)
    t = {
        "chave": chave, "projeto": projeto, "titulo": " ".join(titulo),
        "etapa": "us", "status": "pronto", "feedback": None, "motivo": None,
        "duvidas": [], "historico": [], "criado": agora(),
    }
    salvar(t, "criada")
    print(f"OK {chave} criada. PRÓXIMO: rodar analista-us")


def todas():
    if not TAREFAS.exists():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(TAREFAS.glob("*/estado.json"))]


def cmd_painel():
    ts = todas()
    if not ts:
        print("Nenhuma tarefa. Use /nova.")
        return
    ordem = {"aguardando_aprovacao": 0, "aguardando_humano": 1, "pronto": 2, "rodando": 3, "em_qa": 4}
    ts.sort(key=lambda t: (not any(d["status"] == "aberta" for d in t["duvidas"]), ordem.get(t["status"], 9)))
    print(f"{'CHAVE':<12}{'PROJETO':<14}{'ETAPA':<30}{'STATUS':<22}PRÓXIMO")
    for t in ts:
        print(f"{t['chave']:<12}{t['projeto'][:13]:<14}{etapa(t)['nome'][:29]:<30}{t['status']:<22}{proximo_passo(t)}")
    rod = sum(t["status"] == "rodando" for t in ts)
    apr = sum(t["status"] == "aguardando_aprovacao" for t in ts)
    print(f"\nRodando: {rod} | Esperando sua aprovação: {apr}")


def cmd_fila():
    ts = todas()
    duv = [t for t in ts if any(d["status"] == "aberta" for d in t["duvidas"])]
    prontas = [t for t in ts if t["status"] == "pronto"]
    rod = sum(t["status"] == "rodando" for t in ts)
    print(f"RODANDO_AGORA={rod}")
    for t in duv:
        for d in t["duvidas"]:
            if d["status"] == "aberta":
                print(f"DUVIDA {t['chave']} id={d['id']} agente=qa-responder :: {d['texto'][:80]}")
    for t in sorted(prontas, key=lambda t: t["atualizado"]):
        fb = f" feedback={t['feedback']!r}" if t["feedback"] else ""
        print(f"PRONTA {t['chave']} etapa={t['etapa']} agente={etapa(t)['agente']}{fb}")


def cmd_iniciar(chave):
    with Trava():
        t = ler(chave)
        exigir(t["status"] == "pronto", f"{chave} não está pronta (status={t['status']})")
        t["status"] = "rodando"
        salvar(t, f"iniciou {t['etapa']}")
    print(f"OK {chave} rodando {t['etapa']}")


def cmd_concluir(chave):
    with Trava():
        t = ler(chave)
        exigir(t["status"] == "rodando", f"{chave} não está rodando (status={t['status']})")
        feita = t["etapa"]
        prox = avancar(t)
        salvar(t, f"concluiu {feita}")
    if prox.get("gate"):
        print(f"OK {chave} em {prox['id']}. PRÓXIMO: rodar red-team e apresentar Resumo de Aprovação")
    elif prox.get("final"):
        print(f"OK {chave} em QA. PRÓXIMO: mover issue no Jira para o status de QA")
    else:
        print(f"OK {chave} → {prox['id']}. PRÓXIMO: rodar {prox['agente']}")


def cmd_aguardar(chave, *motivo):
    with Trava():
        t = ler(chave)
        exigir(t["status"] == "rodando", f"{chave} não está rodando")
        t["status"] = "aguardando_humano"
        t["motivo"] = " ".join(motivo)
        salvar(t, f"aguardando humano: {t['motivo']}")
    print(f"OK {chave} aguardando você: {t['motivo']}")


def cmd_retomar(chave):
    with Trava():
        t = ler(chave)
        exigir(t["status"] == "aguardando_humano", f"{chave} não está aguardando você")
        t["status"] = "pronto"
        t["motivo"] = None
        salvar(t, "retomada")
    print(f"OK {chave} pronta. PRÓXIMO: rodar {etapa(t)['agente']}")


def cmd_aprovar(chave, *nota):
    with Trava():
        t = ler(chave)
        exigir(etapa(t).get("gate") and t["status"] == "aguardando_aprovacao",
               f"{chave} não está esperando aprovação (etapa={t['etapa']}, status={t['status']})")
        gate = t["etapa"]
        prox = avancar(t)
        salvar(t, f"APROVADO {gate}" + (f": {' '.join(nota)}" if nota else ""))
    print(f"OK {gate} aprovado. PRÓXIMO: rodar {prox.get('agente', 'nada')}")


def cmd_reprovar(chave, *nota):
    exigir(nota, "diga o que precisa mudar")
    with Trava():
        t = ler(chave)
        exigir(etapa(t).get("gate") and t["status"] == "aguardando_aprovacao",
               f"{chave} não está esperando aprovação")
        gate = t["etapa"]
        i = IDX[gate] - 1
        while not ETAPAS[i].get("agente"):
            i -= 1
        t["etapa"] = ETAPAS[i]["id"]
        t["status"] = "pronto"
        t["feedback"] = " ".join(nota)
        salvar(t, f"REPROVADO {gate}: {t['feedback']}")
    print(f"OK volta para {t['etapa']}. PRÓXIMO: rodar {ETAPAS[i]['agente']} com o feedback")


def cmd_pular(chave, *justificativa):
    exigir(justificativa, "justificativa obrigatória para pular etapa")
    with Trava():
        t = ler(chave)
        exigir(etapa(t).get("pulavel") and t["status"] == "pronto",
               f"etapa {t['etapa']} não pode ser pulada")
        feita = t["etapa"]
        avancar(t)
        salvar(t, f"PULOU {feita}: {' '.join(justificativa)}")
    print(f"OK {feita} pulada (registrado no histórico).")


def cmd_duvida(chave, *texto):
    with Trava():
        t = ler(chave)
        novo = max([d["id"] for d in t["duvidas"]], default=0) + 1
        t["duvidas"].append({"id": novo, "texto": " ".join(texto), "status": "aberta", "aberta_em": agora()})
        salvar(t, f"dúvida QA #{novo}")
    print(f"OK dúvida #{novo} em {chave}. PRÓXIMO: rodar qa-responder")


def cmd_responder(chave, id_, *resumo):
    with Trava():
        t = ler(chave)
        d = next((d for d in t["duvidas"] if d["id"] == int(id_)), None)
        exigir(d and d["status"] == "aberta", f"dúvida #{id_} não está aberta")
        d["status"] = "respondida"
        d["resposta"] = " ".join(resumo)
        d["respondida_em"] = agora()
        salvar(t, f"dúvida #{id_} respondida")
    print(f"OK dúvida #{id_} fechada.")


COMANDOS = {k[4:]: v for k, v in globals().items() if k.startswith("cmd_")}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(__doc__)
        sys.exit(1)
    try:
        COMANDOS[sys.argv[1]](*sys.argv[2:])
    except TypeError:
        print(__doc__)
        sys.exit(1)
