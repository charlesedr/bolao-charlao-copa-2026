"""Cria (ou promove) o usuário administrador a partir das variáveis ADMIN_* do .env."""
from sqlmodel import Session

from _common import *  # noqa: F401,F403  (ajuste de sys.path)

from app.core.config import settings
from app.core.db import engine
from app.core.security import hash_senha
from app.domain.enums import StatusUsuario
from app.repositories import user_repo
from app.domain.models import Usuario


def main() -> None:
    if not (settings.admin_email and settings.admin_apelido and settings.admin_senha):
        print("ERRO: defina ADMIN_NOME, ADMIN_APELIDO, ADMIN_EMAIL e ADMIN_SENHA no .env.")
        return

    with Session(engine) as session:
        existente = user_repo.get_by_email(session, settings.admin_email)
        if existente:
            existente.is_admin = True
            existente.status = StatusUsuario.APROVADO
            user_repo.salvar(session, existente)
            print(f"Admin já existia — promovido/aprovado: {existente.apelido} ({existente.email})")
            return

        admin = Usuario(
            nome=settings.admin_nome or settings.admin_apelido,
            apelido=settings.admin_apelido,
            email=settings.admin_email,
            senha_hash=hash_senha(settings.admin_senha),
            status=StatusUsuario.APROVADO,
            is_admin=True,
            senha_temporaria=False,
        )
        user_repo.salvar(session, admin)
        print(f"Admin criado: {admin.apelido} ({admin.email}) — troque a senha depois.")


if __name__ == "__main__":
    main()
