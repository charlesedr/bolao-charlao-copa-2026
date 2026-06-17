"""Sincronização automática de resultados via ESPN (gratuito, sem chave).

- Endpoint scoreboard: jogos do dia + placar + status
- Endpoint summary: cartões (keyEvents)

Regra de override:
  - dados_origem == 'manual'  -> NÃO atualiza placar/cartões. Só guarda o
    snapshot ESPN em placar_espn_* para o admin ver a divergência.
  - dados_origem == 'auto' ou NULL -> aplica ESPN normalmente.

Cartões da ESPN são best-effort: ESPN reporta yellow/red como eventos
individuais, mas não diferencia "vermelho direto" de "amarelo + vermelho
direto mesmo jogador" de forma confiável. Estratégia:
  - Yellow Card        -> fp_amarelos
  - Yellow Red Card    -> fp_verm_2amarelo (segundo amarelo)
  - Red Card           -> fp_verm_direto

A categoria fp_amarelo_verm (amarelo + vermelho direto mesmo jogador, -5)
não é detectada automaticamente — admin override quando necessário.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any

import requests
from sqlmodel import Session, select

from app.core.timezone import now_utc
from app.domain.enums import StatusPartida
from app.domain.models import Partida, Selecao
from app.services import match_service

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
ESPN_TIMEOUT = 15

# ID do "admin sintético" usado nos logs de auto-sync.
# -1 indica que não é um usuário humano — verificado em admin_log_repo se necessário.
ADMIN_ID_SISTEMA = -1


# ---------------------------------------------------------------------------
# Fetch ESPN
# ---------------------------------------------------------------------------
def _fetch_scoreboard(data_yyyymmdd: str) -> dict[str, Any]:
    url = f"{ESPN_BASE}/scoreboard"
    r = requests.get(url, params={"dates": data_yyyymmdd}, timeout=ESPN_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _fetch_summary(event_id: str) -> dict[str, Any]:
    url = f"{ESPN_BASE}/summary"
    r = requests.get(url, params={"event": event_id}, timeout=ESPN_TIMEOUT)
    r.raise_for_status()
    return r.json()


# ---------------------------------------------------------------------------
# Parse de placar / status / equipes
# ---------------------------------------------------------------------------
def _parse_evento(evento: dict[str, Any]) -> dict[str, Any] | None:
    """Extrai (event_id, mandante_abbr, visitante_abbr, placar_m, placar_v, completed)."""
    try:
        competicoes = evento.get("competitions") or []
        if not competicoes:
            return None
        comp = competicoes[0]
        competidores = comp.get("competitors") or []
        mandante = next((c for c in competidores if c.get("homeAway") == "home"), None)
        visitante = next((c for c in competidores if c.get("homeAway") == "away"), None)
        if mandante is None or visitante is None:
            return None
        status = (evento.get("status") or {}).get("type") or {}
        completed = bool(status.get("completed"))
        em_andamento = status.get("state") == "in" or status.get("name") in {
            "STATUS_IN_PROGRESS", "STATUS_HALFTIME", "STATUS_END_PERIOD",
        }
        return {
            "event_id": str(evento.get("id")),
            "mandante_abbr": (mandante.get("team") or {}).get("abbreviation"),
            "mandante_espn_id": str((mandante.get("team") or {}).get("id") or ""),
            "visitante_abbr": (visitante.get("team") or {}).get("abbreviation"),
            "visitante_espn_id": str((visitante.get("team") or {}).get("id") or ""),
            "placar_mandante": _int_safe(mandante.get("score")),
            "placar_visitante": _int_safe(visitante.get("score")),
            "completed": completed,
            "em_andamento": em_andamento,
        }
    except Exception:
        return None


def _int_safe(x: Any) -> int | None:
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Parse de cartões (keyEvents) — por ID ESPN da equipe
# ---------------------------------------------------------------------------
def _contar_cartoes(summary: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Retorna {espn_team_id: {'amarelos': N, 'verm_2amarelo': N, 'verm_direto': N}}."""
    counts: dict[str, dict[str, int]] = {}
    for ev in summary.get("keyEvents") or []:
        tipo = ((ev.get("type") or {}).get("text") or "").lower()
        team_id = str((ev.get("team") or {}).get("id") or "")
        if not team_id:
            continue
        bucket = counts.setdefault(
            team_id, {"amarelos": 0, "verm_2amarelo": 0, "verm_direto": 0}
        )
        if "yellow red" in tipo or "second yellow" in tipo:
            bucket["verm_2amarelo"] += 1
        elif "yellow" in tipo:
            bucket["amarelos"] += 1
        elif "red" in tipo:
            bucket["verm_direto"] += 1
    return counts


# ---------------------------------------------------------------------------
# Mapeamento ESPN <-> Seleção do banco
# ---------------------------------------------------------------------------
def _mapa_selecoes_por_codigo(session: Session) -> dict[str, Selecao]:
    return {
        (s.codigo_fifa or "").upper(): s
        for s in session.exec(select(Selecao)).all()
        if s.codigo_fifa
    }


