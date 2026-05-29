"""Cadastro, login e validações de usuário."""
import re

from email_validator import EmailNotValidError, validate_email
from sqlmodel import Session

from app.core.security import hash_senha, verificar_senha
from app.domain.enums import StatusUsuario
from app.domain.models import Usuario
from app.repositories import user_repo

SENHA_MIN = 6
APELIDO_RE = re.compile(r"^[A-Za-z0-9_.\- ]{2,40}$")


def _validar_senha(senha: str) -> str | None:
    if len(senha) < SENHA_MIN:
        return f"A senha precisa ter ao menos {SENHA_MIN} caracteres."
    return None


def _validar_email(email: str) -> str | None:
    try:
        validate_email(email, check_deliverability=False)
        return None
    except EmailNotValidError:
        return "E-mail inválido."


def _validar_telefone(telefone: str) -> str | None:
    digitos = re.sub(r"\D", "", telefone or "")
    if not (10 <= len(digitos) <= 13):
        return "Telefone inválido. Informe DDD + número (ex.: 11 91234-5678)."
    return None


def cadastrar(
    session: Session, *, nome: str, apelido: str, email: str, telefone: str, senha: str
) -> tuple[bool, str, Usuario | None]:
    nome = (nome or "").strip()
    apelido = (apelido or "").strip()
    email = (email or "").strip()
    telefone = (telefone or "").strip()

    if not nome:
        return False, "Informe seu nome.", None
    if not APELIDO_RE.match(apelido):
        return False, "Apelido inválido (2-40 caracteres: letras, números, _ . -).", None
    if (msg := _validar_email(email)) is not None:
        return False, msg, None
    if (msg := _validar_telefone(telefone)) is not None:
        return False, msg, None
    if (msg := _validar_senha(senha)) is not None:
        return False, msg, None

    if user_repo.get_by_email(session, email):
        return False, "Este e-mail já está cadastrado.", None
    if user_repo.get_by_apelido(session, apelido):
        return False, "Este apelido já está em uso.", None

    usuario = Usuario(
        nome=nome,
        apelido=apelido,
        email=email,
        telefone=telefone,
        senha_hash=hash_senha(senha),
        status=StatusUsuario.PENDENTE,
        is_admin=False,
    )
    user_repo.salvar(session, usuario)
    return True, "Cadastro realizado! Aguarde a aprovação do administrador.", usuario


def autenticar(
    session: Session, *, login: str, senha: str
) -> tuple[bool, str, Usuario | None]:
    usuario = user_repo.get_by_login(session, login)
    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return False, "Apelido/e-mail ou senha incorretos.", None
    return True, "ok", usuario


def mensagem_por_status(usuario: Usuario) -> str | None:
    """Mensagem de bloqueio conforme status; None se pode acessar."""
    if usuario.status == StatusUsuario.APROVADO:
        return None
    if usuario.status == StatusUsuario.PENDENTE:
        return "Seu cadastro está aguardando aprovação do administrador."
    if usuario.status == StatusUsuario.BLOQUEADO:
        return "Sua conta está bloqueada. Fale com o administrador."
    if usuario.status == StatusUsuario.REPROVADO:
        return "Seu cadastro foi recusado."
    return "Acesso não autorizado."
