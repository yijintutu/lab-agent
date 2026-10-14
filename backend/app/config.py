from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # 后端项目的根路径


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24

    AI_ENABLED: bool = False
    AI_TOOLS_ENABLED: bool = False
    AI_WRITE_TOOLS_ENABLED: bool = False

    # AI 接入配置均可缺省，缺少密钥时只影响 AI 请求，不影响阶段①业务启动。
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = ""
    LLM_MODEL: str = ""
    LLM_MODEL_PROVIDER: str = ""
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_TEMPERATURE: float = 0.2
    LLM_STREAM_ENABLED: bool = False

    # RAG 使用独立的 Embedding 配置。API 模式下 key/base_url 可回退到 LLM 配置，
    # 但 Embedding 模型名必须单独确认，不能默认把聊天模型名当作向量模型。
    RAG_EMBEDDING_BACKEND: str = "api"
    RAG_EMBEDDING_API_KEY: str = ""
    RAG_EMBEDDING_BASE_URL: str = ""
    RAG_EMBEDDING_MODEL: str = ""
    RAG_LOCAL_EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    RAG_LOCAL_DEVICE: str = "cpu"
    RAG_EMBEDDING_TIMEOUT_SECONDS: float = 60.0
    RAG_CHROMA_DIR: Path = BASE_DIR / "data" / "chroma"
    RAG_KB_DIR: Path = BASE_DIR / "data" / "kb"
    RAG_COLLECTION_PREFIX: str = "lab_kb"
    RAG_CHUNK_SIZE: int = 600
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 4
    RAG_MIN_RELEVANCE_SCORE: float = 0.2

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"
    )


settings = Settings()  # type: ignore[call-arg]

# 文件上传限制:`UPLOAD_DIR`（存哪）、`ALLOWED_EXTENSIONS`（允许什么类型）、`MAX_FILE_SIZE`（多大）、`BASE_DIR`
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}
