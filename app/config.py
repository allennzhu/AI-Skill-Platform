from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    llm_timeout_seconds: float = 120
    # 瞬时失败（524/502/超时）自动重试次数；免费模型冷启动常见第一次 524、第二次成功
    llm_retry_times: int = 1
    llm_retry_backoff_seconds: float = 1.0
    session_ttl_seconds: int = 3600
    # 51PM 业务后端（用户级 API Key resolve）
    biz_base_url: str = "http://127.0.0.1:8888"
    biz_internal_secret: str = ""
    biz_resolve_timeout_seconds: float = 5


def get_settings() -> Settings:
    return Settings()
