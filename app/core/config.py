from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "dev"
    database_url: str
    database_url_prod: str = ""
    secret_key: str = "dev-insecure-key"
    tz_display: str = "America/Sao_Paulo"

    # Bootstrap do admin (usado por scripts/criar_admin.py)
    admin_nome: str = ""
    admin_apelido: str = ""
    admin_email: str = ""
    admin_senha: str = ""

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    @property
    def active_database_url(self) -> str:
        if self.is_prod and self.database_url_prod:
            return self.database_url_prod
        return self.database_url


settings = Settings()
