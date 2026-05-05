from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    layer_a_mysql_host: str = "127.0.0.1"
    layer_a_mysql_port: int = 3308
    layer_a_mysql_user: str = "root"
    layer_a_mysql_password: str = ""
    layer_a_mysql_db: str = "osu"

    layer_a_mode: str = "osu"
    layer_a_version: str = "top_10000"
    layer_a_ymd: str = ""

    layer_b_pg_host: str = "127.0.0.1"
    layer_b_pg_port: int = 5432
    layer_b_pg_user: str = "osu"
    layer_b_pg_password: str = ""
    layer_b_pg_db: str = "all_of_osu"

    liquipedia_user_agent: str = (
        "All-Of-Osu-DB/0.1 (https://github.com/mattik01/All-Of-Osu-DB; "
        "glaeser.matteo@googlemail.com)"
    )
    liquipedia_cache_dir: Path = Path("data/layerA/liquipedia/_cache")
    liquipedia_output_dir: Path = Path("data/layerA/liquipedia")
    liquipedia_min_request_interval_s: float = 30.0

    @property
    def layer_a_url(self) -> str:
        pw = f":{self.layer_a_mysql_password}" if self.layer_a_mysql_password else ""
        return (
            f"mysql+pymysql://{self.layer_a_mysql_user}{pw}"
            f"@{self.layer_a_mysql_host}:{self.layer_a_mysql_port}"
            f"/{self.layer_a_mysql_db}?charset=utf8mb4"
        )

    @property
    def layer_b_url(self) -> str:
        return (
            f"postgresql://{self.layer_b_pg_user}:{self.layer_b_pg_password}"
            f"@{self.layer_b_pg_host}:{self.layer_b_pg_port}/{self.layer_b_pg_db}"
        )
