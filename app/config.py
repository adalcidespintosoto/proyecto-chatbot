"""
Módulo de configuración global de la aplicación UniMon.
Utiliza Pydantic Settings para cargar y validar variables de entorno desde el archivo .env.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración centralizada para el backend de UniMon.
    Valida variables de conexión a GLPI, Ollama y parámetros del servidor.
    """
    # Configuración de Servidor
    app_name: str = "UniMon - Asistente Virtual de Soporte Técnico USB"
    app_version: str = "1.0.0"
    environment: str = "development"
    port: int = 8000
    host: str = "0.0.0.0"
    debug: bool = False

    # Credenciales de Administración (/admin y APIs protegidas)
    admin_username: str = "admin"
    admin_password: str = ""  # NO HARDCODEAR CONTRASEÑAS EN PRODUCCIÓN

    # Configuración de GLPI REST API (deben definirse en .env)
    glpi_base_url: str = "https://pruebas.us5.glpi-network.cloud/api.php/v1"
    glpi_app_token: str = ""
    glpi_user_token: str = ""
    glpi_timeout: float = 15.0

    # Configuración de Proveedor LLM (gemini | openai | ollama)
    llm_provider: str = "gemini"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout: float = 35.0

    # Configuración de Google Gemini (Nube)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    gemini_timeout: float = 35.0

    # Configuración de Ollama (RAG / LLM Local)
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "unimon:8b"
    ollama_timeout: float = 45.0

    # Configuración de Vision-LLM (Ingesta Multimodal)
    vision_model: str = "llama3.2-vision:11b"
    vision_timeout: float = 120.0
    vision_max_image_size: int = 1024
    vision_min_image_kb: int = 15

    # Configuración de ChromaDB y Embeddings
    chroma_db_dir: str = "./chroma_db"
    docs_dir: str = "./data/docs"
    embedding_model: str = "intfloat/multilingual-e5-large"
    rag_inject_full_doc: bool = False  # False = Modo Chunks (Ahorro de tokens); True = Documento Completo
    rag_max_chunks: int = 4

    # Límites de Seguridad
    max_upload_size_mb: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna una instancia única (cacheada) de la configuración de la aplicación.
    """
    return Settings()
