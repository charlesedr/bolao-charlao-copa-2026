from enum import StrEnum


class StatusUsuario(StrEnum):
    PENDENTE = "pendente"
    APROVADO = "aprovado"
    BLOQUEADO = "bloqueado"
    REPROVADO = "reprovado"


class StatusPartida(StrEnum):
    NAO_INICIADO = "nao_iniciado"
    EM_ANDAMENTO = "em_andamento"
    FINALIZADO = "finalizado"


class FasePartida(StrEnum):
    GRUPOS = "grupos"
    R32 = "32avos"
    OITAVAS = "oitavas"
    QUARTAS = "quartas"
    SEMIFINAL = "semifinal"
    DISPUTA_3O = "disputa_3o"
    FINAL = "final"


class TipoOrigem(StrEnum):
    VENCEDOR = "vencedor"
    PERDEDOR = "perdedor"


class ContextoDesempate(StrEnum):
    GRUPO = "grupo"
    TERCEIROS = "terceiros"


# Fases de mata-mata (todas exceto grupos) — útil para regras de pontuação/classificado.
FASES_MATA_MATA = {
    FasePartida.R32,
    FasePartida.OITAVAS,
    FasePartida.QUARTAS,
    FasePartida.SEMIFINAL,
    FasePartida.DISPUTA_3O,
    FasePartida.FINAL,
}
