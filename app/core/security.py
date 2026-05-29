from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

ALG = "HS256"
SESSAO_DIAS = 7


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def criar_token(usuario_id: int, dias: int = SESSAO_DIAS) -> str:
    payload = {
        "sub": str(usuario_id),
        "exp": datetime.now(UTC) + timedelta(days=dias),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALG)


def decodificar_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALG])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
