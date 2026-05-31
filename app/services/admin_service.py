"""Ações administrativas sobre usuários."""
import secrets

from sqlmodel import Session, delete

from app.core.security import hash_senha
from app.domain.enums import StatusUsuario
from app.domain.models import (
    ApostaClassificacaoFinal,
    DesempatePalpiteUsuario,
    Palpite,
    PontuacaoPartida,
)
from app.repositories import admin_log_repo, user_repo


def _mudar_status(
    session: Session, *, admin_id: int, usuario_id: int, novo_status: str, acao: str
) -> tuple[bool, str]:
    usuario = user_repo.get_by_id(session, usuario_id)
    if usuario is None:
        return False, "Usuário não encontrado."
    if usuario.is_admin and novo_status != StatusUsuario.APROVADO:
        return False, "Não é possível bloquear/reprovar um administrador."
    usuario.status = novo_status
    session.add(usuario)
    admin_log_repo.registrar(
        session, admin_id=admin_id, acao=acao, entidade="usuario", entidade_id=usuario_id,
        detalhes={"status": str(novo_status)},
    )
    session.commit()
    return True, "Status atualizado."


def aprovar(session, *, admin_id, usuario_id):
    return _mudar_status(session, admin_id=admin_id, usuario_id=usuario_id,
                         novo_status=StatusUsuario.APROVADO, acao="aprovar_usuario")


def reprovar(session, *, admin_id, usuario_id):
    return _mudar_status(session, admin_id=admin_id, usuario_id=usuario_id,
                         novo_status=StatusUsuario.REPROVADO, acao="reprovar_usuario")


def bloquear(session, *, admin_id, usuario_id):
    return _mudar_status(session, admin_id=admin_id, usuario_id=usuario_id,
                         novo_status=StatusUsuario.BLOQUEADO, acao="bloquear_usuario")


def desbloquear(session, *, admin_id, usuario_id):
    return _mudar_status(session, admin_id=admin_id, usuario_id=usuario_id,
                         novo_status=StatusUsuario.APROVADO, acao="desbloquear_usuario")


def excluir_usuario(
    session: Session, *, admin_id: int, usuario_id: int
) -> tuple[bool, str]:
    """Exclui um usuário (não-admin) e seus dados relacionados.

    Libera o e-mail/apelido para um eventual novo cadastro. Permitido apenas para
    usuários com status REPROVADO ou BLOQUEADO (evita exclusão acidental de ativos).
    """
    usuario = user_repo.get_by_id(session, usuario_id)
    if usuario is None:
        return False, "Usuário não encontrado."
    if usuario.is_admin:
        return False, "Não é possível excluir um administrador."
    if usuario.status not in (StatusUsuario.REPROVADO, StatusUsuario.BLOQUEADO):
        return False, "Só é possível excluir usuários reprovados ou bloqueados."

    for tabela in (Palpite, PontuacaoPartida, ApostaClassificacaoFinal, DesempatePalpiteUsuario):
        session.exec(delete(tabela).where(tabela.usuario_id == usuario_id))
    admin_log_repo.registrar(
        session, admin_id=admin_id, acao="excluir_usuario", entidade="usuario",
        entidade_id=usuario_id, detalhes={"email": usuario.email, "apelido": usuario.apelido},
    )
    session.delete(usuario)
    session.commit()
    return True, "Usuário excluído. E-mail e apelido liberados para novo cadastro."


def resetar_senha(session: Session, *, admin_id: int, usuario_id: int) -> tuple[bool, str]:
    usuario = user_repo.get_by_id(session, usuario_id)
    if usuario is None:
        return False, "Usuário não encontrado."
    nova = secrets.token_urlsafe(8)
    usuario.senha_hash = hash_senha(nova)
    usuario.senha_temporaria = True
    session.add(usuario)
    admin_log_repo.registrar(
        session, admin_id=admin_id, acao="reset_senha", entidade="usuario", entidade_id=usuario_id,
    )
    session.commit()
    return True, f"Senha temporária: {nova}"
