"""Testes unitários para auth_service.alterar_senha (validações puras)."""
from unittest.mock import patch

from app.core.security import hash_senha
from app.domain.models import Usuario
from app.services import auth_service


def _user(senha_atual: str = "senhaAntiga1", temp: bool = False) -> Usuario:
    return Usuario(
        id=1,
        nome="Teste",
        apelido="teste",
        email="teste@x.com",
        senha_hash=hash_senha(senha_atual),
        senha_temporaria=temp,
    )


def test_senha_atual_incorreta():
    user = _user("certinha123")
    with (
        patch("app.services.auth_service.user_repo.get_by_id", return_value=user),
        patch("app.services.auth_service.user_repo.salvar") as salvar,
    ):
        ok, msg = auth_service.alterar_senha(
            None, usuario_id=1, senha_atual="errada", senha_nova="novasenha1", confirmacao="novasenha1",
        )
    assert not ok
    assert "incorreta" in msg.lower()
    salvar.assert_not_called()


def test_confirmacao_diferente():
    user = _user("certinha123")
    with patch("app.services.auth_service.user_repo.get_by_id", return_value=user):
        ok, msg = auth_service.alterar_senha(
            None, usuario_id=1, senha_atual="certinha123",
            senha_nova="novasenha1", confirmacao="diferente1",
        )
    assert not ok
    assert "confer" in msg.lower()


def test_senha_curta():
    user = _user("certinha123")
    with patch("app.services.auth_service.user_repo.get_by_id", return_value=user):
        ok, msg = auth_service.alterar_senha(
            None, usuario_id=1, senha_atual="certinha123",
            senha_nova="abc", confirmacao="abc",
        )
    assert not ok
    assert "6 caracteres" in msg


def test_senha_igual_atual():
    user = _user("certinha123")
    with patch("app.services.auth_service.user_repo.get_by_id", return_value=user):
        ok, msg = auth_service.alterar_senha(
            None, usuario_id=1, senha_atual="certinha123",
            senha_nova="certinha123", confirmacao="certinha123",
        )
    assert not ok
    assert "diferente" in msg.lower()


def test_sucesso_altera_e_limpa_temporaria():
    user = _user("certinha123", temp=True)
    with (
        patch("app.services.auth_service.user_repo.get_by_id", return_value=user),
        patch("app.services.auth_service.user_repo.salvar") as salvar,
    ):
        ok, msg = auth_service.alterar_senha(
            None, usuario_id=1, senha_atual="certinha123",
            senha_nova="senhaNova42", confirmacao="senhaNova42",
        )
    assert ok
    assert "sucesso" in msg.lower()
    assert user.senha_temporaria is False
    # Hash mudou e a nova senha verifica
    from app.core.security import verificar_senha
    assert verificar_senha("senhaNova42", user.senha_hash)
    salvar.assert_called_once()


def test_usuario_inexistente():
    with patch("app.services.auth_service.user_repo.get_by_id", return_value=None):
        ok, msg = auth_service.alterar_senha(
            None, usuario_id=999, senha_atual="x", senha_nova="abcdef", confirmacao="abcdef",
        )
    assert not ok
    assert "não encontrado" in msg.lower()
