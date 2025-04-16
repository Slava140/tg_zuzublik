from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


env_path = Path(__file__).parent.parent / '.env'


class Settings(BaseSettings):
    SQLITE_DB_PATH: Path

    TG_BOT_TOKEN: str

    UPLOAD_ALLOWED_SUFFIXES: set

    DOCUMENT_COLUMN_NAMES: set

    uploads_dir: Path = Path(__file__).parent.parent / 'uploads'

    @property
    def database_url(self):
        if self.SQLITE_DB_PATH.is_absolute():
            return f"sqlite+aiosqlite:////{self.SQLITE_DB_PATH}"
        else:
            return f"sqlite+aiosqlite:///{env_path.parent / self.SQLITE_DB_PATH}"

    @property
    def allowed_suffixes(self) -> str:
        return ', '.join(self.UPLOAD_ALLOWED_SUFFIXES)

    @property
    def document_column_names(self) -> str:
        return ', '.join(self.DOCUMENT_COLUMN_NAMES)

    @classmethod
    def load(cls):
        return cls()

    model_config = SettingsConfigDict(env_file=env_path if env_path.exists() else None)

settings = Settings.load()