def _achar_partida(
    session: Session, mandante_id: int, visitante_id: int
) -> Partida | None:
    return session.exec(
        select(Partida).where(
            Partida.mandante_id == mandante_id,
            Partida.visitante_id == visitante_id,
        )
    ).first()


# ---------------------------------------------------------------------------
# Orquestração principal
# ---------------------------------------------------------------------------
def sincronizar(
    session: Session, *, dias_atras: int = 1, dias_a_frente: int = 1, dry_run: bool = False
) -> dict[str, Any]:
    """Roda o sync para [hoje-N, hoje+M]. Retorna estatísticas.

    Para cada evento ESPN finalizado:
      - achar a Partida correspondente (por codigo_fifa dos 2 times)
      - se dados_origem != 'manual': aplica placar + cartões via match_service
      - se 'manual' E placar diverge: salva snapshot em placar_espn_*
    """
    selecoes = _mapa_selecoes_por_codigo(session)
    hoje = now_utc().date()
    datas = [
        (hoje + timedelta(days=d)).strftime("%Y%m%d")
        for d in range(-dias_atras, dias_a_frente + 1)
    ]

    stats: dict[str, Any] = {
        "datas_consultadas": datas,
        "eventos_vistos": 0,
        "atualizados": 0,
        "divergencias_manual": 0,
        "ignorados_manual": 0,
        "nao_mapeados": 0,
        "ignorados_nao_finalizado": 0,
        "erros": [],
    }

    for data in datas:
        try:
            data_payload = _fetch_scoreboard(data)
        except requests.RequestException as exc:
            stats["erros"].append(f"scoreboard {data}: {exc}")
            continue

        for evento in data_payload.get("events") or []:
            parsed = _parse_evento(evento)
            if parsed is None:
                continue
            stats["eventos_vistos"] += 1

            sel_m = selecoes.get((parsed["mandante_abbr"] or "").upper())
            sel_v = selecoes.get((parsed["visitante_abbr"] or "").upper())
            if sel_m is None or sel_v is None:
                stats["nao_mapeados"] += 1
                stats["erros"].append(
                    f"Não mapeei {parsed['mandante_abbr']} x {parsed['visitante_abbr']} "
                    f"({data})"
                )
                continue

            partida = _achar_partida(session, sel_m.id, sel_v.id)
            if partida is None:
                continue  # confronto que não existe no nosso bracket

            if not (parsed["completed"] or parsed["em_andamento"]):
                stats["ignorados_nao_finalizado"] += 1
                continue

            placar_m = parsed["placar_mandante"]
            placar_v = parsed["placar_visitante"]
            if placar_m is None or placar_v is None:
                continue

            # Cartões só fazem sentido após o jogo começar — chama summary
            cards_m = {"amarelos": 0, "verm_2amarelo": 0, "verm_direto": 0}
            cards_v = {"amarelos": 0, "verm_2amarelo": 0, "verm_direto": 0}
            if parsed["completed"]:
                try:
                    summary = _fetch_summary(parsed["event_id"])
                    counts = _contar_cartoes(summary)
                    cards_m = counts.get(parsed["mandante_espn_id"], cards_m)
                    cards_v = counts.get(parsed["visitante_espn_id"], cards_v)
                except requests.RequestException as exc:
                    stats["erros"].append(
                        f"summary {parsed['event_id']}: {exc}"
                    )

            status_novo = (
                StatusPartida.FINALIZADO if parsed["completed"] else StatusPartida.EM_ANDAMENTO
            )

            if partida.dados_origem == match_service.ORIGEM_MANUAL:
                # Override manual: só grava snapshot se diverge do que está salvo.
                diverge = (
                    partida.placar_mandante != placar_m
                    or partida.placar_visitante != placar_v
                )
                if diverge:
                    stats["divergencias_manual"] += 1
                    if not dry_run:
                        partida.placar_espn_mandante = placar_m
                        partida.placar_espn_visitante = placar_v
                        partida.dados_sincronizado_em = now_utc()
                        session.add(partida)
                        session.commit()
                else:
                    stats["ignorados_manual"] += 1
                continue

            # Aplica via match_service (que cuida do classificado, recálculo etc.)
            if dry_run:
                stats["atualizados"] += 1
                continue
            ok, _ = match_service.lancar_placar(
                session,
                admin_id=ADMIN_ID_SISTEMA,
                partida_id=partida.id,
                placar_mandante=placar_m,
                placar_visitante=placar_v,
                status=status_novo,
                fp_amarelos_mandante=cards_m["amarelos"],
                fp_verm_2amarelo_mandante=cards_m["verm_2amarelo"],
                fp_verm_direto_mandante=cards_m["verm_direto"],
                fp_amarelos_visitante=cards_v["amarelos"],
                fp_verm_2amarelo_visitante=cards_v["verm_2amarelo"],
                fp_verm_direto_visitante=cards_v["verm_direto"],
                origem=match_service.ORIGEM_AUTO,
            )
            if ok:
                stats["atualizados"] += 1
            else:
                stats["erros"].append(
                    f"lancar_placar {partida.codigo}: {ok}"
                )

    return stats
