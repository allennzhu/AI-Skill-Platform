from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "deepseek-r1"
    llm_timeout_seconds: float = 120
    session_ttl_seconds: int = 3600
    cors_origins: str = "http://localhost:7777,http://127.0.0.1:7777,http://localhost:8080,http://127.0.0.1:8080"
    # 本地开发：除显式名单外，再正则放行 localhost 与私有网段（10.x / 192.168.x / 172.16-31.x）任意端口，
    # 避免开发机 IP 变动就要改配置（置空字符串则关闭正则，仅用显式名单）
    cors_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(:\d+)?$"
    )
    # 51PM 业务后端（用户级 API Key resolve）
    biz_base_url: str = "http://127.0.0.1:8888"
    biz_internal_secret: str = ""
    biz_resolve_timeout_seconds: float = 5

def get_settings() -> Settings:
    return Settings()
